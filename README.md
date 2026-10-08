# audio2md

Transcribe long Hebrew recordings with English technical terms and turn them into an English translation plus structured summary. A GPU-enabled Python 3.11 environment runs two separate stages: `transcribe.py` uses faster-whisper `large-v3` (CTranslate2) and writes timestamped Markdown plus a JSONL window checkpoint; `summarize_chunked.py` uses PyTorch/Transformers with `Qwen/Qwen2.5-7B-Instruct` and writes English Markdown plus a JSON chunk checkpoint. `run-pipeline.sh` chains the stages and stops on failure. Completed chunks survive job interruptions.

## Prerequisites

- WEXAC LSF access to a GPU queue (the existing jobs used `short-gpu`, 2 CPU slots, 16 GB system memory, 18 GB GPU memory), or an equivalent GPU-enabled shell. Do not run inference on a WEXAC login node.
- A Python 3.11 interpreter with the tested direct dependency versions in `requirements.txt`, and locally cached `Systran/faster-whisper-large-v3` and `Qwen/Qwen2.5-7B-Instruct` model weights. No packages or model weights are bundled; this repo does not download them. Ask the operator to provision an environment outside the agent session if absent. `PYTHON_BIN` selects an existing Python interpreter.
- An audio file outside the repo; outputs stay in ignored `out/`. Optional seed and glossary files are recording-specific and should be passed only when relevant. The old meeting/podcast wrappers and prompts remain on the original host but are excluded from this repository.

## New recording on WEXAC

The following is the submission recipe; the generic runner has been tested offline, but a new-recording GPU submission has not been performed as part of repo packaging. Set `PYTHON_BIN` to an already provisioned GPU environment and use absolute paths for inputs and outputs:

```bash
cd /path/to/audio2md
mkdir -p out
export PYTHON_BIN=/path/to/existing/gpu-env/bin/python
AUDIO='/absolute/path/to/recording with spaces.m4a'
PREFIX="$PWD/out/recording-001"
# Optional: provide a seed and glossary specific to THIS recording (outside Git).
SEED=''
GLOSSARY=''
export LSB_JOB_REPORT_MAIL=N
bsub -q short-gpu -n 2 -R 'rusage[mem=8GB]' -R 'span[hosts=1]' \
  -gpu 'num=1:j_exclusive=no:gmem=18G' -W 120 \
  -oo "$PWD/out/run-%J.out" -eo "$PWD/out/run-%J.err" \
  ./run-pipeline.sh "$AUDIO" "$PREFIX" "$SEED" "$GLOSSARY"
```

The runner accepts `AUDIO OUTPUT_PREFIX [SEED_FILE [GLOSSARY_FILE]]`. If `SEED` and `GLOSSARY` are empty, no recording-specific terms are injected. If you are already in a GPU shell, run `./run-pipeline.sh "$AUDIO" "$PREFIX" "$SEED" "$GLOSSARY"` directly. For a resumed run, use the same prefix; it reuses complete windows and translation chunks. Use a new prefix for a new recording. The runner forces Hugging Face offline mode so missing cached models fail instead of downloading.

To monitor: `bjobs -l JOB_ID` and `tail -f out/run-JOB_ID.out out/run-JOB_ID.err`. Confirm `stage 1 exit: 0` and `stage 2 exit: 0` in stdout. An interrupted or failed Stage 2 leaves the Hebrew transcript available.

## Correct terms without retranscribing

Preserve the original by choosing a new report prefix. After checking the Hebrew transcript and, when necessary, the recording, write a recording-specific glossary outside tracked source. In a GPU shell run:

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$PYTHON_BIN" summarize_chunked.py \
  --input "$PREFIX.transcript.md" \
  --output "$PREFIX.corrected.summary.md" \
  --model Qwen/Qwen2.5-7B-Instruct --max-chars 6000 \
  --glossary-file /absolute/path/to/recording-glossary.md
```

To submit Stage 2 via LSF instead, reuse the resource and log flags in the previous `bsub` command and replace `./run-pipeline.sh ...` with the quoted Python invocation above. Do not add `--no-resume` to an existing output prefix: it can replace useful checkpoint state. The generated top-level digest and full translation require source review before claiming technical accuracy.

## Verify locally without a GPU

With an environment containing `requirements.txt` dependencies, the following command was run successfully in this repository:

```bash
cd /path/to/audio2md
/path/to/existing/gpu-env/bin/python -m unittest discover -s tests -v
bash -n run-pipeline.sh
```

Expected: 7 passing tests and no output from `bash -n`. The tests invoke the real runner with a temporary fake Python executable and directly test actual transcript chunking, translation normalization, report writing, and window coverage. They do not submit LSF jobs or load model weights.

For a real run, inspect `PREFIX.transcript.md` (window and segment counts; last timestamp near audio duration), `PREFIX.transcript.segments.jsonl` (one JSON record per completed window), `PREFIX.summary.md` (section digests and all translated sections), and `PREFIX.summary.summary.json` (one record per completed section). Check the LSF logs and compare technical passages against the Hebrew transcript and source audio. Use `.agents/skills/verify-handoff/SKILL.md` for the handoff checklist.

## Agent interface

`AGENTS.md` gives the always-on map. Task-specific skills live in `.agents/skills/process-recording/`, `.agents/skills/correct-translation/`, and `.agents/skills/verify-handoff/`. Source code, prompts, and tests are versioned; recordings, outputs, checkpoints, local environment config, and old machine-specific wrappers remain local. No remote push is part of setup.

## Limitations

- Automatic Hebrew transcription and English translation can mishear acronyms, names, or technical terms. Verify against audio before changing meaning.
- A translation chunk can silently omit a span; compare translated sections with the Hebrew source when completeness matters.
- The pre-existing `--no-quiet-split` option in `transcribe.py` currently produces one window for a multi-window file; the default quiet-split path is used here. This separate issue is not changed by repo packaging.
- `summarize.py` is a legacy single-pass script limited to the first 15,000 characters; use `summarize_chunked.py` for long recordings.
