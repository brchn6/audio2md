#!/usr/bin/env python3
"""
audio2md — Transcription Module
Transcribes audio files using faster-whisper on GPU.
Outputs a timestamped markdown transcript.
"""
import argparse
import time
from pathlib import Path
from faster_whisper import WhisperModel


def transcribe(audio_path: str, model_name: str = "large-v3", output: str = "transcript.md"):
    """Transcribe audio file and write markdown transcript."""
    print(f"Loading Whisper model: {model_name}", flush=True)
    t0 = time.time()
    model = WhisperModel(model_name, device="cuda", compute_type="float16")
    print(f"Model loaded in {time.time()-t0:.0f}s", flush=True)

    print(f"Transcribing: {audio_path}", flush=True)
    t0 = time.time()
    segments, info = model.transcribe(audio_path, beam_size=5)

    seg_list = []
    for seg in segments:
        seg_list.append((seg.start, seg.text.strip()))
        print(f"  [{seg.start:.1f}s] {seg.text.strip()}", flush=True)

    elapsed = time.time() - t0
    duration = info.duration

    with open(output, "w", encoding="utf-8") as f:
        f.write("# Meeting Transcript\n\n")
        f.write(f"- **Language:** {info.language} (confidence: {info.language_probability:.0%})\n")
        f.write(f"- **Duration:** {duration:.0f}s ({duration/60:.1f} min)\n")
        f.write(f"- **Model:** {model_name}\n")
        f.write(f"- **Processing:** {elapsed:.0f}s ({duration/elapsed:.1f}x realtime)\n")
        f.write(f"- **Segments:** {len(seg_list)}\n\n")
        f.write("---\n\n")
        for start, text in seg_list:
            f.write(f"**[{start:.1f}s]** {text}\n\n")
        f.write("---\n")
        f.write(f"*Transcribed by faster-whisper {model_name} on GPU*\n")

    print(f"\nDone: {len(seg_list)} segments in {elapsed:.0f}s", flush=True)
    print(f"Output: {output}", flush=True)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio with Whisper")
    parser.add_argument("--input", "-i", required=True, help="Audio file path")
    parser.add_argument("--model", "-m", default="large-v3", help="Whisper model size")
    parser.add_argument("--output", "-o", default="transcript.md", help="Output markdown file")
    args = parser.parse_args()

    transcribe(args.input, args.model, args.output)
