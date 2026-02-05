
import db_manager
import config

db_manager.init_db()
models = db_manager.get_active_models()
print("Active Models:", flush=True)
for m in models:
    print(m, flush=True)

print("\nEnv Config:", flush=True)
print(f"OPENAI_API_KEY: {config.OPENAI_API_KEY[:5]}...", flush=True)
print(f"DEEPSEEK_API_KEY: {config.DEEPSEEK_API_KEY[:5]}...", flush=True)
