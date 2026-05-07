import yfinance as yf
import akshare as ak
import pandas as pd
import datetime
import time
import requests

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
    elif s.isalpha(): # US Stocks (AAPL, MSFT, etc.)
        yahoo_symbol = s.upper()
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
            # 1) Try yfinance
            ticker = yf.Ticker(yahoo_symbol)
            # Use period instead of start/end if start/end is not explicitly provided by caller
            # as period is often more robust for Yahoo Finance API
            if not start_date and not end_date:
                df = ticker.history(period="2y")
            else:
                df = ticker.history(start=start_date, end=end_date)
            
            if df is None or df.empty:
                 df = ticker.history(period="1y")

            if df.empty and s.startswith(('sh', 'sz')) or (s.isdigit() and len(s) == 6):
                # 2) Fallback to AkShare for A-shares
                try:
                    # Map sh600519 to 600519
                    ak_code = s[2:] if s.startswith(('sh', 'sz')) else s
                    # AkShare daily data
                    df_ak = ak.stock_zh_a_hist(symbol=ak_code, period="daily", start_date=start_date.replace('-', ''), end_date=end_date.replace('-', ''), adjust="qfq")
                    if not df_ak.empty:
                        df_ak = df_ak.rename(columns={
                            '日期': 'date', '开盘': 'open', '收盘': 'close', 
                            '最高': 'high', '最低': 'low', '成交量': 'volume'
                        })
                        df = df_ak
                except Exception as ak_e:
                    print(f"AkShare fallback failed: {ak_e}")

            if df.empty:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None

            if 'date' not in df.columns:
                df = df.reset_index()
            
            # Normalize column names
            col_map = {
                'Date': 'date', 'Open': 'open', 'Close': 'close', 
                'High': 'high', 'Low': 'low', 'Volume': 'volume',
                '日期': 'date', '开盘': 'open', '收盘': 'close', 
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            }
            df = df.rename(columns=col_map)
            
            # Convert date to string
            if not pd.api.types.is_string_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
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
    """
    Prefer real-time index from public sources; fallback to yfinance.
    """
    # Try Sina real-time (no cookies needed)
    try:
        sh = _fetch_sina_quote('s_sh000001')
        sz = _fetch_sina_quote('s_sz399001')
        result = {}
        if sh:
            result["sh_index"] = sh.get("price")
            result["sh_change"] = sh.get("pct_change")
            result["sh_time"] = sh.get("time")
            result["sh_source"] = "sina"
        if sz:
            result["sz_index"] = sz.get("price")
            result["sz_change"] = sz.get("pct_change")
            result["sz_time"] = sz.get("time")
            result["sz_source"] = "sina"
        if result:
            return result
    except Exception:
        pass
    # Fallback to yfinance (may be delayed)
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

def get_realtime_quote(symbol):
    """
    Get realtime quote for given symbol using multiple sources (prefer Xueqiu, fallback to Sina/Tencent).
    Returns dict: {price, pct_change, time, source}
    """
    s = symbol.lower()
    # Normalize codes
    if s.startswith('sh') or s.startswith('sz'):
        xq_symbol = s[:2].upper() + s[2:]
        sina_symbol = s
        tencent_symbol = s
    elif s.startswith('hk'):
        xq_symbol = s[:2].upper() + s[2:]
        sina_symbol = None
        tencent_symbol = s
    elif s.isalpha(): # US Stocks
        xq_symbol = s.upper()
        sina_symbol = "gb_" + s # Sina US stock prefix is gb_
        tencent_symbol = "us" + s.upper() # Tencent US stock prefix is us
    else:
        xq_symbol = None
        sina_symbol = s
        tencent_symbol = s
    # 1) Try Xueqiu
    if xq_symbol:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://xueqiu.com/hq",
                "Accept": "application/json",
            }
            url = f"https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol={xq_symbol}"
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                j = r.json()
                items = j.get("data", {}).get("items", [])
                if items:
                    it = items[0]
                    price = round(it.get("current", 0.0), 4)
                    pct = round(it.get("percent", 0.0), 4)
                    ts = it.get("time", 0)
                    # Xueqiu time is ms epoch
                    dt = datetime.datetime.fromtimestamp(ts / 1000)
                    # Xueqiu returns "current" as current price
                    high = round(it.get("high", 0.0), 4)
                    low = round(it.get("low", 0.0), 4)
                    return {
                        "price": price, 
                        "pct_change": pct, 
                        "time": dt.strftime("%Y-%m-%d %H:%M:%S"), 
                        "source": "xueqiu",
                        "high": high,
                        "low": low
                    }
        except Exception:
            pass
    # 2) Try Sina
    if sina_symbol:
        sina_data = _fetch_sina_quote(sina_symbol)
        if sina_data:
            sina_data["source"] = "sina"
            return sina_data
    # 3) Try Tencent
    if tencent_symbol:
        tqq = _fetch_tencent_quote(tencent_symbol)
        if tqq:
            tqq["source"] = "tencent"
            return tqq
    return None

