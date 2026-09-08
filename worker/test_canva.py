import unittest

from worker.canva import PACKS, apply_canva_style, pack_of


class CanvaPackTests(unittest.TestCase):
    def test_eight_packs(self):
        self.assertEqual(len(PACKS), 8)
        self.assertEqual(pack_of("canva-bold-yt")["themeId"], "modern")
        self.assertIsNone(pack_of("missing"))

    def test_apply_fills_empty_style(self):
        next_scenes = apply_canva_style({"canvaStyleId": "canva-crime", "phrases": []})
        self.assertEqual(next_scenes["themeId"], "crime")
        self.assertEqual(next_scenes["brandColor"], "#e23a3a")
        self.assertEqual(next_scenes["editingStyle"]["grade"], "noir")
        self.assertEqual(next_scenes["graphicsDensity"], 0.58)

    def test_apply_keeps_explicit_theme(self):
        next_scenes = apply_canva_style({"canvaStyleId": "canva-pastel", "themeId": "history", "editingStyle": {"grade": "noir"}})
        self.assertEqual(next_scenes["themeId"], "history")
        self.assertEqual(next_scenes["editingStyle"]["grade"], "noir")
        self.assertEqual(next_scenes["editingStyle"]["plaqueRate"], 0.28)


if __name__ == "__main__":
    unittest.main()
