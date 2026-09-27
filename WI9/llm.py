import ollama

DEFAULT_MODEL = "llama3.1:8b"  # whichever model you settled on testing


def run_prompt(prompt: str, model: str = DEFAULT_MODEL) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]

    raise NotImplementedError
