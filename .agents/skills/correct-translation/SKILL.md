---
name: correct-translation
description: Use when an audio2md English translation has misheard names, incorrect technical terms, omitted spans, or needs a glossary-backed Stage 2 rerun.
---

# Correct translation

1. Compare the Hebrew transcript, English output, and source audio where a reading is uncertain. Distinguish observations from guesses; do not change biological or sequencing terminology solely on model confidence.
2. Prepare a recording-specific glossary outside tracked source, or update an existing applicable one after verifying terms against the recording. Avoid mappings of common substrings inside other words. Check translation chunk coverage before calling an output complete.
3. Choose a NEW report path so the old report and checkpoint remain for comparison. Run only `summarize_chunked.py` with `--input` pointing at the existing `.transcript.md`, `--output` at the new report path, and `--glossary-file` as appropriate. Use the README's Stage 2 LSF command on a GPU, or direct Python in an existing GPU shell; do not repeat Stage 1 unless the Hebrew transcription itself is wrong.
4. Compare old and new terminology and meaning, inspect each section for omissions, then follow `verify-handoff`. Complete when the corrected report and its limitations are identified without overwriting the original.
