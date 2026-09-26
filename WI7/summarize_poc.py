"""
Minimal proof-of-concept: send text to one or more local Ollama models and
print back a summary. Not the real pipeline -- just
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
from email.mime import text
import random
from pathlib import Path

import ollama

PROMPT_TEMPLATE = (
    "You will either be given a word to define, or a short paragraph to summarize. If it is a word, provide a concise definition. If it is a paragraph, provide a brief summary."
    "Words: {text}"
)

def summarize(model: str, text: str) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(text=text)}],
    )
    return response["message"]["content"]


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

    lines = [
        (line_number, line)
        for line_number, line in enumerate(text.splitlines(), start=1)
        if line.strip()
    ]
    if len(lines) < 5:
        parser.error("The supplied text must contain at least five non-empty lines")

    required_lines = [entry for entry in lines if 20 <= entry[0] <= 23]
    if not required_lines:
        parser.error("The supplied text must contain a line between 20 and 23")

    selected_lines = [random.choice(required_lines)]
    remaining_lines = [entry for entry in lines if entry not in selected_lines]
    selected_lines.extend(random.sample(remaining_lines, 4))
    random.shuffle(selected_lines)

    for line_number, line in selected_lines:
        print(f"\n=== line {line_number}/{len(lines)} ===")
        for model in args.models:
            print(f"\n--- model {model} ---")
            try:
                summary = summarize(model, line)
            except Exception as exc:
                print(f"FAILED: {exc}")
                print("(Is Ollama running? Is this model pulled? `ollama list` to check.)")
                continue
            print(f"summary: {summary}")


if __name__ == "__main__":
    main()
