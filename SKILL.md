---
name: audio2md
description: |
  Audio-to-markdown meeting summary pipeline for HPC clusters.
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

- **GPU queues**: Use your cluster's GPU queue (e.g. `gpu`, `short-gpu`)
- **GPU memory**: Request at least 8 GB GPU memory for Whisper, 16 GB for LLM
- **Specific hosts**: If some nodes lack GPUs, target known GPU hosts with `-m`
- **SSH**: Configure passwordless SSH to your cluster's login node
