"""
One shared place to talk to Ollama, so every feature router (define,
summarize, whatever comes next) calls the same function instead of each
reimplementing its own ollama.chat() call. If you ever swap models, add
retry logic, or add logging/timing across every AI-backed endpoint, this is
the one file that needs to change.
"""
import ollama

DEFAULT_MODEL = "llama3.1:8b"


def run_prompt(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send one prompt to a local Ollama model and return its text reply.

    Raises whatever ollama.chat() raises (e.g. if Ollama isn't running or the
    model isn't pulled) -- callers (the routers) are responsible for turning
    that into an HTTP error response.
    """
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]
