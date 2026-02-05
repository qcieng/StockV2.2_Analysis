import os
import sys
from dotenv import load_dotenv

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from llm_analyzer import validate_api_key
except ImportError:
    # Fallback if llm_analyzer has dependencies not installed in this context (though they should be)
    print("Error importing llm_analyzer. Ensure requirements are installed.")
    sys.exit(1)

def test_connection():
    load_dotenv()
    
    # Try different key names
    # Prioritize DeepSeek if available
    if os.getenv("DEEPSEEK_API_KEY"):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        provider = "deepseek"
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        provider = "openai" 

    print(f"Testing connection to {base_url}...")
    
    if not api_key:
        print("❌ No API Key found in .env")
        return

    try:
        success, message = validate_api_key(provider, api_key, base_url)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    except Exception as e:
        print(f"❌ Exception during validation: {e}")

if __name__ == "__main__":
    test_connection()
