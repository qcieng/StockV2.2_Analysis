import argparse
import data_fetcher
import llm_analyzer
import notifier
import config
import datetime

def main():
    parser = argparse.ArgumentParser(description="StockV2.0 Daily Analysis")
    parser.add_argument("--no-market-review", action="store_true", help="Skip market review")
    args = parser.parse_args()
    
    print("Starting StockV2.0 Analysis...")
    
    report_content = []
    
    # 1. Market Review
    market_info = None
    if not args.no_market_review:
        print("Fetching Market Overview...")
        market_info = data_fetcher.get_market_overview()
        report_content.append(f"## Market Overview\n{market_info}\n")
    
    # 2. Stock Analysis
    for symbol in config.DEFAULT_STOCKS:
        print(f"Analyzing {symbol}...")
        df = data_fetcher.get_stock_data(symbol)
        if df is not None:
            analysis = llm_analyzer.analyze_stock(symbol, df, market_info)
            report_content.append(f"## {symbol}\n{analysis}\n")
        else:
            report_content.append(f"## {symbol}\nFailed to fetch data.\n")
            
    # 3. Generate Report
    final_report = "\n".join(report_content)
    
    # 4. Notify
    print("Sending Notification...")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    notifier.send_email(f"Stock Analysis Report - {today}", final_report)
    
    print("Done.")

if __name__ == "__main__":
    main()
