# Lessons

## 2026-07-26 - Initial SSH pipeline

### SSH and file transfer
- Use `scp` for audio files rather than rsync for single files.
- Use absolute paths in SSH commands to avoid tilde confusion.

### LSF gotchas
- `#BSUB -oo ~/path` does not expand `~`; use absolute paths.
- Some GPU-queue nodes have no actual GPUs; verify with `bhosts -gpu` and target a known GPU host if needed.

### Models and runtime
- faster-whisper `large-v3` with float16 on GPU gave good Hebrew transcription in the early pipeline (57% confidence on a mixed recording), with around 4x realtime on an A40.
- Qwen2.5-7B requires `tokenizer.apply_chat_template()` and float16 needs about 14 GB GPU memory. Early shared A40 runs achieved around 60 characters per second.
- Create an environment once outside batch jobs; reusing a cached model and environment avoids repeated setup.

## 2026-10-07 - Quiet split option is not symmetric

**What went wrong:** An initial offline test assumed `plan_windows(..., quiet_split=False)` would produce regular fixed-length windows; the existing function instead returns one window for a multi-window recording.
**Why:** In `transcribe.py`, the `else` branch for disabling quiet split assigns `end = total`, not the nominal cut.
**Correct approach:** Test the default quiet-split path used by the pipeline and flag the separate option bug rather than silently changing transcription behavior while packaging the repo.
**Files/commands involved:** `transcribe.py`, `tests/test_processing.py`, `python -m unittest discover -s tests -v`.

## 2026-10-07 - Unrelated audio2md histories

**What happened:** The packaged GPU pipeline and the earlier SSH CLI were separate Git roots, each with an `AGENTS.md`, `README.md`, `.gitignore`, and lesson file.
**Why it matters:** An automatic unrelated-history merge produces competing instructions and entry points.
**Correct approach:** Resolve instructions around one canonical workflow, retain the old CLI as explicitly historical, and preserve both histories without force-pushing.
**Files/commands involved:** `git merge --allow-unrelated-histories`, `AGENTS.md`, `README.md`, root `SKILL.md`.
