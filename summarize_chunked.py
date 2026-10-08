#!/usr/bin/env python3
"""
audio2md - Summarization Module (chunked)
Translates a transcript to English and builds a structured markdown report.

Why chunked (2026-10-05): a 77 min conversation is ~80k characters, while the
model context is 8192 tokens. The original single-pass summarize.py truncated
the transcript at 15 000 characters, so it could only ever cover the first
~15 minutes of an hour-long recording. This module processes the transcript in
bounded chunks instead, keeps a JSON state file so an interrupted job resumes,
and rewrites the markdown report after every finished chunk.
"""
import argparse
import json
import re
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Accepts both timestamp spellings seen in this project's transcripts:
#   **[0:05.2]** text      (current transcribe.py)
#   **[12.3s]** text        (older transcribe-whatsapp.sh)
SEG_RE = re.compile(r"^\*\*\[([0-9:.]+)\s*s?\]\*\*\s+(.*)$")
MAX_INPUT_TOKENS = 8192


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_transcript(path):
    """Return [(timestamp, text)] from a transcribe.py markdown transcript."""
    segments = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = SEG_RE.match(line.strip())
        if m:
            segments.append((m.group(1), m.group(2).strip()))
    return segments


def build_chunks(segments, max_chars):
    """Group segments into chunks of at most max_chars, never splitting one."""
    chunks, current, size = [], [], 0
    for ts, text in segments:
        if current and size + len(text) > max_chars:
            chunks.append(current)
            current, size = [], 0
        current.append((ts, text))
        size += len(text) + 1
    if current:
        chunks.append(current)
    return chunks


def load_model(model_name):
    log(f"Loading model: {model_name}")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    kwargs = {"dtype": torch.float16, "device_map": "auto"}
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    except TypeError:  # older transformers spell it torch_dtype
        kwargs["torch_dtype"] = kwargs.pop("dtype")
        model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    model.eval()
    log(f"Model loaded in {time.time() - t0:.0f}s on {model.device}")
    return model, tokenizer


def generate(model, tokenizer, system, user, max_new_tokens):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS
    ).to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.05
        )
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()


TRANSLATION_NORMALIZATIONS = (
    # Source-backed technical terms that the small translator still rendered
    # inconsistently after the glossary pass.
    ("Yumi, sorry B-UDI 1", "B-UDI 1"),
    ("the chromosome on context", "the chromosomal context"),
    ("chromosome on context", "chromosomal context"),
    ("Using the Yumi primer", "Using the Y-UMI primer"),
    ("Yumi8", "Y-UMI 8"),
    ("YUMMI", "Y-UMI"),
    ("Yumi", "Y-UMI"),
    ("Tzviya helps me", "Esther helps me"),
    ("MINID", "mini-D"),
    ("anchorseq", "Anchor-seq"),
    ("first eight clusters are random", "first eight bases are random"),
)


def normalize_translation(text):
    for old, new in TRANSLATION_NORMALIZATIONS:
        text = text.replace(old, new)
    return text


def write_report(out_path, state, meta):
    chunks = state["chunks"]  # list of per-chunk records, already in order
    lines = [
        "# Summary (English)",
        "",
        f"- **Source:** `{meta['source']}`",
        f"- **Model:** {meta['model']}",
        f"- **Segments:** {meta['n_segments']}",
        f"- **Sections done:** {len(chunks)}/{meta['n_chunks']}",
        f"- **Elapsed:** {time.time() - meta['t_start']:.0f}s",
        "",
        "---",
        "",
    ]
    if state.get("global"):
        # The global-summary prompt asks for a '## Summary' heading, and the model
        # emits it. Strip it here so the report does not print it twice.
        body = state["global"].strip()
        if body.startswith("## Summary"):
            body = body[len("## Summary"):].lstrip("\n")
        lines += ["## Summary", "", body, "", "---", ""]

    if state.get("digests"):
        lines += ["## Section Digests", ""]
        for i, rec in enumerate(chunks):
            rng = rec.get("range", "")
            lines.append(f"### Section {i + 1} {rng}")
            lines.append("")
            lines.append(rec.get("digest", "").strip() or "_pending_")
            lines.append("")
        lines += ["---", ""]

    lines += ["## Full English Transcript", ""]
    for i, rec in enumerate(chunks):
        lines.append(f"### Section {i + 1} {rec.get('range', '')}")
        lines.append("")
        lines.append(rec.get("translation", "").strip() or "_pending_")
        lines.append("")

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    tmp.replace(out_path)


