---
name: process-recording
description: Use when asked to transcribe a new Hebrew audio file or produce its English translation and meeting summary with audio2md.
---

# Process a recording

1. Read the repo `README.md` run instructions. Obtain the recording path and choose a new, unused output prefix under `out/`. Confirm the file exists and can be read. Use the existing GPU Python environment from `requirements.txt` and cached Whisper large-v3 and Qwen2.5-7B-Instruct models. Ask before package installs or GPU job submissions if approval is required.
2. Use only applicable seed/glossary files supplied for this recording; omit them otherwise. For GPU submission, follow the `bsub` recipe in README with absolute audio/output paths and optional seed/glossary files. `run-pipeline.sh` also accepts the same positional arguments directly in a GPU-enabled shell. Quoting matters when audio paths contain spaces.
3. Monitor LSF job and both output logs. Stage 1 failure must leave Stage 2 unrun; Stage 2 failure leaves the transcript intact. A normal rerun with the same prefix resumes from `.segments.jsonl` and `.summary.json`.
4. Complete only after using `verify-handoff` to check duration coverage, segment and chunk counts, job exit status, and human-readable artifacts. Keep recordings, reports, and checkpoints outside Git.
