---
name: audio2md-legacy-cli
description: Use when maintaining the historical audio2md SSH CLI, not when processing new recordings through the canonical GPU pipeline.
---

# Historical SSH CLI

`audio2md`, `src/`, `lsf/`, `config.sh`, `Makefile`, and `INSTALL.md` belong to the preserved pre-merge workflow. The CLI submits two separate GPU jobs over SSH and its single-pass summarizer truncates long transcripts. For new recordings, follow `README.md` and `.agents/skills/process-recording/SKILL.md` instead.

When asked to change this historical CLI, inspect its current source and host configuration before editing. `./audio2md setup` installs dependencies and downloads model weights; `Makefile` contains destructive cleanup targets. Obtain explicit approval for installs, downloads, and data deletion. Keep credentials in an ignored `.env`, never in tracked `config.sh`.
