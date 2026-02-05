
print("Start", flush=True)
import akshare
print("Imported akshare", flush=True)
import pandas
print("Imported pandas", flush=True)
try:
    import data_fetcher
    print("Imported data_fetcher", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
print("Done", flush=True)
