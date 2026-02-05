
import db_manager
import data_fetcher
import llm_analyzer
import config
import sys

def log(msg):
    with open("backend.log", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg)

def verify_backend():
    with open("backend.log", "w", encoding="utf-8") as f:
        f.write("Starting Verification...\n")

    log("--- 1. Checking Database ---")
    try:
        db_manager.init_db()
        models = db_manager.get_active_models()
        log(f"Active models: {len(models)}")
        for m in models:
            log(f" - {m['provider']} ({m['model_name']})")
    except Exception as e:
        log(f"DB Error: {e}")
        return

    log("\n--- 2. Checking Data Fetcher ---")
    stock = "sh600519" # Moutai
    try:
        df = data_fetcher.get_stock_data(stock)
        if df is not None and not df.empty:
            log(f"Successfully fetched data for {stock}: {len(df)} rows")
            log(str(df.tail(1)))
        else:
            log(f"Failed to fetch data for {stock}")
            return
    except Exception as e:
        log(f"Data Fetcher Error: {e}")
        return

    log("\n--- 3. Checking LLM Analysis (Dry Run) ---")
    if not models:
        log("No active models in DB. Checking .env fallback...")
        if config.OPENAI_API_KEY:
            log("Found OpenAI Key in .env")
            models.append({"provider": "openai", "api_key": config.OPENAI_API_KEY, "base_url": config.OPENAI_BASE_URL, "model_name": "gpt-3.5-turbo"})
        elif config.DEEPSEEK_API_KEY:
            log("Found DeepSeek Key in .env")
            models.append({"provider": "deepseek", "api_key": config.DEEPSEEK_API_KEY, "base_url": config.DEEPSEEK_BASE_URL, "model_name": "deepseek-chat"})
    
    if not models:
        log("No models available for analysis.")
        return

    # Use first model
    model = models[0]
    log(f"Testing analysis with {model['provider']}...")
    try:
        # We use a mocked prompt or just run it?
        # Let's run it for real to verify the "Start Analysis" issue.
        result = llm_analyzer.analyze_stock(
            stock, df, market_info={"sh_index": "3000"}, 
            provider=model['provider'], 
            api_key=model['api_key'], 
            base_url=model.get('base_url'),
            model_name=model.get('model_name')
        )
        log(f"Analysis Result Keys: {result.keys()}")
        if "error" in result:
            log(f"Analysis Error: {result['error']}")
        else:
            log("Analysis Success!")
            # log(str(result)[:200] + "...")
    except Exception as e:
        log(f"Analysis Exception: {e}")

if __name__ == "__main__":
    verify_backend()
