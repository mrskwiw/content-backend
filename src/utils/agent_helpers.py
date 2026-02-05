"""Shared utilities for agent operations.

Provides common functions for agent API calls, JSON extraction, and data formatting.
"""

import json
import re
from typing import Any, Optional

from .logger import logger


def extract_json_from_response(response: str, fallback: Optional[Any] = None) -> Any:
    """Extract JSON from Claude API response.

    Handles multiple JSON formats:
    - JSON in code blocks (```json {...} ```)
    - Plain JSON objects/arrays
    - Malformed responses

    Args:
        response: API response text
        fallback: Value to return if extraction fails (default: {})

    Returns:
        Parsed JSON data (dict, list, or fallback value)
    """
    if fallback is None:
        fallback = {}

    try:
        # Try direct JSON parse first
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to extract from code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object or array
    json_match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not extract JSON from response: {response[:100]}...")
    return fallback


def call_claude_api(
    client: Any,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.5,
    extract_json: bool = False,
    fallback_on_error: Optional[Any] = None,
) -> Any:
    """Make a Claude API call with consistent error handling.

    Args:
        client: Anthropic client instance (from get_default_client())
        prompt: User prompt/message
        system_prompt: Optional system prompt
        max_tokens: Max tokens for response
        temperature: Temperature for generation
        extract_json: Whether to extract JSON from response
        fallback_on_error: Value to return on error (default: {} if extract_json, else "")

    Returns:
        API response text or extracted JSON

    Raises:
        Exception: Re-raises exceptions if fallback_on_error is None
    """
    if fallback_on_error is None:
        fallback_on_error = {} if extract_json else ""

    try:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.create_message(**kwargs)

        if extract_json:
            return extract_json_from_response(response, fallback=fallback_on_error)

        return response

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        if fallback_on_error is not None:
            return fallback_on_error
        raise


async def call_claude_api_async(
    client: Any,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.5,
    extract_json: bool = False,
    fallback_on_error: Optional[Any] = None,
) -> Any:
    """Async version of call_claude_api.

    Args:
        client: Async Anthropic client instance
        prompt: User prompt/message
        system_prompt: Optional system prompt
        max_tokens: Max tokens for response
        temperature: Temperature for generation
        extract_json: Whether to extract JSON from response
        fallback_on_error: Value to return on error

    Returns:
        API response text or extracted JSON
    """
    if fallback_on_error is None:
        fallback_on_error = {} if extract_json else ""

    try:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await client.create_message_async(**kwargs)

        if extract_json:
            return extract_json_from_response(response, fallback=fallback_on_error)

        return response

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        if fallback_on_error is not None:
            return fallback_on_error
        raise
