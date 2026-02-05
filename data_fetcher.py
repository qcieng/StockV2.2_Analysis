import yfinance as yf
import pandas as pd
import datetime
import time

def get_stock_data(symbol, period="daily", start_date=None, end_date=None, limit=None):
    """
    Fetch stock data using yfinance.
    Symbol format: sh600519 -> 600519.SS, sz000001 -> 000001.SZ
    """
    max_retries = 3
    retry_delay = 2

    # Map symbol to Yahoo format
    s = symbol.lower()
    yahoo_symbol = s
    if s.startswith('sh') and s[2:].isdigit():
        yahoo_symbol = s[2:] + ".SS"
    elif s.startswith('sz') and s[2:].isdigit():
        yahoo_symbol = s[2:] + ".SZ"
    elif s.startswith('hk') and s[2:].isdigit():
        code_int = int(s[2:])
        yahoo_symbol = f"{code_int:04d}.HK"
    elif s.isdigit():
        if len(s) == 6:
            if s.startswith('6'):
                yahoo_symbol = s + ".SS"
            elif s.startswith('0') or s.startswith('3'):
                yahoo_symbol = s + ".SZ"
        elif len(s) == 5:
            code_int = int(s)
            yahoo_symbol = f"{code_int:04d}.HK"
    
    # Handle period mapping if needed, but 'daily' isn't a yf param. 
    # yf uses 'period' (1d, 5d, 1mo, 1y, max) or start/end.
    # We will use start/end if provided, else period='1y' (defaulting to safe range).
    
    # Calculate start/end if not provided
    if not start_date:
        # Default to 2 years to ensure enough data for indicators
        start_date_obj = datetime.datetime.now() - datetime.timedelta(days=730)
        start_date = start_date_obj.strftime("%Y-%m-%d")
    else:
        # Convert YYYYMMDD to YYYY-MM-DD
        if len(start_date) == 8:
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            
    if not end_date:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    else:
        if len(end_date) == 8:
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                 # Try fetching with period if start/end fails or returns empty (sometimes happens)
                 df = ticker.history(period="1y")

            if df.empty:
                return None

            df = df.reset_index()
            
            df = df.rename(columns={
                'Date': 'date', 'Open': 'open', 'Close': 'close', 
                'High': 'high', 'Low': 'low', 'Volume': 'volume'
            })
            
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            df['pct_change'] = df['close'].pct_change() * 100
            df['pct_change'] = df['pct_change'].fillna(0)
            if limit:
                df = df.tail(limit)

            return df[['date', 'open', 'close', 'high', 'low', 'volume', 'pct_change']]

        except Exception as e:
            print(f"Error fetching data for {symbol} (Attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return None

def get_market_overview():
    try:
        sh_t = yf.Ticker("000001.SS")
        sh_hist = sh_t.history(period="5d")
        sz_t = yf.Ticker("399001.SZ")
        sz_hist = sz_t.history(period="5d")
        result = {}
        if not sh_hist.empty:
            sh_last = sh_hist.iloc[-1]['Close']
            sh_prev = sh_hist.iloc[-2]['Close'] if len(sh_hist) > 1 else sh_last
            result["sh_index"] = round(sh_last, 2)
            result["sh_change"] = round(((sh_last - sh_prev) / sh_prev) * 100, 2)
        if not sz_hist.empty:
            sz_last = sz_hist.iloc[-1]['Close']
            sz_prev = sz_hist.iloc[-2]['Close'] if len(sz_hist) > 1 else sz_last
            result["sz_index"] = round(sz_last, 2)
            result["sz_change"] = round(((sz_last - sz_prev) / sz_prev) * 100, 2)
        if result:
            return result
        return {"error": "No data"}
    except Exception as e:
        return {"error": str(e)}

def get_stock_name(symbol):
    name_map = {
        "sh600519": "贵州茅台",
        "sz000001": "平安银行",
        "hk00700": "腾讯控股",
        "hk09988": "阿里巴巴",
        "sz002594": "比亚迪",
        "sz300750": "宁德时代",
        "sz000858": "五粮液",
    }
    s = symbol.lower()
    return name_map.get(s, symbol)

def search_stock_code(keyword):
    k = str(keyword).strip().lower()
    results = []
    if not k:
        return results
    if k.startswith(("sh", "sz")) and k[2:].isdigit() and len(k[2:]) == 6:
        code = k
        if get_stock_data(code, limit=3) is not None:
            results.append((code, get_stock_name(code)))
        return results
    if k.startswith("hk") and k[2:].isdigit() and len(k[2:]) in (4, 5):
        code = "hk" + k[2:].zfill(5)
        if get_stock_data(code, limit=3) is not None:
            results.append((code, get_stock_name(code)))
        return results
    if k.isdigit():
        if len(k) == 6:
            if k.startswith('6'):
                code = "sh" + k
            else:
                code = "sz" + k
            if get_stock_data(code, limit=3) is not None:
                results.append((code, get_stock_name(code)))
        elif len(k) == 5:
            code = "hk" + k
            if get_stock_data(code, limit=3) is not None:
                results.append((code, get_stock_name(code)))
        return results
    name_to_code = {
        "贵州茅台": "sh600519",
        "茅台": "sh600519",
        "平安银行": "sz000001",
        "腾讯": "hk00700",
        "腾讯控股": "hk00700",
        "阿里": "hk09988",
        "阿里巴巴": "hk09988",
        "比亚迪": "sz002594",
        "宁德时代": "sz300750",
        "五粮液": "sz000858",
    }
    if k in name_to_code:
        code = name_to_code[k]
        if get_stock_data(code, limit=3) is not None:
            results.append((code, get_stock_name(code)))
    return results

if __name__ == "__main__":
    # Test
    print(get_stock_data("sh600519").tail())
    print(get_market_overview())
