import os
import sys

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
DB_NAME = os.getenv("DB_NAME", "review_history.db")

def _validate_config() -> None:
    if GEMINI_API_KEY is None or GEMINI_API_KEY.strip() == "":
        sys.stderr.write(
            "[config.py] FATAL: GEMINI_API_KEY is not set. "
            "Please define it in your .env file. Halting.\n"
        )
        sys.exit(1)

    if MODEL_NAME is None:
        sys.stderr.write(
            "[config.py] WARNING: MODEL_NAME is not set. "
            "Falling back to None; downstream calls may fail.\n"
        )
    if DB_NAME is None:
        sys.stderr.write(
            "[config.py] WARNING: DB_NAME is not set. "
            "Falling back to None; downstream calls may fail.\n"
        )


_validate_config()


if __name__ == "__main__":
    # Quick manual check: `python config.py`
    print(f"GEMINI_API_KEY: {'*' * len(GEMINI_API_KEY)} (loaded)")
    print(f"MODEL_NAME:     {MODEL_NAME}")
    print(f"DB_NAME:        {DB_NAME}")
