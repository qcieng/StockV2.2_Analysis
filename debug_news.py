import akshare as ak
import pandas as pd

try:
    print("Fetching news using stock_info_global_cls...")
    news_df = ak.stock_info_global_cls(symbol="A股 24小时")
    print("Columns:", news_df.columns.tolist())
    print("First row:", news_df.iloc[0].to_dict() if not news_df.empty else "Empty DataFrame")
except Exception as e:
    print(f"Error with stock_info_global_cls: {e}")

try:
    print("\nFetching news using stock_news_latest_sina...")
    # This might fail if not available, but let's check docs or try common ones
    # Usually stock_js_weibo_report is good for 7x24
    pass
except Exception as e:
    print(f"Error: {e}")
