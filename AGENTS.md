# audio2md - agent orientation

Python 3.11, Bash, LSF/CUDA, faster-whisper `large-v3`, CTranslate2, PyTorch/Transformers with Qwen2.5-7B-Instruct. Read `README.md` for setup and verified commands.

- `transcribe.py` is the Stage 1 writer: audio -> timestamped Hebrew Markdown + `.segments.jsonl` resume state.
- `summarize_chunked.py` is the Stage 2 writer: transcript -> English report + `.summary.json` resume state.
- `run-pipeline.sh` chains both stages for an explicitly supplied audio file/output prefix; local `out/` and recordings are untracked.
- `requirements.txt` records tested top-level versions. Use an existing environment; ask before any package install, GPU job submission, or remote push.
- Use `.agents/skills/process-recording/SKILL.md` when asked to run a new recording; `.agents/skills/correct-translation/SKILL.md` when asked to correct technical translation; `.agents/skills/verify-handoff/SKILL.md` to validate and deliver outputs.
- Use recording-specific seed and glossary files only when relevant; do not silently substitute people, indices, or biology terms. Keep source recordings, outputs, secrets, and machine-specific profiles outside Git.
- Check offline changes with `python -m unittest discover -s tests -v` using an environment with the manifest dependencies and `bash -n run-pipeline.sh`. Do not rerun an output prefix with `--no-resume` if it holds work that must be preserved.
