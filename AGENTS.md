# audio2md - agent orientation

Canonical pipeline: Python 3.11, Bash, LSF/CUDA, faster-whisper `large-v3`, CTranslate2, PyTorch/Transformers with Qwen2.5-7B-Instruct. Read `README.md` for setup and verified commands.

- `transcribe.py` writes the timestamped Hebrew transcript and `.segments.jsonl` checkpoint. `summarize_chunked.py` writes the English report and `.summary.json` checkpoint. `run-pipeline.sh` chains them for explicit input and output paths.
- `requirements.txt` records tested top-level versions. Use an existing environment; ask before package installs, GPU job submissions, or remote pushes.
- Use `.agents/skills/process-recording/SKILL.md` for a new recording, `.agents/skills/correct-translation/SKILL.md` for a glossary-backed Stage 2 correction, and `.agents/skills/verify-handoff/SKILL.md` for checking and delivering artifacts.
- Use recording-specific seed and glossary files only when relevant. Keep source recordings, generated outputs, secrets, and local overrides out of Git. Use a new report path instead of overwriting valuable checkpoints.
- Validate offline with `python -m unittest discover -s tests -v` in an environment with the manifest dependencies, and `bash -n run-pipeline.sh`.

## Historical CLI

The pre-merge `audio2md` SSH CLI, `src/`, `lsf/`, `Makefile`, `INSTALL.md`, `config.sh`, and root `SKILL.md` are preserved for history but are not the canonical pipeline. The old summarizer truncates long transcripts. Its setup and cleanup commands may install packages, download models, or delete data; never run them as part of the canonical workflow. `config.sh` is a tracked legacy template; keep real host configuration and credentials in an ignored local `.env` or outside the repository. Do not silently update two pipelines for one task.
