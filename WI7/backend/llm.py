"""
One shared place to talk to Ollama. Every feature router (define,
summarize, whatever comes next) should call a function from this file
instead of each writing its own ollama.chat() call -- that way if you ever
swap the default model, add retries, or add logging/timing, there's exactly
one place to change it.

Goal for this file:
    - One function that takes a finished prompt string (and optionally a
      model name) and returns the model's reply text.
"""

# TODO: import ollama

DEFAULT_MODEL = "llama3.1:8b"  # whichever model you settled on testing


def run_prompt(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send `prompt` to `model` via Ollama and return the reply text.

    Hints:
    - ollama.chat() takes model= and messages= (a list of
      {"role": ..., "content": ...} dicts -- one message with role "user"
      is all this needs).
    - The reply is nested; the text you want is at
      response["message"]["content"].
    - Let exceptions from ollama.chat() propagate up out of this function
      (don't catch them here). The router calling this is the better place
      to decide what HTTP status a failure should map to -- this function
      shouldn't know or care that it's being called from an API.
    """
    # TODO: implement and return the reply text
    raise NotImplementedError
