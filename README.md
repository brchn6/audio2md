# audio2md — Audio to English Markdown Summary

**Transform meeting recordings into structured English summaries using the WEXAC cluster's GPUs.**

Takes any audio file (m4a, mp3, wav, etc.) and runs it through a two-stage GPU pipeline:

```
Audio → faster-whisper (GPU) → transcript → Qwen LLM (GPU) → English summary.md
```

## Features

- 🎙️ **Any audio format** — m4a, mp3, wav, Zoom recordings
- 🌐 **Multi-language** — transcribes Hebrew, English, mixed — translates everything to English
- 🏗️ **Structured output** — Participants, Summary, Key Points, Decisions, Action Items
- 🚀 **GPU-accelerated** — 4× realtime transcription on A40/A100 GPUs
- 🔒 **Fully local** — no API calls, everything runs on the cluster
- 📦 **Self-contained** — one command from audio to summary

## Requirements

- Access to the **WEXAC cluster** (SSH key configured)
- `conda` available on the cluster (default on WEXAC)

## Quick Start

```bash
# 1. Setup (one-time)
cd ~/dev/audio2md
./audio2md setup

# 2. Run on any audio file
./audio2md ~/Downloads/meeting-recording.m4a

# 3. Get your summary
./audio2md fetch my-meeting-summary.md
```

## Commands

| Command | Description |
|---|---|
| `./audio2md setup` | One-time setup: create conda env, install models |
| `./audio2md <file>` | Full pipeline: transcribe + summarize |
| `./audio2md transcribe <file>` | Step 1: transcribe audio only |
| `./audio2md summarize` | Step 2: summarize existing transcript |
| `./audio2md fetch [output.md]` | Download results from cluster |
| `./audio2md status` | Check job progress and files |
| `./audio2md help` | Show full usage |

## Examples

```bash
# Basic usage
./audio2md meeting.m4a

# Custom output name
./audio2md ~/Downloads/voice.mp3 lab-meeting-2026-07-26.md

# Step-by-step (useful for long files)
./audio2md transcribe long-meeting.wav
# ... wait for transcription ...
./audio2md summarize
./audio2md fetch final-summary.md
```

## How It Works

```
Your Machine                    WEXAC Cluster (GPU nodes)
┌──────────────┐               ┌──────────────────────────┐
│  audio2md    │── scp audio ──→│  Step 1: faster-whisper  │
│  CLI tool    │               │  (large-v3, GPU, 4× RT)  │
│              │←── result ────│  → transcript.md          │
│              │               │                          │
│              │── submit ────→│  Step 2: Qwen2.5-7B       │
│              │               │  (translate + structure)  │
│              │←── result ────│  → english-summary.md     │
└──────────────┘               └──────────────────────────┘
```

## Configuration

Edit `config.sh` to customize:

- `CLUSTER` — SSH target (default: `login4`)
- `WHISPER_MODEL` — `large-v3` (best) or `medium` (faster)
- `TRANS_QUEUE` / `LLM_QUEUE` — GPU queues (default: `rhel96-gpu`)
- `GPU_MEM` — GPU memory reservation (default: `8G`)

## Tips

- **First run** takes longer (downloading models to cache). Subsequent runs are faster.
- **Large files** (>1 hour): use step-by-step mode (`transcribe` then `summarize`)
- **Multiple files**: the pipeline reuses cached models between runs
- **Watch progress**: `./audio2md status` shows jobs and files

## Architecture

```
~/dev/audio2md/
├── audio2md              # Main CLI entry point
├── config.sh             # Cluster configuration
├── README.md             # This file
├── INSTALL.md            # Setup guide for new users
├── SKILL.md              # AI assistant skill definition
├── AGENTS.md             # Agent instructions
├── .memory/lessons.md    # Lessons learned
├── Makefile              # Install, clean, test
├── src/
│   ├── transcribe.py     # Whisper transcription
│   └── summarize.py      # LLM translation + structuring
└── lsf/
    ├── transcribe.lsf    # LSF batch script for transcription
    └── summarize.lsf     # LSF batch script for LLM
```

## License

Free to use and distribute within the Weizmann Institute of Science.

Built by barc using open-source tools: faster-whisper (MIT), Qwen2.5 (Apache 2.0), Transformers (Apache 2.0).