def save_state(state_path, state):
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(state_path)


def summarize(transcript_path, model_name="Qwen/Qwen2.5-7B-Instruct",
              output="english-summary.md", max_chars=6000, resume=True,
              glossary=None):
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    state_path = out_path.with_suffix(".summary.json")

    segments = parse_transcript(transcript_path)
    if not segments:
        raise SystemExit(f"No '[timestamp] text' lines found in {transcript_path}")
    chunks = build_chunks(segments, max_chars)
    log(f"Parsed {len(segments)} segments into {len(chunks)} chunks")

    meta = {
        "source": str(transcript_path),
        "model": model_name,
        "n_segments": len(segments),
        "n_chunks": len(chunks),
        "t_start": time.time(),
    }

    state = {"chunks": [], "global": "", "digests": True}
    if resume and state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            log(f"Resuming: {len(state.get('chunks', []))}/{len(chunks)} chunks already done")
        except json.JSONDecodeError:
            log("State file unreadable, starting over")

    model, tokenizer = load_model(model_name)

    translate_system = (
        "You are a professional translator. Translate the Hebrew transcript excerpt "
        "into fluent, natural English. Keep names, product names and technical terms "
        "in English. Output only the translation as flowing paragraphs, with no "
        "commentary, headings or notes."
    )
    if glossary:
        translate_system += (
            "\n\nUse this term map. It overrides your own guess for every term listed; "
            "these are the words that were misheard in the source transcript:\n\n"
            + glossary
        )
        log(f"Glossary attached to the translation prompt: {len(glossary)} chars")
    digest_system = (
        "You summarize meeting and podcast transcripts. Write at most 3 short bullet "
        "points covering the main claims in the excerpt. Output only the bullets."
    )

    for i, chunk in enumerate(chunks):
        if i < len(state["chunks"]):
            continue
        body = "\n".join(text for _, text in chunk)
        rng = f"[{chunk[0][0]} - {chunk[-1][0]}]"

        t0 = time.time()
        translation = generate(model, tokenizer, translate_system, body, 2048)
        translation = normalize_translation(translation)
        t_tr = time.time() - t0

        t0 = time.time()
        digest = generate(model, tokenizer, digest_system, translation, 200)
        log(f"Chunk {i + 1}/{len(chunks)} {rng} chars={len(body)} "
            f"translated in {t_tr:.0f}s, digest {time.time() - t0:.0f}s")

        state["chunks"].append({"range": rng, "translation": translation, "digest": digest})
        save_state(state_path, state)
        write_report(out_path, state, meta)

    if not state.get("global"):
        digests = "\n\n".join(
            f"Section {i + 1} {rec.get('range', '')}:\n{rec.get('digest', '')}"
            for i, rec in enumerate(state["chunks"])
        )
        global_system = (
            "You are a professional editor. You are given the section digests of a "
            "Hebrew-language recording. Write a concise English markdown report "
            "with exactly these sections, in this order: '## Summary' (one paragraph), "
            "'## Key Discussion Points' (bullets), '## Decisions Made' (bullets, or "
            "'None recorded' if there were none), '## Action Items' (bullets, or 'None "
            "recorded' if there were none). Output only the report."
        )
        t0 = time.time()
        state["global"] = generate(model, tokenizer, global_system, digests, 1200)
        log(f"Global summary generated in {time.time() - t0:.0f}s")
        save_state(state_path, state)
        write_report(out_path, state, meta)

    log(f"Done: {len(state['chunks'])} chunks in {time.time() - meta['t_start']:.0f}s")
    log(f"Output: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate and summarize a transcript")
    parser.add_argument("--input", "-i", required=True, help="Transcript markdown file")
    parser.add_argument("--model", "-m", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--output", "-o", default="english-summary.md")
    parser.add_argument("--max-chars", type=int, default=6000, help="Transcript chars per chunk")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--glossary-file", default=None,
                        help="Markdown term map appended to the translation prompt")
    args = parser.parse_args()

    glossary = None
    if args.glossary_file:
        glossary = Path(args.glossary_file).read_text(encoding="utf-8").strip()

    summarize(
        args.input,
        model_name=args.model,
        output=args.output,
        max_chars=args.max_chars,
        resume=not args.no_resume,
        glossary=glossary,
    )
