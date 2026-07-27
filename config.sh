#!/bin/bash
# audio2md configuration
# Edit this file to match your cluster setup

# Load secrets from .env if present
[ -f "$(cd "${BASH_SOURCE[0]%/*}" && pwd)/.env" ] && source "$(cd "${BASH_SOURCE[0]%/*}" && pwd)/.env"

# Cluster SSH target (user@host) — e.g. "login-node"
CLUSTER="my-cluster"

# Working directory on cluster
REMOTE_DIR="\$HOME/dev/audio2md"

# Local working directory
LOCAL_DIR="$HOME/dev/audio2md"

# Conda environment name on cluster
CONDA_ENV="audio2md"

# GPU queue for transcription
TRANS_QUEUE="gpu-queue"
TRANS_HOST=""              # specific host (or leave empty)

# GPU queue for summarization
LLM_QUEUE="gpu-queue"
LLM_HOST=""                # specific host (or leave empty)

# GPU resources
GPU_MEM="8G"
CPU_CORES="2"
MEM_GB="10"

# Model settings
WHISPER_MODEL="large-v3"    # or "medium" for faster
LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"

# Output directory for results
OUTPUT_DIR="./"
