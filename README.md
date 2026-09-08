# LumenCut

Personal 1080p documentary desk. Paste a 1,500–4,000 word script. The desk voices it, matches stills and ≤5s cuts, lays motion graphics, and opens a layered timeline. Export MP4, thumbnail, title, description, and CC attributions.

Everything lives in `./data`. No accounts, no sign-in, no payments, no credits.

Repo: [github.com/olyaolya89/LumenCut](https://github.com/olyaolya89/LumenCut)

## Install in 10 minutes

### What you need

- [Node.js 22+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/downloads/)
- [ffmpeg](https://ffmpeg.org/download.html) on `PATH` (ffprobe too)
- Optional: [Docker](https://docs.docker.com/get-docker/) if you prefer compose

### Without Docker

```bash
git clone https://github.com/olyaolya89/LumenCut.git lumencut && cd lumencut
cp .env.example .env
# Set LLM_PROVIDER=gemini|grok|ollama and the matching key (or leave Gemini empty for heuristic analysis).
npm install
python3 -m pip install -r worker/requirements.txt
# Edge TTS is the default voice. No key. Search and ffmpeg stay local/free.
npm run dev
```

Open the desk at the printed URL. Paste a script on the home screen. Settings hold optional keys and the projects folder (`./data`).

`npm run dev` starts the UI on port 8080 and the film worker on 8091. It loads `.env` automatically.

### With Docker

```bash
git clone https://github.com/olyaolya89/LumenCut.git lumencut && cd lumencut
docker compose up --build
```

The web UI is on port 8080. The film worker stays internal on 8091. Projects and the media cache bind-mount `./data`.

### Check it works

```bash
npm test
```

That runs unit tests (script split, layout validator: no holes, clips ≤5s) and one 200-word e2e: paste → timeline → MP4.

## Keys (optional except the LLM you pick)

The desk runs without keys. Edge TTS, Wikimedia, Openverse, Internet Archive, ffmpeg, and the local `/public/library` stills are enough. The only billable switch is `LLM_PROVIDER`.

Put keys in `.env` (copy `.env.example`) or **Settings**. Env wins over `data/config.json`. Do not commit `.env`.

| Key | Used for | Get it |
|---|---|---|
| `LLM_PROVIDER` | `gemini` · `grok` · `ollama` | `.env` |
| _(none)_ | Edge Neural TTS (default, unlimited) | built in — [edge-tts](https://github.com/rany2/edge-tts) |
| _(none)_ | Wikimedia / Wikipedia stills & video | [Wikimedia Commons](https://commons.wikimedia.org/) |
| _(none)_ | Openverse CC search | [Openverse](https://openverse.org/) |
| _(none)_ | Internet Archive | [archive.org](https://archive.org/) |
| `GEMINI_API_KEY` | Scene analysis when `LLM_PROVIDER=gemini` | [aistudio.google.com](https://aistudio.google.com/apikey) |
| `XAI_API_KEY` | Scene analysis + Imagine when `LLM_PROVIDER=grok` | [console.x.ai](https://console.x.ai/) |
| `OLLAMA_HOST` / `OLLAMA_MODEL` | Local LLM when `LLM_PROVIDER=ollama` | [ollama.com](https://ollama.com/) |
| `PEXELS_API_KEY` | Pexels photos & video | [pexels.com/api](https://www.pexels.com/api/) |
| `PIXABAY_API_KEY` | Pixabay photos & video | [pixabay.com/api/docs](https://pixabay.com/api/docs/) |
| `UNSPLASH_ACCESS_KEY` | Unsplash photos | [unsplash.com/developers](https://unsplash.com/developers) |
| `ELEVENLABS_API_KEY` | ElevenLabs catalogue voices | [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) |
| `YOUTUBE_DATA_API_KEY` | Outlier thumbnails / channel search | [Google Cloud YouTube Data API](https://console.cloud.google.com/apis/library/youtube.googleapis.com) |
| `SERPAPI_KEY` | Optional Google Images | [serpapi.com](https://serpapi.com/) |

```bash
export LLM_PROVIDER=gemini       # gemini | grok | ollama
export TTS_DEFAULT=edge          # edge | elevenlabs
export RENDER_ENGINE=ffmpeg      # ffmpeg | remotion
export DATA_DIR=./data
export MAX_CLIP_MS=5000
export CONCURRENT_DOWNLOADS=6
```

## Tests

```bash
npm test
npm run typecheck
```

- Script split: `src/lib/studio/normalize-script.test.ts`, `worker/test_normalize.py`
- Layout validator (no holes, ≤5s): `src/lib/studio/layout.test.ts`, `worker/test_layout.py`
- E2E 200-word paste → MP4: `worker/test_e2e.py`
