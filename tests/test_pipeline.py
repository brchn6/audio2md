"""Offline tests of the real shell runner using a recording-safe fake interpreter."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run-pipeline.sh"


class PipelineRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.audio = self.base / "recording with spaces.m4a"
        self.audio.write_bytes(b"test")
        self.prefix = self.base / "results" / "my recording"
        self.log = self.base / "calls.txt"
        self.fake = self.base / "fake-python"
        self.fake.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "with open(os.environ['CALL_LOG'], 'a') as f:\n"
            "    f.write(repr(sys.argv[1:]) + '\\n')\n"
            "if os.environ.get('FAIL_STAGE') and os.environ['FAIL_STAGE'] in sys.argv[1]:\n"
            "    sys.exit(7)\n"
        )
        self.fake.chmod(0o700)

    def run_pipeline(self, *extra, fail_stage=None):
        env = dict(os.environ, PYTHON_BIN=str(self.fake), CALL_LOG=str(self.log))
        if fail_stage:
            env["FAIL_STAGE"] = fail_stage
        return subprocess.run(
            ["bash", str(RUNNER), str(self.audio), str(self.prefix), *map(str, extra)],
            text=True, capture_output=True, env=env, cwd=self.base,
        )

    def test_new_recording_calls_both_stages_with_quoted_paths(self):
        seed = self.base / "seed.txt"
        glossary = self.base / "terms.md"
        seed.write_text("names")
        glossary.write_text("terms")
        result = self.run_pipeline(seed, glossary)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text().splitlines()
        self.assertEqual(len(calls), 2)
        self.assertIn(repr(str(self.audio)), calls[0])
        self.assertIn(repr(str(seed)), calls[0])
        self.assertIn(repr(str(glossary)), calls[1])
        self.assertIn(repr(str(self.prefix) + ".transcript.md"), calls[1])
        self.assertTrue(self.prefix.parent.is_dir())

    def test_stage_one_failure_does_not_run_stage_two(self):
        result = self.run_pipeline(fail_stage="transcribe.py")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(len(self.log.read_text().splitlines()), 1)

    def test_missing_optional_file_fails_before_stages(self):
        result = self.run_pipeline(self.base / "missing-seed.txt")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
