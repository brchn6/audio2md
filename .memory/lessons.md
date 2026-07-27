# audio2md — Lessons Learned

## 2026-07-26: Initial Pipeline

### SSH + File Transfer
- Use `scp` for audio files, not rsync (simpler for single files)
- Always use absolute paths in SSH commands to avoid tilde confusion

### LSF Gotchas
- `#BSUB -oo ~/path` does NOT expand `~` — use absolute paths `/home/...`
- Some GPU-queue nodes don't actually have GPUs — verify with `bhosts -gpu`
- Target specific known GPU hosts with `-m <hostname>` to avoid headless nodes

### faster-whisper
- `large-v3` model gives good Hebrew transcription (57% confidence on mixed recording)
- GPU acceleration: A40 does ~4× realtime
- Model caching in `~/.cache/huggingface/` — first run slow, subsequent fast
- Set `compute_type="float16"` for best GPU performance

### Qwen2.5-7B for Translation
- **Must use `tokenizer.apply_chat_template()`** — raw prompts don't work
- System prompt + user message format is required for instruction following
- 7B model in float16 needs ~14 GB VRAM (fits on A40 with 48 GB shared)
- Generation speed: ~60 chars/s on shared A40
- Output quality: good for structured summaries with participants, decisions, action items

### Conda Environment
- Creating env on each bsub job is wasteful — create once, reuse
- Packages needed: `faster-whisper`, `torch` (CUDA 12.4), `transformers`, `accelerate`, `sentencepiece`
- The `whisper-md` env persists across jobs in the user's home dir
