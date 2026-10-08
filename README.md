# audio2md

Canonical workflow: transcribe long Hebrew recordings with faster-whisper `large-v3`, then translate and summarize with `Qwen/Qwen2.5-7B-Instruct`. `transcribe.py` writes timestamped Hebrew Markdown and `.segments.jsonl` checkpoints; `summarize_chunked.py` writes English Markdown and `.summary.json` checkpoints. `run-pipeline.sh` chains both stages and stops on failure. Resume is automatic for the same output prefix.

## Prerequisites

- WEXAC LSF access to a GPU queue such as `short-gpu`, or an equivalent GPU-enabled shell. Do not run inference on a WEXAC login node.
- A Python 3.11 environment containing the versions in `requirements.txt`, with `Systran/faster-whisper-large-v3` and `Qwen/Qwen2.5-7B-Instruct` already cached. Models and packages are not bundled or downloaded by the canonical runner. `PYTHON_BIN` selects that existing interpreter.
- Audio outside the repository. `out/`, recordings, local seed/glossary files, and credentials stay untracked. The tracked `config.sh` is only for the historical CLI; do not put real host details or credentials in it.

## Run a new recording on WEXAC

This GPU submission recipe has not been run for a new recording as part of this merge; the generic runner was tested offline. Set absolute paths and an existing Python interpreter:

```bash
cd /path/to/audio2md
mkdir -p out
export PYTHON_BIN=/path/to/existing/gpu-env/bin/python
AUDIO='/absolute/path/to/recording with spaces.m4a'
PREFIX="$PWD/out/recording-001"
SEED=''      # optional file for this recording only
GLOSSARY=''  # optional file for this recording only
export LSB_JOB_REPORT_MAIL=N
bsub -q short-gpu -n 2 -R 'rusage[mem=8GB]' -R 'span[hosts=1]' \
  -gpu 'num=1:j_exclusive=no:gmem=18G' -W 120 \
  -oo "$PWD/out/run-%J.out" -eo "$PWD/out/run-%J.err" \
  ./run-pipeline.sh "$AUDIO" "$PREFIX" "$SEED" "$GLOSSARY"
```

The runner accepts `AUDIO OUTPUT_PREFIX [SEED_FILE [GLOSSARY_FILE]]`; empty optional arguments add no meeting-specific vocabulary. A rerun with the same prefix resumes completed windows and translation chunks. For another recording use a new prefix. The runner forces Hugging Face offline mode so a missing cached model fails rather than downloading. In a GPU shell, call `./run-pipeline.sh "$AUDIO" "$PREFIX" "$SEED" "$GLOSSARY"` directly.

Monitor with `bjobs -l JOB_ID` and `tail -f out/run-JOB_ID.out out/run-JOB_ID.err`. Confirm both `stage 1 exit: 0` and `stage 2 exit: 0` in the job log.

## Correct a translation without retranscribing

Compare the English report against the Hebrew transcript and audio first. Put recording-specific terms in a glossary outside tracked files, choose a new report name to preserve the original, then run in a GPU shell:

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$PYTHON_BIN" summarize_chunked.py \
  --input "$PREFIX.transcript.md" \
  --output "$PREFIX.corrected.summary.md" \
  --model Qwen/Qwen2.5-7B-Instruct --max-chars 6000 \
  --glossary-file /absolute/path/to/recording-glossary.md
```

For Stage 2 in LSF, reuse the GPU resource/log flags above and submit this Python command instead of the full runner. Do not use `--no-resume` on an output path whose checkpoint you need to preserve.

## Offline verification

Using an existing environment containing `requirements.txt` dependencies:

```bash
cd /path/to/audio2md
/path/to/existing/gpu-env/bin/python -m unittest discover -s tests -v
bash -n run-pipeline.sh
```

Expected: 7 passing tests and no output from `bash -n`. Tests invoke the real runner using a temporary fake interpreter and exercise production chunking, normalization, report writing, and window coverage; no GPU or model weights are used. For a real run, compare transcript window and segment counts and last timestamp to the audio duration, count translated sections and `.summary.json` chunks, inspect job exit codes, then source-check technical passages. See `.agents/skills/verify-handoff/SKILL.md`.

## Agent interface

`AGENTS.md` is the always-on map. Repo-local skills in `.agents/skills/process-recording/`, `.agents/skills/correct-translation/`, and `.agents/skills/verify-handoff/` define tasks and completion checks. `requirements.txt` records the tested direct dependency versions; it is not a full lockfile. No remote push, package install, or model download is part of local verification.

## Historical CLI (preserved, not the recommended workflow)

The original SSH-based `./audio2md` entry point, `src/`, `lsf/`, `config.sh`, `Makefile`, `INSTALL.md`, and root `SKILL.md` remain in the merged history. They describe a different two-job workflow with a single-pass summarizer that truncates long transcripts. Use `run-pipeline.sh` and the repo-local skills for new work. The old `Makefile` contains destructive `clean` and `reset` targets; do not invoke them without explicit approval. The old `./audio2md setup` installs dependencies and downloads models; it is not required by the canonical path.

## Known limitations

- Whisper and Qwen can mishear names and technical terms, and a translation chunk can silently omit a span. Compare against the audio before claiming a complete or accurate translation.
- The existing `--no-quiet-split` option in `transcribe.py` produces one window for a multi-window file; use the default quiet-split path until that separate issue is fixed.
- `summarize.py` is a legacy single-pass implementation limited to the beginning of long transcripts; use `summarize_chunked.py`.
