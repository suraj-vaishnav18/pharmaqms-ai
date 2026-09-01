"""
Thin wrapper around the Groq client so the rest of the pipeline
doesn't need to know which model/provider is being used.
"""
import json
from groq import Groq

from app.config import settings

_client = Groq(api_key=settings.groq_api_key)


def call_fast_model(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Use gemma2-9b-it: cheap/fast, good for classification-style tasks."""
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client.chat.completions.create(
        model=settings.groq_fast_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        **kwargs,
    )
    return resp.choices[0].message.content


def call_reasoning_model(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Use llama-3.3-70b-versatile: for root cause / CAPA reasoning, more context."""
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client.chat.completions.create(
        model=settings.groq_reasoning_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        **kwargs,
    )
    return resp.choices[0].message.content


def safe_json_parse(text: str, fallback: dict) -> dict:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return fallback
