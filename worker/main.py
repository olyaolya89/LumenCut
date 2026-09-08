"""Loopback film worker. FastAPI when installed, stdlib HTTP otherwise.

Bind 127.0.0.1:8091 on the desk. Docker may set LUMENCUT_WORKER_HOST=0.0.0.0.
"""
from __future__ import annotations

import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from worker import store
from worker.pipeline import STEPS, run as run_pipeline, step_rank

from worker.render import cpu_jobs, render_engine
from worker.score import clip_available

HOST = os.environ.get("LUMENCUT_WORKER_HOST", "127.0.0.1")
PORT = int(os.environ.get("LUMENCUT_WORKER_PORT", "8091"))
ID_RE = re.compile(r"^[a-zA-Z0-9._-]{8,80}$")
LOCK = threading.Semaphore(1)
RUNNING: set[str] = set()


def _valid_id(project_id: str) -> bool:
    return bool(ID_RE.match(project_id)) and ".." not in project_id


def enqueue(project_id: str, from_step: str | None = None) -> dict[str, Any]:
    if not _valid_id(project_id):
        return {"ok": False, "error": "bad id"}
    dest = store.ensure_project(project_id)
    scenes = store.read_json(dest / "scenes.json") or {}
    script = store.project_script(project_id)
    if not scenes and not script:
        return {"ok": False, "error": "missing scenes.json"}
    if not scenes:
        scenes = {"id": project_id, "script": script}
        store.write_json(dest / "scenes.json", scenes)
    elif script and not str(scenes.get("script") or "").strip():
        scenes = {**scenes, "script": script}
        store.write_json(dest / "scenes.json", scenes)
    current = store.read_json(dest / "status.json") or {}
    if current.get("status") in {"queued", "running"} and project_id in RUNNING:
        return {"ok": True, "status": current, "reused": True}
    if not from_step and current.get("status") == "ready" and (dest / "timeline.json").is_file():
        return {"ok": True, "status": current, "reused": True}

    step = from_step.strip() if isinstance(from_step, str) and from_step.strip() else None
    need_script = not step or step_rank(step) <= 0
    if need_script and not script:
        return {"ok": False, "error": "empty script"}
    store.write_status(
        project_id,
        status="queued",
        stage=step or "queued",
        progress=1,
        message=f"Retry {step}" if step else "Queued",
        error=None,
    )
    if step:
        store.upsert_task(project_id, STEPS[step_rank(step)], status="queued")

    def work() -> None:
        RUNNING.add(project_id)
        try:
            with LOCK:
                run_pipeline(project_id, step)
        finally:
            RUNNING.discard(project_id)

    threading.Thread(target=work, name=f"lumencut-{project_id[:8]}", daemon=True).start()
    return {"ok": True, "status": store.read_json(dest / "status.json"), "fromStep": step}


def job_status(project_id: str) -> dict[str, Any]:
    if not _valid_id(project_id):
        return {"ok": False, "error": "bad id"}
    status = store.read_json(store.project_dir(project_id) / "status.json")
    if not status:
        return {"ok": False, "error": "unknown"}
    return {"ok": True, "status": status}


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "worker": "lumencut",
        "dataDir": str(store.ROOT),
        "clip": clip_available(),
        "renderEngine": render_engine(),
        "renderJobs": cpu_jobs(),
    }


def _install_fastapi():
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(title="LumenCut worker", docs_url=None, redoc_url=None)

    @app.get("/health")
    def get_health():
        return health()

    @app.post("/jobs")
    async def post_job(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        project_id = str((payload or {}).get("project_id") or "")
        from_step = (payload or {}).get("from_step") or (payload or {}).get("step")
        result = enqueue(project_id, str(from_step) if from_step else None)
        if not result.get("ok"):
            raise HTTPException(400, result.get("error") or "rejected")
        return result

    @app.post("/jobs/{project_id}/retry")
    async def retry_job(project_id: str, request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        step = str((payload or {}).get("step") or (payload or {}).get("from_step") or "") or None
        result = enqueue(project_id, step)
        if not result.get("ok"):
            raise HTTPException(400, result.get("error") or "rejected")
        return result

    @app.get("/jobs/{project_id}")
    def get_job(project_id: str):
        result = job_status(project_id)
        if not result.get("ok"):
            raise HTTPException(404, result.get("error") or "unknown")
        return result

    @app.get("/")
    def root():
        return JSONResponse(health())

    return app


try:
    app = _install_fastapi()
except Exception:
    app = None


class StdHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._send(200, health())
            return
        if path.startswith("/jobs/"):
            pid = path.split("/jobs/", 1)[1].strip("/")
            result = job_status(pid)
            self._send(200 if result.get("ok") else 404, result)
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        retry = path.startswith("/jobs/") and path.rstrip("/").endswith("/retry")
        if retry:
            pid = path.strip("/").split("/")[1]
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                body = {}
            result = enqueue(pid, str(body.get("step") or body.get("from_step") or "") or None)
            self._send(200 if result.get("ok") else 400, result)
            return
        if path != "/jobs":
            self._send(404, {"ok": False, "error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send(400, {"ok": False, "error": "bad json"})
            return
        result = enqueue(str(body.get("project_id") or ""), str(body.get("from_step") or body.get("step") or "") or None)
        self._send(200 if result.get("ok") else 400, result)


def run() -> None:
    store.ROOT.mkdir(parents=True, exist_ok=True)
    # FastAPI 0.141 + Starlette 1.6 in this image treat body/Request as query
    # fields. The stdlib server is the reliable loopback API.
    if os.environ.get("LUMENCUT_FASTAPI") == "1" and app is not None:
        import uvicorn

        uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)
        return
    httpd = ThreadingHTTPServer((HOST, PORT), StdHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    run()
