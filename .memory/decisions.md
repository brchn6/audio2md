# Decisions

## 2026-10-07 - Preserve both histories and designate a canonical workflow

Merge the unrelated `master` and `agent-ready-20261007` histories without rewriting either. Keep the original SSH CLI and its files available as legacy; use `run-pipeline.sh`, `transcribe.py`, and `summarize_chunked.py` for all new recordings. README and agent skill pointers lead to the canonical path.

## 2026-10-07 - Package the existing pipeline rather than replace it

Keep `transcribe.py` and `summarize_chunked.py` as the canonical writers. Provide one generic CLI runner and three repo-local task skills. Use explicit input and output paths, optional recording-specific prompts, and locally cached model weights. Keep historical machine-specific wrappers and outputs outside Git. Use a local Git repository; no remote push or installation is part of this work.
