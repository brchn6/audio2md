# audio2md — AI Agent Instructions

When working on this project, follow these guidelines:

## Architecture

- `audio2md` — Main CLI entry point (bash script)
- `src/transcribe.py` — Python: faster-whisper on GPU
- `src/summarize.py` — Python: Qwen2.5 LLM translation + structuring
- `lsf/transcribe.lsf` — LSF batch script for transcription
- `lsf/summarize.lsf` — LSF batch script for summarization
- `config.sh` — Cluster configuration (edit for each user)

## Key Patterns

### LSF Job Submission
The pipeline submits separate bsub jobs for transcription and summarization.
Jobs run on `rhel96-gpu` queue, targeting `dgn06` host specifically (some nodes
in GPU queues don't actually have GPUs — e.g. `hgn*` nodes).

### GPU Memory
- `faster-whisper large-v3` ~4 GB VRAM
- `Qwen2.5-7B-Instruct float16` ~14 GB VRAM
- Request `gmem=8G` for whisper, `gmem=16G` would be safer for LLM but 8G works
  if the node has enough total VRAM (A40 has 48 GB shared across jobs)

### Model Caching
Models are cached in `~/.cache/huggingface/` on the cluster after first download.
Subsequent runs are faster. The conda env `audio2md` persists after `./audio2md setup`.

## Known Issues

1. **hgn* nodes** — appear in GPU queues but lack GPUs. Always use `-m dgn06`
2. **First run** — slow (downloading ~3 GB Whisper model + ~4 GB LLM). Cache persists.
3. **Tilde in LSF paths** — `~` is NOT expanded in `#BSUB -oo/-eo`. Use absolute paths.
4. **Transcription context** — 15000 char limit for LLM. Longer transcripts get truncated.
