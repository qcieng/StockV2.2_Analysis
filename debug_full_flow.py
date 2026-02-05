
import sys
import os

print("DEBUG: Script started", flush=True)

try:
    print("Importing data_fetcher...", flush=True)
    import data_fetcher
    print("Importing llm_analyzer...", flush=True)
    import llm_analyzer
    print("Importing db_manager...", flush=True)
    import db_manager
    print("Importing config...", flush=True)
    import config
    print("DEBUG: Imports successful", flush=True)
except Exception as e:
    print(f"DEBUG: Import failed: {e}", flush=True)
    sys.exit(1)

def test_flow():
    symbol = "sh600519" # Moutai
    print(f"1. Testing Data Fetching for {symbol}...", flush=True)
    
    try:
        df = data_fetcher.get_stock_data(symbol)
        if df is None or df.empty:
            print("❌ Data Fetching Failed: Returned None or Empty", flush=True)
            return
        print(f"✅ Data Fetched: {len(df)} rows. Last date: {df.iloc[-1]['date']}", flush=True)
    except Exception as e:
        print(f"❌ Data Fetching Exception: {e}", flush=True)
        return

    print("2. Testing LLM Analysis...", flush=True)
    
    # Check for keys
    api_key = config.OPENAI_API_KEY
    provider = "openai"
    if not api_key:
        api_key = config.DEEPSEEK_API_KEY
        provider = "deepseek"
    
    if not api_key:
        print("⚠️ No API keys found in config. Attempting to use DB config...", flush=True)
        db_manager.init_db()
        models = db_manager.get_active_models()
        if models:
            provider = models[0]['provider']
            api_key = models[0]['api_key']
            print(f"Found model in DB: {provider}", flush=True)
        else:
            print("❌ No models configured. Cannot test LLM.", flush=True)
            return

    try:
        # We perform the actual analysis call
        print(f"Calling analyze_stock with {provider}...", flush=True)
        result = llm_analyzer.analyze_stock(
            symbol, df, 
            market_info={"sh_index": 3000, "sh_change": 1.5},
            provider=provider,
            api_key=api_key
        )
        
        if "error" in result:
            print(f"❌ LLM Analysis Failed: {result['error']}", flush=True)
        else:
            print("✅ LLM Analysis Successful.", flush=True)
            if "predictions" in result:
                print(f"Predictions: {result['predictions']}", flush=True)
            
            # Check DB
            print("3. Checking Database for Predictions...", flush=True)
            db_manager.init_db()
            conn = db_manager.get_db_connection() # This function might not exist in db_manager, checking imports
            # db_manager code shows it uses sqlite3.connect inside functions, doesn't export get_db_connection usually?
            # Wait, I read db_manager.py and it didn't have get_db_connection exported.
            # I should use sqlite3 directly.
            import sqlite3
            conn = sqlite3.connect("predictions.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE stock_code=? ORDER BY id DESC LIMIT 1", (symbol,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                print(f"✅ Prediction found in DB: ID={row[0]}, Horizon={row[4]}, Pred={row[5]}%", flush=True)
            else:
                print("❌ No prediction found in DB despite successful analysis!", flush=True)
                
    except Exception as e:
        print(f"❌ Analysis Exception: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flow()
