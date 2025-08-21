import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Firebase
    FIREBASE_KEY_PATH: str = os.getenv("FIREBASE_KEY_PATH")
    
# Create a singleton instance
settings = Settings()
