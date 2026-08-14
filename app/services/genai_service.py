import json
import logging
import random
import re
import time
from functools import lru_cache

from fastapi import HTTPException
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.llm import LlmResponse
from app.schemas.word import WordInfo


SYSTEM_PROMPT = """You are an English lexicography and corpus linguistics expert.
I am learning English words and phrases. Provide usage examples, translations, and linguistic data.

### REFERENCE EXAMPLES FOR STABILITY:
- "House" (Word) → Level: A1, Rank: 150, Group: Core 500, Range: 1-500
- "Challenge" (Word) → Level: B1, Rank: 1200, Group: Core Plus, Range: 1001-2000
- "Inevitable" (Word) → Level: B2, Rank: 4500, Group: Active Extended, Range: 3001-5000
- "Pragmatic" (Word) → Level: C1, Rank: 8500, Group: Advanced, Range: 7001-10000
- "Take care" (Phrase) → Level: A1, Rank: 300, Group: Very Common, Range: 1-500
- "Once in a blue moon" (Phrase) → Level: C1, Rank: 12000, Group: Very Rare, Range: 10000+

### INSTRUCTIONS:
1. Provide "level" strictly as a single value (A1, A2, B1, B2, C1, or C2).
2. Provide "rank" as a realistic estimated frequency number. Be consistent with the Reference Examples above.
3. For "synonyms":
   - Return them as a LIST of strings.
   - For words: provide 3-5 single-word synonyms.
   - For phrases: provide 2-3 alternative phrases.
4. "translation": Ukrainian language, comma-separated if multiple.
5. "category": Choose from [Phrases, Verbs, Nouns, Adverbs, Adjectives, Idioms]. Use "General" if no match.
6. "is_phrasal" is used ONLY for phrasal verbs without additional context:
    - is_phrasal = true:
        - take off
        - pick up
        - look forward to
        - put up with
    - is_phrasal = false
        - look forward to seeing you soon
        - take off your clothes

### FREQUENCY RULES:
- WORDS: 1–500 (Core 500), 501–1000 (Core 1000), 1001–2000 (Core Plus), 2001–3000 (Active Basic), 3001–5000 (Active Extended), 5001–7000 (Fluent Core), 7001–10000 (Advanced), 10001–15000 (Academic), 15001–25000 (Rare), 25000+ (Obscure).
- PHRASES: 1–500 (Very Common), 501–2000 (Common), 2001–5000 (Less Common), 5001–10000 (Rare), 10000+ (Very Rare).

### RESPONSE FORMAT (JSON only):
{
    "word": "",
    "level": "B2",
    "type": "word | phrase",
    "is_phrasal": true | false,
    "is_idiom": true | false,
    "frequency": 1-10,
    "rank": 1234,
    "rank_range": "1001-2000",
    "frequency_group": "...",
    "translation": "",
    "category": "",
    "synonyms": ["syn1", "syn2", "syn3"],
    "meanings": [
        {
            "partOfSpeech": "",
            "definitions": [{"definition": "", "example": ""}]
        }
    ]
}
"""

USER_TEMPLATE = "Input: %s"

TEMPERATURE = 0.1
MAX_TOKENS = 4000
BACKOFF_BASE_SECONDS = 0.5

logger = logging.getLogger(__name__)

# Retrying these cannot change the outcome: the credentials are refused or
# the request itself is malformed. Retrying spent the whole budget across
# every model, on every word added, and buried the one error worth reading.
FATAL_ERRORS = (AuthenticationError, PermissionDeniedError, BadRequestError)

# Fatal for this model only. Another one in the list may well exist.
MODEL_ERRORS = (NotFoundError,)

# Worth another attempt. The parsing errors belong here because the model
# can return valid JSON on a second try.
RETRYABLE_ERRORS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
    json.JSONDecodeError,
    ValidationError,
    APIError,
)


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Build the client once.

    A client per request throws away its connection pool, so every word paid
    for a fresh TLS handshake.
    """
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        timeout=float(settings.OPENROUTER_TIMEOUT_SECONDS),
        max_retries=0,
    )


def _sleep_with_backoff(attempt: int) -> None:
    delay = BACKOFF_BASE_SECONDS * (2**attempt)
    jitter = random.uniform(0, BACKOFF_BASE_SECONDS)
    time.sleep(delay + jitter)


def _strip_code_fences(content: str | None) -> str:
    return re.sub(r"^```json\s*|```$", "", (content or "").strip(), flags=re.MULTILINE)


def _extract_json(content: str | None) -> dict:
    cleaned = _strip_code_fences(content=content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


def _build_examples(response: LlmResponse) -> str:
    examples: list[str] = []
    for meaning in response.meanings:
        pos = meaning.partOfSpeech or ""
        for definition in meaning.definitions:
            if definition.example:
                if pos:
                    examples.append(f"({pos}) {definition.example}")
                else:
                    examples.append(definition.example)

    unique_examples = list(dict.fromkeys(examples))
    return "\n".join(unique_examples) if unique_examples else "Examples not found"


def _format_synonyms(response: LlmResponse) -> str:
    if response.synonyms:
        return ", ".join(response.synonyms)
    return "No synonyms found"


def _parse_response(content: str) -> LlmResponse:
    data = _extract_json(content=content)
    return LlmResponse.model_validate(data)


def _build_models() -> list[str]:
    models = [settings.OPENROUTER_MODEL]
    for model in settings.OPENROUTER_FALLBACK_MODELS:
        if model not in models:
            models.append(model)
    return models


def get_usage_examples(word: str) -> WordInfo:
    """
    Retrieves usage examples, synonyms, and additional metadata for a given word
    from an external language model API via OpenRouter.
    """
    client = _get_client()

    prompt = USER_TEMPLATE % word.lower()

    # _build_models already removes duplicates, so this list needs no guard.
    models = _build_models()
    attempted_models: list[str] = []
    retry_count = settings.OPENROUTER_MAX_RETRIES

    for model in models:
        attempted_models.append(model)
        for attempt in range(retry_count + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
                content = response.choices[0].message.content or ""
                parsed = _parse_response(content=content)
                return WordInfo(
                    word=parsed.word,
                    rank=parsed.rank,
                    rank_range=parsed.rank_range,
                    translation=parsed.translation,
                    category=parsed.category,
                    level=parsed.level,
                    type=parsed.type,
                    frequency=parsed.frequency,
                    frequency_group=parsed.frequency_group,
                    examples=_build_examples(response=parsed),
                    is_phrasal=parsed.is_phrasal,
                    is_idiom=parsed.is_idiom,
                    synonyms=_format_synonyms(response=parsed),
                )
            except FATAL_ERRORS as exc:
                logger.error("LLM rejected the request, not retrying: %s", exc)
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "LLM rejected the request. Check OPENROUTER_API_KEY "
                        "and the configured model."
                    ),
                ) from exc
            except MODEL_ERRORS as exc:
                logger.warning(
                    "Model %s is unavailable, trying the next: %s", model, exc
                )
                break
            except RETRYABLE_ERRORS as exc:
                error_message = f"{model} attempt {attempt + 1}: {exc}"
                logger.warning("LLM request failed: %s", error_message)
                if attempt < retry_count:
                    _sleep_with_backoff(attempt)
                else:
                    logger.warning("Retry budget exhausted for model %s", model)

    models_tried = ", ".join(attempted_models) or "none"
    raise HTTPException(
        status_code=502,
        detail=f"LLM request failed after retries. Models tried: {models_tried}",
    )
