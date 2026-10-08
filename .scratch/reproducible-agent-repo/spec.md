# Reproducible audio2md agent repo

## Goal
Package the existing `audio2md` Python/LSF pipeline as a locally versioned repository that another agent can operate for a new recording without guessing commands, reusing recording-specific names, or committing source audio and outputs.

## Scope
- Preserve working transcription and translation scripts and historical wrappers and reports in place.
- Add concise root `AGENTS.md` describing architecture, scope of edits, data boundary, and links to repo-local task skills.
- Add three repo-local skills under `.agents/skills/`: process a recording, correct terminology and rerun translation, and verify and hand off a run. Each has an explicit trigger and testable completion condition.
- Make a generic, parameterized run path based on the existing scripts; use recording-specific seed/glossary only when supplied by the operator. Document exact commands for a new recording, resumability, and GPU/LSF constraints.
- Add an environment manifest for the known Python dependencies without installing packages. Keep dependencies in one declared place; document model cache requirements and machine-local overrides without committing secrets or host paths.
- Add minimal offline tests exercising the actual chunk/window and report logic and validating workflow-facing commands without downloading models or submitting GPU jobs.
- Add `.gitignore` for audio, generated `out/`, checkpoints, machine-local settings, caches, and virtual environments. Initialize a local Git repository and commit only inspected source and documentation. Do not push.
- Document verified setup/run/check commands in `README.md` and initialize project `.memory/` for future agent continuity.

## Design
The existing `transcribe.py` remains the canonical Stage 1 writer for transcript Markdown and JSONL checkpoints. `summarize_chunked.py` remains the canonical Stage 2 writer for English Markdown and JSON checkpoints. A generic parameterized LSF wrapper invokes both in order and fails clearly if required local paths or models are missing; it must not embed meeting-specific names or audio paths. Repo-local skills instruct agents which wrapper/CLI to use for a task and where to stop for user decisions. README is the human entry point; `AGENTS.md` is the short always-on agent map. Checkpoints are outputs, not a second published data store.

## Acceptance
- A fresh clone has no audio, outputs, credentials, workstation-specific paths, or cached models committed.
- An agent can read `AGENTS.md` and discover the correct skill for each of the three tasks.
- README includes copy-paste commands to configure an existing environment, submit a new recording, monitor it, rerun only Stage 2, and verify resulting artifacts.
- Automated offline tests pass using available Python stdlib/unmodified installed runtime; shell wrappers pass `bash -n`; skill references resolve to real commands/files.
- Historical outputs remain locally intact; no package installation, remote push, or GPU rerun is required for packaging.
