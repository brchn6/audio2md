# Lessons

## 2026-10-07 - Quiet split option is not symmetric

**What went wrong:** An initial offline test assumed `plan_windows(..., quiet_split=False)` would produce regular fixed-length windows; the existing function instead returns one window for a multi-window recording.
**Why:** In `transcribe.py`, the `else` branch for disabling quiet split assigns `end = total`, not the nominal cut.
**Correct approach:** Test the default quiet-split path used by the pipeline and flag the separate option bug rather than silently changing transcription behavior while packaging the repo.
**Files/commands involved:** `transcribe.py`, `tests/test_processing.py`, `python -m unittest discover -s tests -v`.
