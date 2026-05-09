"""
sovereign/llm.py

Thin wrapper around the OpenAI SDK that always routes requests to
the Sovereign Core vLLM endpoint (default localhost:8001/v1).

Usage
-----
    from sovereign.llm import complete, complete_stream, create_client

    client, model = create_client()
    response = complete(client, model, messages=[...])
"""
from __future__ import annotations

import json
from typing import Generator, Iterator, List, Optional

import backoff
import openai

from sovereign.config import (
    MAX_TOKENS,
    SOVEREIGN_API_BASE,
    SOVEREIGN_API_KEY,
    SOVEREIGN_MODEL,
    TEMPERATURE,
    TOP_P,
)


def create_client(
    model: Optional[str] = None,
    api_base: Optional[str] = None,
) -> tuple[openai.OpenAI, str]:
    """
    Create an OpenAI-compatible client pointing at the Sovereign Core endpoint.

    Returns:
        (client, resolved_model_name)
    """
    resolved_model = model or SOVEREIGN_MODEL
    resolved_base = api_base or SOVEREIGN_API_BASE
    client = openai.OpenAI(
        base_url=resolved_base,
        api_key=SOVEREIGN_API_KEY,
        timeout=120.0,
    )
    return client, resolved_model


@backoff.on_exception(
    backoff.expo,
    (openai.RateLimitError, openai.APITimeoutError),
    max_time=180,
    max_value=30,
)
def complete(
    client: openai.OpenAI,
    model: str,
    messages: List[dict],
    temperature: float = TEMPERATURE,
    top_p: float = TOP_P,
    max_tokens: int = MAX_TOKENS,
    tools: Optional[List[dict]] = None,
    tool_choice: Optional[str] = None,
    n: int = 1,
) -> openai.types.chat.ChatCompletion:
    """Single non-streaming completion via the Sovereign Core endpoint."""
    kwargs: dict = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=n,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice or "auto"
    return client.chat.completions.create(**kwargs)


def complete_text(
    client: openai.OpenAI,
    model: str,
    messages: List[dict],
    **kwargs,
) -> str:
    """Convenience wrapper — returns the first choice's text directly."""
    response = complete(client, model, messages, **kwargs)
    return response.choices[0].message.content or ""


def complete_stream(
    client: openai.OpenAI,
    model: str,
    messages: List[dict],
    temperature: float = TEMPERATURE,
    top_p: float = TOP_P,
    max_tokens: int = MAX_TOKENS,
) -> Generator[str, None, None]:
    """Token-by-token streaming generator."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
