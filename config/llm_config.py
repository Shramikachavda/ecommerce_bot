from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

def get_llm():
    """Factory method to initialize and return the LLM instance."""
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY,
        )
    except Exception as e:
        print(f"[LLM INIT ERROR] {str(e)}")
        return None
