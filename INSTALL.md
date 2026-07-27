# audio2md — Installation Guide

## For New Users at Weizmann Institute

### Prerequisites

1. **WEXAC cluster access** — you need an account on the cluster
2. **SSH key configured** — passwordless login to `login4`:
   ```bash
   ssh-keygen -t ed25519 -C "your@email.com"   # if you don't have a key
   ssh-copy-id login4
   ```
3. **`conda`** — available on the cluster by default

### Install

```bash
# Clone / copy the audio2md package to your home directory
cp -r /path/to/audio2md ~/dev/
cd ~/dev/audio2md

# Edit the config to point to your cluster
nano config.sh    # Change CLUSTER="login4" if needed

# Run setup (one-time, creates conda env and downloads models)
./audio2md setup
```

### First Run

```bash
# Transcribe + summarize a test file
./audio2md ~/Downloads/short-test.m4a

# Watch progress
./audio2md status

# Get results
./audio2md fetch result.md
```

### Troubleshooting

| Problem | Solution |
|---|---|
| `ssh: connection refused` | Check cluster access, VPN? |
| `bsub: command not found` | You're not on a WEXAC login node |
| `conda: command not found` | Run: `source /etc/profile.d/modules.sh` |
| GPU queue full | Change `TRANS_QUEUE` to `short-gpu` in `config.sh` |
| `No transcript.md found` | Transcription job hasn't finished yet — check with `./audio2md status` |
