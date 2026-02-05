import akshare as ak

try:
    print("Testing stock_individual_info_em...")
    df = ak.stock_individual_info_em(symbol="600519")
    print(df)
except Exception as e:
    print(e)
