"""
Minimal proof-of-concept: send text to one or more local Ollama models and
print back a summary + how long each took. Not the real pipeline -- just
enough to prove the Ollama -> Python integration works before building
the actual scaffolding (routing, error handling, etc.) around it.

Prereqs:
    - Ollama installed and running (the Ollama app/service, not just this script)
    - Models pulled first, e.g.: ollama pull llama3.1:8b
    - pip install ollama

Usage:
    python summarize_poc.py --models llama3.1:8b qwen2.5:14b --text-file note.txt
    python summarize_poc.py --models llama3.1:8b --text "some raw text here"
"""
import argparse
import time
from pathlib import Path

import ollama

PROMPT_TEMPLATE = (
    "Summarize the following text in 2-3 sentences, capturing the main points. "
    "Do not add information that isn't in the text.\n\n{text}"
)


def summarize(model: str, text: str) -> tuple[str, float]:
    start = time.perf_counter()
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(text=text)}],
    )
    elapsed = time.perf_counter() - start
    return response["message"]["content"], elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", default=["llama3.1:8b"],
        help="Ollama model tags to test, space-separated (must already be pulled)",
    )
    parser.add_argument("--text-file", type=Path, help="Path to a text file to summarize")
    parser.add_argument("--text", type=str, help="Inline text to summarize instead of a file")
    args = parser.parse_args()

    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        parser.error("Provide either --text-file or --text")

    for model in args.models:
        print(f"\n=== {model} ===")
        try:
            summary, elapsed = summarize(model, text)
        except Exception as exc:
            print(f"FAILED: {exc}")
            print("(Is Ollama running? Is this model pulled? `ollama list` to check.)")
            continue
        print(f"time: {elapsed:.2f}s")
        print(f"summary: {summary}")


if __name__ == "__main__":
    main()
