"""Configuration settings for gtts."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Google API
    google_api_key: str = ""

    # TTS Model settings
    tts_model: str = "gemini-2.5-flash-preview-tts"
    default_voice: str = "Kore"

    # Audio settings
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2  # 16-bit

    # Output settings
    output_dir: Path = Path("output")

    # Text chunking (to stay under context limit)
    max_chunk_chars: int = 20000  # ~5000 tokens, well under 32k limit

    # Google OAuth settings (for Google Docs access)
    google_credentials_path: Path = Path("google_credentials.json")
    google_token_path: Path = Path("google_token.json")

    model_config = {"env_prefix": "", "extra": "ignore"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Try alternate env var names
        if not self.google_api_key:
            self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        if not self.google_api_key:
            self.google_api_key = os.getenv("GEMINI_KEY", "")


# Available voices from Gemini TTS
AVAILABLE_VOICES = [
    "Zephyr",
    "Puck",
    "Charon",
    "Kore",
    "Fenrir",
    "Leda",
    "Orus",
    "Aoede",
    "Callirrhoe",
    "Autonoe",
    "Enceladus",
    "Iapetus",
    "Umbriel",
    "Algieba",
    "Despina",
    "Erinome",
    "Algenib",
    "Rasalgethi",
    "Laomedeia",
    "Achernar",
    "Alnilam",
    "Schedar",
    "Gacrux",
    "Pulcherrima",
    "Achird",
    "Zubenelgenubi",
    "Vindemiatrix",
    "Sadachbia",
    "Sadaltager",
    "Sulafat",
]

settings = Settings()
