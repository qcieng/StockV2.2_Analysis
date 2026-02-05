
import os
import sys
import pandas as pd
import config
import db_manager
import data_fetcher
import llm_analyzer

# Ensure stdout is flushed
sys.stdout.reconfigure(encoding='utf-8')

# Mock Streamlit session state
class MockSessionState(dict):
    def __init__(self, *args, **kwargs):
        super(MockSessionState, self).__init__(*args, **kwargs)
        self.__dict__ = self

# Ensure DB init
db_manager.init_db()

def test_analysis_flow():
    print("--- Testing Analysis Flow ---", flush=True)
    
    # 1. Check Config
    stocks = config.DEFAULT_STOCKS
    print(f"Stocks to analyze: {stocks}", flush=True)
    if not stocks:
        print("ERROR: No stocks in config.DEFAULT_STOCKS", flush=True)
        return

    # 2. Check API Key
    provider = config.LLM_PROVIDER
    api_key = config.DEEPSEEK_API_KEY if provider == 'deepseek' else config.OPENAI_API_KEY
    print(f"LLM Provider: {provider}", flush=True)
    print(f"API Key present: {'Yes' if api_key else 'No'}", flush=True)
    
    if not api_key:
        print("WARNING: No API Key found in env. Analysis might fail or return error.", flush=True)

    # 3. Simulate Loop
    for symbol in stocks:
        print(f"\nProcessing {symbol}...", flush=True)
        
        # A. Get Name
        try:
            name = data_fetcher.get_stock_name(symbol)
            print(f"Name: {name}", flush=True)
        except Exception as e:
            print(f"Error getting name: {e}", flush=True)
            continue
        
        # B. Get Data
        try:
            df = data_fetcher.get_stock_data(symbol)
            if df is None or df.empty:
                print(f"ERROR: Failed to fetch data for {symbol}", flush=True)
                continue
            print(f"Data fetched: {len(df)} rows. Last date: {df.iloc[-1]['date']}", flush=True)
        except Exception as e:
            print(f"Error getting data: {e}", flush=True)
            continue
        
        # C. Analyze
        try:
            print("Calling analyze_stock...", flush=True)
            key_to_use = api_key if api_key else "dummy_key"
            
            report = llm_analyzer.analyze_stock(
                symbol, df, market_info={}, 
                provider=provider, api_key=key_to_use, stock_name=name
            )
            
            print("Report type:", type(report), flush=True)
            print("Report content sample:", str(report)[:100], flush=True)
            
            if isinstance(report, dict) and "error" in report:
                print(f"Analysis returned error: {report['error']}", flush=True)
            else:
                print("Analysis successful (structure-wise).", flush=True)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRITICAL ERROR in analyze_stock: {e}", flush=True)

if __name__ == "__main__":
    test_analysis_flow()
