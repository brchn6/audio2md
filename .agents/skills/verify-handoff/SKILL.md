---
name: verify-handoff
description: Use when checking audio2md transcription coverage, translation completeness, job success, or preparing a transcript and report for human handoff.
---

# Verify and hand off

1. Read the LSF stdout/stderr and check both stage exit codes, not just the presence of files. Inspect the actual transcript and report for empty sections, duplicated headings, obvious name/term substitutions, and dropped spans. A zero exit code alone does not establish translation fidelity.
2. Load `.segments.jsonl` and `.summary.json` with Python's `json` module. Compare windows done, segment count, and last timestamp to audio duration; compare Stage 2 chunk count to report section count. Do not treat a digest as a substitute for a full translation.
3. For technical claims and uncertain speech, compare the English section to the Hebrew transcript and source recording. Mark uncertain readings honestly rather than inventing certainty. Preserve earlier versions for comparison.
4. Give the user both file paths plus a short contents summary and explicitly state what was verified and what remains uncertain. Complete only when both deliverables are readable and the evidence checks match.
