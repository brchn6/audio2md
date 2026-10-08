#!/usr/bin/env python3
"""
audio2md - Transcription Module
Transcribes audio files using faster-whisper on GPU.

Long-file behaviour (2026-10-05 rewrite):
  * the audio is decoded once, then transcribed in fixed windows;
  * each finished window is appended to a .segments.jsonl sidecar and the
    markdown is rewritten from that sidecar, so an interrupted job keeps
    everything already transcribed and a rerun continues where it stopped;
  * window boundaries are moved to the quietest 100 ms frame near the nominal
    cut, because a fixed cut lands mid-word;
  * language defaults to auto-detect but should be pinned (--language he) for
    Hebrew: auto-detect slides into English on Hebrew speech that carries many
    English loanwords;
  * condition_on_previous_text is off: left on it degenerates into repetition
    loops across an hour-long file.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

SAMPLE_RATE = 16000


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fmt_ts(seconds):
    h, rem = divmod(float(seconds), 3600.0)
    m, s = divmod(rem, 60.0)
    if h:
        return f"{int(h)}:{int(m):02d}:{s:04.1f}"
    return f"{int(m)}:{s:04.1f}"


def pick_boundary(audio, target, search=20.0, frame=0.1, floor=0.0):
    """Move a window boundary to the quietest 100 ms frame near `target`."""
    f = int(frame * SAMPLE_RATE)
    lo = max(int(floor * SAMPLE_RATE), int((target - search) * SAMPLE_RATE))
    hi = min(len(audio), int((target + search) * SAMPLE_RATE))
    n = (hi - lo) // f
    if n <= 1:
        return float(target)
    blocks = audio[lo:lo + n * f].reshape(n, f).astype(np.float32)
    rms = np.sqrt((blocks ** 2).mean(axis=1))
    return (lo + int(np.argmin(rms)) * f) / SAMPLE_RATE


def plan_windows(audio, chunk_seconds, quiet_split):
    """Absolute [start, end) windows covering the whole file."""
    total = len(audio) / SAMPLE_RATE
    windows = []
    start = 0.0
    while start < total - 0.05:
        nominal_end = min(start + chunk_seconds, total)
        if quiet_split and nominal_end < total - 1.0:
            end = pick_boundary(audio, nominal_end, floor=start + chunk_seconds / 2)
        else:
            end = total
        windows.append((start, end))
        start = end
    return windows


def load_sidecar(path):
    records = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            records[int(rec["chunk"])] = rec
    return records


def write_markdown(out_path, records, meta):
    ordered = [records[k] for k in sorted(records)]
    # Wall-clock so far. The rate must divide audio seconds by elapsed seconds;
    # dividing by meta['processed'] (also audio seconds) always yields ~1.0x.
    elapsed = time.time() - meta["t_start"]
    lines = [
        "# Meeting Transcript\n",
        "",
        f"- **Source:** `{meta['source']}`",
        f"- **Language:** {meta['language']} (pinned)" if meta.get("pinned") else f"- **Language:** {meta.get('language', 'unknown')}",
        f"- **Duration:** {meta['duration']:.0f}s ({meta['duration'] / 60:.1f} min)",
        f"- **Model:** {meta['model']}",
        f"- **Windows done:** {len(ordered)}/{meta['n_windows']}",
        f"- **Segments:** {sum(len(r['segments']) for r in ordered)}",
        f"- **Processing:** {elapsed:.0f}s elapsed"
        + (f" ({meta['duration'] / max(elapsed, 1):.1f}x realtime)" if meta.get("processed") else ""),
        "",
        "---",
        "",
    ]
    for rec in ordered:
        for start, text in rec["segments"]:
            lines.append(f"**[{fmt_ts(start)}]** {text}")
            lines.append("")
    lines.append("---")
    lines.append(f"*Transcribed by faster-whisper {meta['model']} on GPU*")
    lines.append("")
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    tmp.replace(out_path)


def transcribe(audio_path, model_name="large-v3", output="transcript.md",
               language=None, chunk_seconds=600.0, quiet_split=True,
               beam_size=5, resume=True, max_duration=None, initial_prompt=None):
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = out_path.with_suffix(".segments.jsonl")

    log(f"Decoding {audio_path}")
    t0 = time.time()
    audio = decode_audio(str(audio_path), sampling_rate=SAMPLE_RATE)
    duration = len(audio) / SAMPLE_RATE
    if max_duration:
        audio = audio[: int(max_duration * SAMPLE_RATE)]
    log(f"Decoded {duration / 60:.1f} min in {time.time() - t0:.0f}s "
        f"({audio.nbytes / 1e6:.0f} MB in RAM)")

    windows = plan_windows(audio, chunk_seconds, quiet_split)
    log(f"Planned {len(windows)} windows of <= {chunk_seconds:.0f}s")

    meta = {
        "source": str(audio_path),
        "language": language or "auto",
        "pinned": bool(language),
        "duration": duration,
        "model": model_name,
        "n_windows": len(windows),
        "t_start": time.time(),
        "processed": 0.0,
    }

    records = load_sidecar(sidecar) if resume else {}
    if records:
        log(f"Resuming: {len(records)}/{len(windows)} windows already done")

    log(f"Loading Whisper model: {model_name}")
    if initial_prompt:
        log(f"Seed prompt: {len(initial_prompt)} chars")
    t0 = time.time()
    model = WhisperModel(model_name, device="cuda", compute_type="float16")
    log(f"Model loaded in {time.time() - t0:.0f}s")

    for i, (start, end) in enumerate(windows):
        if i in records:
            continue
        clip = audio[int(start * SAMPLE_RATE): int(end * SAMPLE_RATE)]
        t0 = time.time()
        segments, info = model.transcribe(
            clip,
            language=language,
            beam_size=beam_size,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=initial_prompt,
            log_progress=False,
        )
        seg_list = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                seg_list.append([round(start + seg.start, 2), text])

        rec = {
            "chunk": i,
            "window": [round(start, 2), round(end, 2)],
            "language": info.language,
            "language_probability": round(float(info.language_probability), 4),
            "detected_duration": round(float(info.duration), 2),
            "seconds": round(time.time() - t0, 1),
            "segments": seg_list,
        }
        with sidecar.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
        records[i] = rec
        meta["language"] = info.language if not language else language
        meta["processed"] += rec["detected_duration"]

        write_markdown(out_path, records, meta)
        log(f"Window {i + 1}/{len(windows)} [{fmt_ts(start)}-{fmt_ts(end)}] "
            f"{len(seg_list)} segments in {rec['seconds']:.0f}s "
            f"({rec['detected_duration'] / max(rec['seconds'], 1):.1f}x realtime)")

    write_markdown(out_path, records, meta)
    total_segments = sum(len(r["segments"]) for r in records.values())
    elapsed = time.time() - meta["t_start"]
    log(f"Done: {len(records)} windows, {total_segments} segments in {elapsed:.0f}s")
    log(f"Output: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio with Whisper")
    parser.add_argument("--input", "-i", required=True, help="Audio file path")
    parser.add_argument("--model", "-m", default="large-v3", help="Whisper model size")
    parser.add_argument("--output", "-o", default="transcript.md", help="Output markdown file")
    parser.add_argument("--language", "-l", default=None,
                        help="Pin the language (e.g. he for Hebrew). Default: auto-detect")
    parser.add_argument("--chunk-seconds", type=float, default=600.0,
                        help="Window length; each window is written as it finishes")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-quiet-split", action="store_true",
                        help="Cut windows at the nominal position instead of the quietest frame")
    parser.add_argument("--no-resume", action="store_true",
                        help="Ignore the .segments.jsonl sidecar and start over")
    parser.add_argument("--max-duration", type=float, default=None,
                        help="Only process the first N seconds (sanity runs)")
    parser.add_argument("--initial-prompt", default=None,
                        help="Text that biases spelling of names and domain terms")
    parser.add_argument("--initial-prompt-file", default=None,
                        help="Read the seed prompt from a file (UTF-8)")
    args = parser.parse_args()

    seed = args.initial_prompt
    if args.initial_prompt_file:
        seed = Path(args.initial_prompt_file).read_text(encoding="utf-8").strip()

    transcribe(
        args.input,
        model_name=args.model,
        output=args.output,
        language=args.language,
        chunk_seconds=args.chunk_seconds,
        quiet_split=not args.no_quiet_split,
        beam_size=args.beam_size,
        resume=not args.no_resume,
        max_duration=args.max_duration,
        initial_prompt=seed,
    )
