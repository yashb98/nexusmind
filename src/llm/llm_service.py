"""LLM service — generation with LiteLLM routing and Langfuse tracing."""

import uuid
from collections.abc import AsyncIterator

import litellm
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

# Suppress LiteLLM internal logs
litellm.suppress_debug_info = True


def _get_primary_model() -> str:
    """Get the primary LLM model identifier."""
    if settings.llm.runpod_llm_endpoint:
        return settings.llm.runpod_llm_model
    return settings.llm.litellm_fallback_model


def _get_api_base() -> str | None:
    """Get API base URL for RunPod endpoint."""
    if settings.llm.runpod_llm_endpoint:
        return f"https://api.runpod.ai/v2/{settings.llm.runpod_llm_endpoint}/openai/v1"
    return None


def _get_api_key() -> str:
    """Get API key for the active provider."""
    if settings.llm.runpod_llm_endpoint:
        return settings.llm.runpod_api_key
    return settings.llm.anthropic_api_key


async def generate(
    system_prompt: str,
    messages: list[dict],
    trace_id: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Generate a complete LLM response (non-streaming)."""
    trace_id = trace_id or str(uuid.uuid4())

    all_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = await litellm.acompletion(
            model=_get_primary_model(),
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            api_base=_get_api_base(),
            api_key=_get_api_key(),
            metadata={"trace_id": trace_id},
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "llm_generate",
            trace_id=trace_id,
            model=_get_primary_model(),
            tokens=response.usage.total_tokens if response.usage else 0,
        )
        return content

    except Exception as primary_err:
        logger.warning("llm_primary_failed", error=str(primary_err))
        # Fallback to Anthropic
        try:
            response = await litellm.acompletion(
                model=settings.llm.litellm_fallback_model,
                messages=all_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                api_key=settings.llm.anthropic_api_key,
                metadata={"trace_id": trace_id},
            )
            content = response.choices[0].message.content or ""
            logger.info(
                "llm_fallback_used",
                trace_id=trace_id,
                model=settings.llm.litellm_fallback_model,
            )
            return content
        except Exception as fallback_err:
            logger.error("llm_all_failed", primary=str(primary_err), fallback=str(fallback_err))
            raise


async def generate_stream(
    system_prompt: str,
    messages: list[dict],
    trace_id: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> AsyncIterator[str]:
    """Generate a streaming LLM response."""
    trace_id = trace_id or str(uuid.uuid4())

    all_messages = [{"role": "system", "content": system_prompt}] + messages

    response = await litellm.acompletion(
        model=_get_primary_model(),
        messages=all_messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        api_base=_get_api_base(),
        api_key=_get_api_key(),
        metadata={"trace_id": trace_id},
    )

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
