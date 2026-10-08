# Reproducible audio2md Agent Repo Implementation Plan

> **For agentic workers:** Execute the tasks inline in order and verify each task before moving on; do not install packages, run GPU jobs, or push.

**Goal:** Make the current two-stage audio pipeline safe and reproducible for humans and agents on new recordings.

**Architecture:** Keep `transcribe.py` and `summarize_chunked.py` unchanged as writers. A generic LSF-compatible shell runner calls them using an explicit audio path, output prefix, and optional seed/glossary paths; agent skills route tasks to the runner and existing CLI. Generated artifacts stay untracked.

**Tech Stack:** Python 3.11, stdlib unittest, Bash, LSF, faster-whisper/CTranslate2, PyTorch/Transformers.

---

### Task 1: Contract and test

**Files:** Create `tests/test_pipeline.py`, `run-pipeline.sh`.

- [ ] Write stdlib tests that invoke the actual runner using an isolated fake Python executable, asserting arguments with spaces, optional prompts, failure propagation, and independent Stage 2 rerun via the existing Python CLI.
- [ ] Run `python3 -m unittest discover -s tests -v` and observe a missing-runner failure.
- [ ] Implement the runner with explicit arguments, `PYTHON_BIN` override, output directory creation, optional files validation, Stage 1 short-circuit, and Stage 2 execution.
- [ ] Re-run tests and `bash -n run-pipeline.sh`; expect success and no output outside the test temporary directory.

### Task 2: Agent interface and environment

**Files:** Create `AGENTS.md`, `.agents/skills/process-recording/SKILL.md`, `.agents/skills/correct-translation/SKILL.md`, `.agents/skills/verify-handoff/SKILL.md`, `.gitignore`, `requirements.txt`, `.memory/progress.md`, `.memory/decisions.md`, `.memory/lessons.md`; modify `README.md`.

- [ ] Write concise task triggers, checkable completion criteria, and safety boundaries. Keep runtime configuration outside tracked files and use `PYTHON_BIN` for the existing environment.
- [ ] Document exact verified runner, Stage 2, LSF submission, monitoring, verification and prerequisites in README; explain model cache requirement and machine paths without embedding them in new runner.
- [ ] Validate path references, `bash -n`, `python3 -m unittest discover -s tests -v`, and `git check-ignore` after initializing Git.

### Task 3: Local Git repository

**Files:** Existing source and documentation only.

- [ ] Check all prospective tracked files for embedded credentials and inspect `git status`/ignored audio and outputs before staging.
- [ ] Initialize local Git repository (explicitly approved in the spec), stage only inspected source/docs/tests, and create one initial commit if identity permits.
- [ ] Confirm no audio, generated outputs, secrets, or machine-specific `config.sh` are tracked; verify clean git status. Do not push.
