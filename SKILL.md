---
name: audio2md
description: |
  Audio-to-markdown meeting summary pipeline for WEXAC cluster.
  Takes any audio file (m4a, mp3, wav), transcribes with faster-whisper on GPU,
  then translates Hebrew→English and structures into markdown using Qwen2.5-7B LLM.
  Use when the user wants to transcribe a meeting, summarize audio, or convert
  voice recordings to markdown documents.
---

# audio2md — Audio to Markdown Meeting Summaries

## Pipeline

1. **Transcribe**: `faster-whisper large-v3` on GPU (4× realtime)
2. **Summarize**: `Qwen/Qwen2.5-7B-Instruct` on GPU (translate + structure)

## Quick Commands

```bash
cd ~/dev/audio2md
./audio2md setup                  # First-time setup
./audio2md <audio-file>           # Full pipeline
./audio2md transcribe <file>      # Step 1 only
./audio2md summarize              # Step 2 only
./audio2md fetch [output.md]      # Get results
./audio2md status                 # Check progress
```

## Cluster Notes

- **GPU nodes**: `dgn06`, `dgn07` (A40), prefer `rhel96-gpu` queue
- **Avoid**: `hgn*` nodes (some don't have GPUs despite being in GPU queues)
- **Specific host**: use `-m dgn06` in bsub to target known GPU nodes
- **SSH**: passwordless to `login4.wexac.weizmann.ac.il`
