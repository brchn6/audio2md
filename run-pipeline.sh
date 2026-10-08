#!/usr/bin/env bash
# Usage: run-pipeline.sh AUDIO OUTPUT_PREFIX [SEED_FILE [GLOSSARY_FILE]]
# Submit through LSF for GPU inference; no recording-specific defaults.
set -euo pipefail

if (( $# < 2 || $# > 4 )); then
    echo "Usage: $0 AUDIO OUTPUT_PREFIX [SEED_FILE [GLOSSARY_FILE]]" >&2
    exit 2
fi

AUDIO=$1
PREFIX=$2
SEED=${3:-}
GLOSSARY=${4:-}
PY=${PYTHON_BIN:-python3}
# Fail instead of silently fetching a model on a new machine.
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

for file in "$AUDIO" ${SEED:+"$SEED"} ${GLOSSARY:+"$GLOSSARY"}; do
    if [[ ! -f "$file" ]]; then
        printf 'Missing input file: %s\n' "$file" >&2
        exit 2
    fi
done
if ! command -v "$PY" >/dev/null 2>&1; then
    printf 'Python interpreter not found: %s\n' "$PY" >&2
    exit 2
fi
mkdir -p "$(dirname "$PREFIX")"

transcribe_args=(--input "$AUDIO" --output "$PREFIX.transcript.md" --language he --chunk-seconds 600 --beam-size 5)
if [[ -n "$SEED" ]]; then transcribe_args+=(--initial-prompt-file "$SEED"); fi
if "$PY" "$ROOT/transcribe.py" "${transcribe_args[@]}"; then
    echo "stage 1 exit: 0"
else
    rc=$?
    echo "stage 1 exit: $rc; stage 2 skipped" >&2
    exit "$rc"
fi

summary_args=(--input "$PREFIX.transcript.md" --output "$PREFIX.summary.md" --model Qwen/Qwen2.5-7B-Instruct --max-chars 6000)
if [[ -n "$GLOSSARY" ]]; then summary_args+=(--glossary-file "$GLOSSARY"); fi
if "$PY" "$ROOT/summarize_chunked.py" "${summary_args[@]}"; then
    echo "stage 2 exit: 0"
else
    rc=$?
    echo "stage 2 exit: $rc; transcript remains available" >&2
    exit "$rc"
fi
