"""Tests for the AIService caching layer (Redis-backed).

Pins two things that used to be wrong: the cache key ignored the context
sentence (the prompt explicitly asks for a context-specific definition), and
the TTL was the helper default (1h) while the docstring promised 7 days.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai_service import AIService

_PAYLOAD = (
    '{"definition":"cached-def","translation":"cached-trans","part_of_speech":"noun",'
    '"ipa":"/wɜːrd/","example_sentences":["ex1"],"collocations":["col1"],"difficulty_level":"B1"}'
)


@pytest.mark.asyncio
async def test_enrich_caches_result_and_skips_llm_for_same_context(fake_redis):
    """Same word + same context: the second call is served from cache."""
    service = AIService()

    chat_mock = AsyncMock(return_value=_PAYLOAD)
    with patch.object(service, "_chat", new=chat_mock):
        result1 = await service.enrich_vocabulary_word("hello", "hello world")

    assert result1["definition"] == "cached-def"
    assert chat_mock.call_count == 1
    keys = [k for k in fake_redis._store if k.startswith("ai_cache:")]
    assert len(keys) == 1

    # The cache entry must live for 7 days, not the 1h helper default. The
    # deadline is computed from the fake clock, so allow for float rounding at
    # the exact boundary instead of asserting on the float value.
    ttl = fake_redis._expires[keys[0]] - time.monotonic()
    assert 6 * 86400 < ttl <= 7 * 86400 + 1

    chat_mock2 = AsyncMock()
    with patch.object(service, "_chat", new=chat_mock2):
        result2 = await service.enrich_vocabulary_word("hello", "hello world")

    assert chat_mock2.call_count == 0
    assert result2 == result1


@pytest.mark.asyncio
async def test_enrich_does_not_share_cache_across_contexts(fake_redis):
    """The same word in a different sentence gets its own LLM answer/cache key."""
    service = AIService()

    first = AsyncMock(return_value='{"definition":"sense-a","translation":"A"}')
    with patch.object(service, "_chat", new=first):
        result_a = await service.enrich_vocabulary_word("bank", "river bank")

    second = AsyncMock(return_value='{"definition":"sense-b","translation":"B"}')
    with patch.object(service, "_chat", new=second):
        result_b = await service.enrich_vocabulary_word("bank", "bank account")

    assert first.call_count == 1
    assert second.call_count == 1
    assert result_a["definition"] == "sense-a"
    assert result_b["definition"] == "sense-b"
    assert len([k for k in fake_redis._store if k.startswith("ai_cache:")]) == 2


@pytest.mark.asyncio
async def test_enrich_raises_when_llm_fails(fake_redis):
    """If the LLM raises, enrich propagates AIServiceError instead of silently
    persisting an empty-default dict (the old behavior masked real failures)."""
    from app.services.ai_service import AIServiceError

    service = AIService()

    with patch.object(service, "_chat", new=AsyncMock(side_effect=AIServiceError("boom"))):
        with pytest.raises(AIServiceError):
            await service.enrich_vocabulary_word("brokenword")
