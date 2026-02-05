import os
from dotenv import load_dotenv, set_key

# Load environment variables
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(ENV_PATH)

def save_key(key, value):
    """Save a key-value pair to the .env file."""
    try:
        # Create .env if it doesn't exist
        if not os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'w') as f:
                f.write("")
        
        set_key(ENV_PATH, key, value)
        # Reload environment variables
        load_dotenv(ENV_PATH, override=True)
        return True
    except Exception as e:
        print(f"Error saving key: {e}")
        return False

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek") # openai, deepseek, or gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Stock Configuration
# Format: "symbol" (e.g., "sh600519" for Moutai)
DEFAULT_STOCKS = ["sh600519", "sz000001", "hk00700"]

# Notification Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
