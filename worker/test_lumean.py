import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from worker.lumean import STUDIO_TO_EL, template_body, unwrap, voice_id_for


class LumeanContractTests(unittest.TestCase):
    def test_voice_id_strips_prefix_and_maps_studio(self):
        self.assertEqual(voice_id_for("lumean:CwhRBWXzGAHq8TQ4Fs17"), "CwhRBWXzGAHq8TQ4Fs17")
        self.assertEqual(voice_id_for("lumean-eve"), STUDIO_TO_EL["eve"])
        self.assertEqual(voice_id_for("eve"), STUDIO_TO_EL["eve"])
        self.assertEqual(voice_id_for("JBFqnCBsd6RMkjVDRZzb"), "JBFqnCBsd6RMkjVDRZzb")
        self.assertEqual(voice_id_for(""), STUDIO_TO_EL["lumen"])

    def test_template_puts_voice_in_tts_settings_not_order(self):
        body = template_body("eve", "Desk Eve")
        self.assertEqual(body["service_key"], "elevenlabs")
        self.assertEqual(body["config"]["tts_settings"]["voice_id"], STUDIO_TO_EL["eve"])
        self.assertNotIn("voice_id", body)
        dumped = json.dumps(body)
        self.assertNotIn("orders.voice_id", dumped)
        self.assertIn("eleven_multilingual_v2", dumped)

    def test_unwrap_data_envelope(self):
        self.assertEqual(unwrap({"success": True, "data": {"id": "abc"}}), {"id": "abc"})
        self.assertEqual(unwrap({"voices": []}), {"voices": []})

    def test_speak_skips_without_key(self):
        from worker import lumean

        dest = Path(tempfile.gettempdir()) / "lumean-empty.mp3"
        duration, words = lumean.speak_one("Hello", "eve", "", dest)
        self.assertEqual(duration, 0.0)
        self.assertEqual(words, [])
        self.assertIn("LUMEAN_API_KEY", lumean.LAST_ERROR)


class LumeanHttpTests(unittest.TestCase):
    def test_ensure_template_caches_id(self):
        from worker import lumean

        calls: list[tuple[str, str]] = []

        def fake_request(method, path, api_key, **kwargs):
            calls.append((method, path))
            if path == "/templates":
                return 201, {"data": {"id": "tmpl-1"}}
            return 404, {}

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(lumean, "_cache_path", return_value=Path(tmp) / "t.json"):
                with patch.object(lumean, "_request", side_effect=fake_request):
                    first = lumean.ensure_template("key", "eve")
                    second = lumean.ensure_template("key", "eve")
        self.assertEqual(first, "tmpl-1")
        self.assertEqual(second, "tmpl-1")
        self.assertEqual(calls, [("POST", "/templates")])


if __name__ == "__main__":
    unittest.main()
