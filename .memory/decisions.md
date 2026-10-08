# Decisions

## 2026-10-07 - Package the existing pipeline rather than replace it

Keep `transcribe.py` and `summarize_chunked.py` as the canonical writers. Provide one generic CLI runner and three repo-local task skills. Use explicit input and output paths, optional recording-specific prompts, and locally cached model weights. Keep historical machine-specific wrappers and outputs outside Git. Use a local Git repository; no remote push or installation is part of this work.