def _fetch_sina_quote(symbol):
    """
    Fetch realtime from Sina. 
    For stocks use 'sh600519', for index use 's_sh000001' or 's_sz399001'.
    """
    try:
        url = f"http://hq.sinajs.cn/list={symbol}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        txt = r.text
        # Example: var hq_str_sh600519="贵州茅台,1805.000,1806.000,1825.000,1830.000,1790.000,....,2026-02-05,15:00:03,00";
        if "=" not in txt:
            return None
        data_str = txt.split("=", 1)[1].strip().strip('";').strip('"')
        parts = data_str.split(",")
        if symbol.startswith("s_"):
            # s_sh000001 format: name,price,change_percent,change_amount,volume,amount
            name = parts[0]
            price = float(parts[1]) if parts[1] else 0.0
            pct = float(parts[2]) if parts[2] else 0.0
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"name": name, "price": round(price, 4), "pct_change": round(pct, 4), "time": now}
        else:
            name = parts[0]
            open_p = float(parts[1]) if parts[1] else 0.0
            prev_close = float(parts[2]) if parts[2] else 0.0
            current = float(parts[3]) if parts[3] else 0.0
            high = float(parts[4]) if parts[4] else 0.0
            low = float(parts[5]) if parts[5] else 0.0
            date = parts[30] if len(parts) > 30 else datetime.datetime.now().strftime("%Y-%m-%d")
            time_str = parts[31] if len(parts) > 31 else datetime.datetime.now().strftime("%H:%M:%S")
            pct = ((current - prev_close) / prev_close) * 100 if prev_close else 0.0
            return {"name": name, "price": round(current, 4), "pct_change": round(pct, 4), "time": f"{date} {time_str}", "open": open_p, "high": high, "low": low}
    except Exception:
        return None

def _fetch_tencent_quote(symbol):
    """
    Fetch realtime from Tencent.
    """
    try:
        url = f"http://qt.gtimg.cn/q={symbol}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        txt = r.text
        # Example: v_sh600519=~贵州茅台~600519~1825.00~1826.00~...~date~time~...
        if "=" not in txt:
            return None
        right = txt.split("=", 1)[1]
        parts = right.split("~")
        name = parts[1]
        current = float(parts[3]) if parts[3] else 0.0
        prev_close = float(parts[4]) if parts[4] else 0.0
        high = float(parts[33]) if len(parts) > 33 and parts[33] else 0.0
        low = float(parts[34]) if len(parts) > 34 and parts[34] else 0.0
        
        date = parts[30] if len(parts) > 30 else datetime.datetime.now().strftime("%Y-%m-%d")
        time_str = parts[31] if len(parts) > 31 else datetime.datetime.now().strftime("%H:%M:%S")
        pct = ((current - prev_close) / prev_close) * 100 if prev_close else 0.0
        return {
            "name": name, 
            "price": round(current, 4), 
            "pct_change": round(pct, 4), 
            "time": f"{date} {time_str}",
            "high": high,
            "low": low
        }
    except Exception:
        return None

def get_stock_name(symbol):
    name_map = {
        "sh600519": "贵州茅台",
        "sh600418": "江淮汽车",
        "sz000001": "平安银行",
        "hk00700": "腾讯控股",
        "hk09988": "阿里巴巴",
        "sz002594": "比亚迪",
        "sz300750": "宁德时代",
        "sz000858": "五粮液",
        "aapl": "苹果",
        "msft": "微软",
        "googl": "谷歌",
        "nvda": "英伟达",
        "tsla": "特斯拉",
        "amzn": "亚马逊",
        "meta": "脸书",
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
    
    # Handle US Stocks (A-Z)
    import re
    if re.match(r'^[a-zA-Z]{1,5}$', k):
        code = k.upper()
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
        "苹果": "AAPL",
        "微软": "MSFT",
        "谷歌": "GOOGL",
        "英伟达": "NVDA",
        "特斯拉": "TSLA",
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
