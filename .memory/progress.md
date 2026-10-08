# Progress

2026-10-07: Integrated the previously independent SSH CLI and GPU pipeline histories onto `master` in an isolated worktree. `run-pipeline.sh` and repo-local skills are canonical; `audio2md`, `src/`, `lsf/`, `Makefile`, `INSTALL.md`, and root `SKILL.md` remain as labeled legacy artifacts. The merge does not require package installs or model downloads.

2026-10-07: Existing two-stage GPU pipeline was packaged with a parameterized `run-pipeline.sh`, offline unittest checks, environment manifest, `AGENTS.md`, and repo-local skills for processing, correction, and handoff. The original wrappers, meeting-specific prompts, recordings, and generated reports remain locally present but excluded from version control. Offline tests passed (7/7); a new-recording GPU run has not been performed as part of packaging. See `README.md` for commands and limitations.
