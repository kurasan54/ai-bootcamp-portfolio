from google import genai
from google.genai import types

import config

client = genai.Client(api_key=config.GEMINI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a database-integrated text processing utility. Analyze the user text data. "
    "You MUST output your response in a strict formatted style containing two sections:\n"
    "1. A bulleted summary synthesized from the reviews.\n"
    "2. A standalone single line stating exactly: 'FINAL_RATING: X' (where X is an integer score from 0 to 10).\n\n"
    "Keep your response analytical and professional."
)


def _classify(rating: int) -> str:
    """Maps a 0-10 numeric rating to a category tier."""
    if 8 <= rating <= 10:
        return "Good"
    elif 4 <= rating <= 7:
        return "Average"
    else:
        return "Bad"


def analyze_review_sentiment(review_content: str):
    
    response = client.models.generate_content(
        model=config.MODEL_NAME,
        contents=review_content,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.1,
        ),
    )

    raw_output = response.text

    # PARSING LOGIC: Extract score metrics from the structural wrapper tag.
    rating = 5  # Safe default fallback score if parsing fails
    clean_summary = raw_output

    if "FINAL_RATING:" in raw_output:
        parts = raw_output.split("FINAL_RATING:")
        clean_summary = parts[0].strip()
        try:
            # Extract trailing numerical characters after the tag.
            digits = "".join(filter(str.isdigit, parts[1]))
            rating = int(digits) if digits else 5
        except ValueError:
            rating = 5

    # Clamp into the valid 0-10 range in case the model returns something odd
    # (e.g. "100" from a stray extra digit).
    rating = max(0, min(10, rating))

    category = _classify(rating)

    return clean_summary, rating, category
