import json
import re

from google import genai
from google.genai.types import GenerateContentConfig

from app.core.config import settings

PROMPT = """
You are an English lexicography and corpus linguistics expert.
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

### FREQUENCY RULES:
- WORDS: 1–500 (Core 500), 501–1000 (Core 1000), 1001–2000 (Core Plus), 2001–3000 (Active Basic), 3001–5000 (Active Extended), 5001–7000 (Fluent Core), 7001–10000 (Advanced), 10001–15000 (Academic), 15001–25000 (Rare), 25000+ (Obscure).
- PHRASES: 1–500 (Very Common), 501–2000 (Common), 2001–5000 (Less Common), 5001–10000 (Rare), 10000+ (Very Rare).

### RESPONSE FORMAT (JSON only):
{
    "word": "",
    "level": "B2",
    "type": "word | phrase",
    "is_phrasal": true | false,  // Set true only for phrasal verbs like "take off", "get out".
    "is_idiom": true | false,  // Set true for figurative expressions like "break the ice", "piece of cake".
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

Input: "%s"
"""


def get_usage_examples(word: str) -> dict:
    """
    Retrieves usage examples, synonyms, and additional metadata for a given word
    from an external language model API.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    config = GenerateContentConfig(temperature=0.1)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=PROMPT % word.lower(),
        config=config,
    )
    clean_json = re.sub(
        r"^```json\s*|```$", "", response.text.strip(), flags=re.MULTILINE
    )
    data = json.loads(clean_json)

    examples = []
    for meaning in data.get("meanings", []):
        pos = meaning.get("partOfSpeech", "")
        for definition in meaning.get("definitions", []):
            if example := definition.get("example"):
                examples.append(f"({pos}) {example}")

    unique_examples = list(dict.fromkeys(examples))

    synonyms_raw = data.get("synonyms", [])
    if isinstance(synonyms_raw, list) and synonyms_raw:
        synonyms = ", ".join(synonyms_raw)
    else:
        synonyms = "No synonyms found"

    return {
        "rank": int(data.get("rank", 0)),
        "rank_range": str(data.get("rank_range", "-")),
        "translation": data.get("translation", ""),
        "category": data.get("category", "General"),
        "level": data.get("level", "A1"),
        "type": data.get("type", "Unknown"),
        "frequency": int(data.get("frequency", 1)),
        "frequency_group": data.get("frequency_group", "Unknown"),
        "examples": (
            "\n".join(unique_examples)
            if unique_examples
            else "Examples not found"
        ),
        "is_phrasal": bool(data.get("is_phrasal", False)),
        "is_idiom": bool(data.get("is_idiom", False)),
        "synonyms": synonyms,
    }
