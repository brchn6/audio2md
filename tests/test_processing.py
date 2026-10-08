"""Offline behavior checks against the production processing functions."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from summarize_chunked import build_chunks, normalize_translation, parse_transcript, write_report
from transcribe import SAMPLE_RATE, plan_windows


class ProcessingTests(unittest.TestCase):
    def test_transcript_segments_reach_chunker_without_splitting_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.md"
            path.write_text("# Transcript\n\n**[0:01.0]** one two\n\n**[0:02.0]** three four\n")
            chunks = build_chunks(parse_transcript(path), max_chars=8)
            self.assertEqual(chunks, [[("0:01.0", "one two")], [("0:02.0", "three four")]])

    def test_report_contains_every_translated_section_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            state = {"chunks": [
                {"range": "[0:01 - 0:02]", "translation": "first", "digest": "- first"},
                {"range": "[0:03 - 0:04]", "translation": "second", "digest": "- second"},
            ], "global": "## Summary\nBody", "digests": True}
            meta = {"source": "test.md", "model": "test", "n_segments": 2, "n_chunks": 2, "t_start": __import__("time").time()}
            write_report(path, state, meta)
            text = path.read_text()
            self.assertEqual(text.count("## Summary"), 1)
            self.assertEqual(text.count("### Section 1"), 2)  # digest + translation
            self.assertIn("first", text)
            self.assertIn("second", text)

    def test_translation_normalization(self):
        self.assertEqual(normalize_translation("Yumi8 chromosome on context MINID"), "Y-UMI 8 chromosomal context mini-D")

    def test_default_windows_cover_audio_in_order(self):
        audio = np.zeros(int(3.5 * SAMPLE_RATE), dtype=np.float32)
        windows = plan_windows(audio, 1.0, quiet_split=True)
        self.assertEqual(windows[0][0], 0.0)
        self.assertEqual(windows[-1][1], 3.5)
        self.assertTrue(all(a[1] == b[0] for a, b in zip(windows, windows[1:])))


if __name__ == "__main__":
    unittest.main()
