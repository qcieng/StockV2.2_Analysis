
import yfinance as yf
print("Imported yfinance", flush=True)

try:
    # 600519.SS is Moutai
    ticker = yf.Ticker("600519.SS")
    print("Fetching history...", flush=True)
    hist = ticker.history(period="1mo")
    print(hist.head(), flush=True)
    if not hist.empty:
        print("Success", flush=True)
    else:
        print("Empty", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
