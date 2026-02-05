
import db_manager
import config
import sys

def restore_models():
    print("Checking for models to restore...")
    db_manager.init_db()
    active = db_manager.get_active_models()
    if active:
        print(f"DB already has {len(active)} active models. Skipping restore.")
        return

    print("DB is empty. Checking .env...")
    added = 0
    if config.OPENAI_API_KEY:
        print("Restoring OpenAI...")
        db_manager.add_model_config("openai", config.OPENAI_API_KEY, config.OPENAI_BASE_URL, "gpt-3.5-turbo")
        added += 1
    
    if config.DEEPSEEK_API_KEY:
        print("Restoring DeepSeek...")
        db_manager.add_model_config("deepseek", config.DEEPSEEK_API_KEY, config.DEEPSEEK_BASE_URL, "deepseek-chat")
        added += 1

    if config.GEMINI_API_KEY:
        print("Restoring Gemini...")
        # Gemini usually doesn't need base_url for standard usage but our code supports it
        db_manager.add_model_config("gemini", config.GEMINI_API_KEY, "", "gemini-pro")
        added += 1
        
    if added > 0:
        print(f"Successfully restored {added} models to DB.")
    else:
        print("No keys found in .env.")

if __name__ == "__main__":
    restore_models()
