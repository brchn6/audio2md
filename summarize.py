#!/usr/bin/env python3
"""
audio2md — Summarization Module
Reads a transcript (Hebrew/English), translates to English via LLM,
and produces a structured markdown document on a GPU node.
"""
import argparse
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def summarize(transcript_path: str, model_name: str = "Qwen/Qwen2.5-7B-Instruct",
              output: str = "english-summary.md", max_transcript_chars: int = 15000):
    """Read transcript, translate Hebrew→English via LLM, output structured markdown."""
    with open(transcript_path, encoding="utf-8") as f:
        transcript = f.read()

    if len(transcript) > max_transcript_chars:
        transcript = transcript[:max_transcript_chars] + "\n\n[...transcript truncated...]"

    print(f"Loading model: {model_name}", flush=True)
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    print(f"Model loaded in {time.time()-t0:.0f}s on {model.device}", flush=True)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional meeting transcriber. "
                "Read the transcript (mix of Hebrew and English). "
                "Translate ALL Hebrew text to English. "
                "Produce a clean, structured English markdown document."
            ),
        },
        {
            "role": "user",
            "content": (
                "Read this meeting transcript (mix of Hebrew and English), "
                "translate Hebrew→English, and output a markdown document with:\n\n"
                "## Participants\n"
                "## Summary\n"
                "## Key Discussion Points\n"
                "## Decisions Made\n"
                "## Action Items\n"
                "## Full English Transcript\n\n"
                f"Transcript:\n{transcript}"
            ),
        },
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    print(f"Prompt: {len(text)} chars", flush=True)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=8192).to(model.device)
    n_tokens = inputs.input_ids.shape[1]
    print(f"Generating ({n_tokens} input tokens)...", flush=True)

    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.2,
            do_sample=True,
            top_p=0.9,
        )

    response = tokenizer.decode(outputs[0][n_tokens:], skip_special_tokens=True)
    elapsed = time.time() - t0
    print(f"Generated {len(response)} chars in {elapsed:.0f}s", flush=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write("# Meeting Summary (English)\n\n")
        f.write(response.strip())
        f.write("\n")

    print(f"Output: {output}", flush=True)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate transcript and structure as markdown")
    parser.add_argument("--input", "-i", required=True, help="Transcript markdown file")
    parser.add_argument("--model", "-m", default="Qwen/Qwen2.5-7B-Instruct", help="HuggingFace model name")
    parser.add_argument("--output", "-o", default="english-summary.md", help="Output markdown file")
    args = parser.parse_args()

    summarize(args.input, args.model, args.output)
