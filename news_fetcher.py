import akshare as ak
import pandas as pd
import datetime

def get_latest_news(limit=20):
    """
    Fetch latest financial news using AkShare.
    """
    try:
        # Use ak.stock_info_global_cls for Cailian Press news (fast, reliable)
        # Or ak.news_cctv() for CCTV finance
        # Using stock_telegraph_cls as a good real-time source if available, or just general news
        
        # stock_zh_a_news_em - EastMoney news
        news_df = ak.stock_info_global_cls(symbol="A股 24小时")
        
        if news_df is None or news_df.empty:
            return []
            
        # Standardize format: title, content, time
        # news_df columns usually: title, content, public_time
        
        results = []
        for index, row in news_df.head(limit).iterrows():
                    # Combine date and time
                    pub_date = str(row.get("发布日期", ""))
                    pub_time = str(row.get("发布时间", ""))
                    full_time = f"{pub_date} {pub_time}".strip()
                    
                    results.append({
                        "title": row.get("标题", "No Title"),
                        "content": row.get("内容", ""),
                        "time": full_time
                    })
            
        return results
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

if __name__ == "__main__":
    news = get_latest_news(5)
    for n in news:
        print(f"[{n['time']}] {n['title']}")
