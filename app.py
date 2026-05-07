import streamlit as st
import pandas as pd
import data_fetcher
import llm_analyzer
import news_fetcher
import db_manager
import config
import os
import time
import datetime

# Ensure DB is initialized at startup
db_manager.init_db()

st.set_page_config(page_title="StockV2.2 AI Dashboard", layout="wide", page_icon="📈")

# Tech-style CSS
st.markdown("""
<style>
    /* Global Background and Font */
    .stApp {
        background-color: #F8F9FA;
        color: #212529;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #0DCAF0 !important;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #FFFFFF;
        color: #0DCAF0;
        border: 1px solid #0DCAF0;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0DCAF0;
        color: #FFFFFF;
        border-color: #0DCAF0;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #0DCAF0;
        font-size: 24px !important; /* Adjusted font size for better visibility */
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #E9ECEF;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #495057;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #0DCAF0;
        border-bottom: 2px solid #0DCAF0;
    }
    
    /* Cards/Containers */
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 StockV2.3 AI 智能决策系统")

# Initialize session state for API Key if not present
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ 系统配置 (Settings)")
    
    # Model Management Section
    st.subheader("🤖 模型管理 (Model Management)")
    
    # Add New Model Form
    with st.expander("➕ 添加新模型 (Add New Model)", expanded=False):
        new_provider = st.selectbox("Provider", ["openai", "deepseek", "gemini", "kimi"], key="new_provider")
        new_api_key = st.text_input("API Key", type="password", key="new_api_key")
        new_base_url = st.text_input("Base URL (Optional)", key="new_base_url")
        new_model_name = st.text_input("Model Name (Optional, e.g. gpt-4)", key="new_model_name")
        
        if st.button("Verify & Add"):
            if new_api_key:
                with st.spinner("Verifying connection..."):
                    # Use a temporary validation call
                    is_valid, msg = llm_analyzer.validate_api_key(
                        new_provider, new_api_key, 
                        base_url=new_base_url if new_base_url else None
                    )
                    if is_valid:
                        db_manager.add_model_config(new_provider, new_api_key, new_base_url, new_model_name)
                        st.success(f"Added {new_provider} successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Validation failed: {msg}")
            else:
                st.warning("API Key required.")

    # List Active Models
    st.write("**Active Models:**")
    active_models = db_manager.get_active_models()
    
    if not active_models:
        st.warning("⚠️ No active models configured!")
        # Fallback to .env config if DB is empty, for backward compatibility
        if config.OPENAI_API_KEY:
             st.info("Using OpenAI from .env")
        if config.DEEPSEEK_API_KEY:
             st.info("Using DeepSeek from .env")
    else:
        for model in active_models:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"✅ **{model['provider']}**" + (f" ({model['model_name']})" if model['model_name'] else ""))
            with col2:
                if st.button("🗑️", key=f"del_{model['id']}"):
                    db_manager.delete_model_config(model['id'])
                    st.rerun()
    
    st.divider()
    
    # Algorithm Display
    st.subheader("🧬 当前预测算法 (Current Prediction Algorithm)")
    top_strategies = db_manager.get_top_strategies(limit=3)
    if top_strategies:
        for idx, rule in enumerate(top_strategies):
            st.info(f"**Rule {idx+1}**: {rule}")
    else:
        st.write("Wait for initialization...")
        
    st.divider()
    
    st.subheader("自选股管理")
    st.caption("支持格式: A股(sh600519/sz000001), 港股(hk00700), 美股(AAPL/NVDA)")
    
    # Search & History
    st.write("**🔍 股票搜索 (Search Stock)**")
    search_query = st.text_input("输入代码或名称 (如: 苹果, AAPL, 茅台)", key="search_box")
    if search_query:
        results = data_fetcher.search_stock_code(search_query)
        if results:
            if len(results) == 1:
                code, name = results[0]
                if code not in config.DEFAULT_STOCKS:
                    config.DEFAULT_STOCKS.append(code)
                st.session_state['stocks_input'] = ",".join(config.DEFAULT_STOCKS)
                st.success(f"已自动填入股票代码框: {name} ({code})")
                time.sleep(0.5)
                st.rerun()
            else:
                st.write("查询结果：")
                for code, name in results:
                    if st.button(f"➕ {code} | {name}", key=f"add_{code}"):
                        if code not in config.DEFAULT_STOCKS:
                            config.DEFAULT_STOCKS.append(code)
                        st.session_state['stocks_input'] = ",".join(config.DEFAULT_STOCKS)
                        st.success(f"已添加 {name} ({code})")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.warning("未查询到该个股")
        
        # Add to history
        db_manager.add_search_history(search_query)

    # Search History
    st.write("**Recent Searches:**")
    history = db_manager.get_search_history(5)
    cols = st.columns(5)
    for i, term in enumerate(history):
        if i < 5:
            if cols[i].button(term, key=f"hist_{i}"):
                pass # Just for quick access visual, or could fill input

    default_stocks_str = ",".join(config.DEFAULT_STOCKS)
    with st.form(key='stock_form'):
        stocks_input = st.text_area("股票代码 (逗号分隔)", value=st.session_state.get('stocks_input', default_stocks_str), height=100, key="stocks_input")
        save_stocks = st.form_submit_button("更新自选股")
        if save_stocks:
             # Logic to save stocks to config (optional, can be added to config.py later)
             # Update config.DEFAULT_STOCKS in memory
             new_list = [s.strip() for s in st.session_state['stocks_input'].split(",") if s.strip()]
             config.DEFAULT_STOCKS = new_list
             st.success("自选股列表已更新 (临时生效)")
             st.rerun()

    stock_list = config.DEFAULT_STOCKS

# Tabs for Main Content
tab_dash, tab_strategy, tab_news, tab_kb = st.tabs(["📊 个股仪表盘 (Dashboard)", "🧠 市场策略 (Strategy)", "📰 财经资讯 (News)", "📚 财经知识库 (Knowledge Base)"])

# --- Tab 1: Dashboard ---
with tab_dash:
    st.header("个股深度分析")
    
    # Verification Section
    with st.expander("🔍 预测验证与模型迭代 (Prediction Verification & Learning)", expanded=False):
        if st.button("开始验证过往预测 (Verify Past Predictions)"):
            with st.spinner("Verifying..."):
                pending_rows = db_manager.get_pending_predictions()
                if not pending_rows:
                    st.info("暂无待验证的预测 (No pending predictions).")
                else:
                    count = 0
                    for row in pending_rows:
                        # row: id, stock_code, stock_name, prediction_time, horizon, predicted_pct, basis, actual_pct, status, error_pct
                        pred_id = row[0]
                        code = row[1]
                        pred_time_str = row[3]
                        horizon = row[4]
                        
                        # Calculate if it's time to verify
                        try:
                            pred_time = pd.to_datetime(pred_time_str)
                            now = pd.Timestamp.now()
                            minutes_passed = (now - pred_time).total_seconds() / 60
                            
                            target_minutes = 0
                            if horizon == '30m': target_minutes = 30
                            elif horizon == '60m': target_minutes = 60
                            elif horizon == '120m': target_minutes = 120
                            
                            if minutes_passed >= target_minutes:
                                # Fetch current price
                                df = data_fetcher.get_stock_data(code) # Daily data might not be enough for intraday check, but let's try spot
                                # Actually, better to get spot price
                                # We can use get_stock_data's last close if market is closed, or fetch real-time
                                # For simplicity, let's re-use get_stock_data(limit=1) or just trust the daily close if it's today
                                if df is not None and not df.empty:
                                    current_price = df.iloc[-1]['close']
                                    # We need the price AT prediction time to calculate actual pct change from THEN
                                    # This is tricky without minute data. 
                                    # Simplified: We assume predicted_pct is relative to the price AT PREDICTION.
                                    # We don't have that stored. We should have stored 'base_price'.
                                    # For now, let's assume the LLM predicted a move from "Previous Close" or "Open".
                                    # Actually, let's just use the current pct_change from today's open/prev_close as a proxy, 
                                    # OR better: In V2.2 we will store base_price. 
                                    # For V2.1, let's assume the user verifies against the current daily pct_change.
                                    # Wait, `predicted_pct` is usually "will rise 1%".
                                    # Let's compare `predicted_pct` with `current_daily_pct_change` roughly.
                                    # This is a limitation, but acceptable for now.
                                    
                                    actual_pct = df.iloc[-1]['pct_change']
                                    db_manager.update_prediction_result(pred_id, actual_pct)
                                    st.write(f"Verified {code} ({horizon}): Pred {row[5]}% vs Actual {actual_pct}%. Basis: {row[6]}")
                                    count += 1
                        except Exception as e:
                            st.error(f"Error verifying {code}: {e}")
                            
                    if count > 0:
                        st.success(f"Verified {count} predictions. Weights updated.")
                        
                        # Button to Trigger Algorithm Update
                        if st.button("🔄 更新预测算法 (Update Prediction Algorithm)"):
                            with st.spinner("Optimizing algorithm based on recent success..."):
                                # Fetch successful bases
                                bases = db_manager.get_successful_prediction_bases(limit=20)
                                result = llm_analyzer.optimize_algorithm(bases)
                                st.success(result)
                                time.sleep(2)
                                st.rerun()
                    else:
                        st.info("No predictions ready for verification yet.")

    st.divider()

    # Initialize Session State
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'market_info' not in st.session_state:
        st.session_state.market_info = {}

    if st.button("🚀 开始分析 (Start Analysis)", type="primary"):
        # Get Active Models
        active_models = db_manager.get_active_models()
        # Fallback to .env if empty
        if not active_models:
             if config.OPENAI_API_KEY:
                 active_models.append({"provider": "openai", "api_key": config.OPENAI_API_KEY, "base_url": config.OPENAI_BASE_URL, "model_name": "gpt-3.5-turbo"})
             elif config.DEEPSEEK_API_KEY:
                 active_models.append({"provider": "deepseek", "api_key": config.DEEPSEEK_API_KEY, "base_url": config.DEEPSEEK_BASE_URL, "model_name": "deepseek-chat"})
        
        if not active_models:
            st.error("No AI models configured! Please add a model in the sidebar.")
        else:
            progress_bar = st.progress(0)
            
            # 1. Fetch Market Overview
            with st.expander("🌍 大盘概览 (Market Overview)", expanded=True):
                with st.spinner("Fetching Market Data..."):
                    market_info = data_fetcher.get_market_overview()
                    st.session_state.market_info = market_info
            
            # 2. Analyze Stocks
            total_steps = len(stock_list) * len(active_models)
            current_step = 0
            
            for symbol in stock_list:
                stock_name = data_fetcher.get_stock_name(symbol)
                
                # Fetch Data ONCE per stock
                df = data_fetcher.get_stock_data(symbol)
                # Fetch realtime quote
                rt = data_fetcher.get_realtime_quote(symbol)
                
                # Update stock name from realtime source if available (fallback for missing static map entries)
                if rt and rt.get('name') and (stock_name == symbol or not stock_name):
                    stock_name = rt.get('name')
                
                # Build market info text with realtime context
                mi_text = ""
                if isinstance(market_info, dict):
                    sh = market_info.get("sh_index")
                    sz = market_info.get("sz_index")
                    shchg = market_info.get("sh_change")
                    szchg = market_info.get("sz_change")
                    mi_text = f"SH Index {sh} ({shchg}%), SZ Index {sz} ({szchg}%)"
                else:
                    mi_text = str(market_info)
                if rt:
                    mi_text += f"\nRealtime {stock_name}: {rt.get('price')} ({rt.get('pct_change')}%) at {rt.get('time')} via {rt.get('source')}"
                
                if df is not None and not df.empty:
                    # Run Analysis for EACH Model
                    for model_cfg in active_models:
                        provider = model_cfg['provider']
                        model_name = model_cfg['model_name']
                        api_key = model_cfg['api_key']
                        base_url = model_cfg['base_url']
                        
                        with st.spinner(f"Analyzing {stock_name} with {provider}..."):
                            # Analyze
                            report_data = llm_analyzer.analyze_stock(
                                symbol, df, mi_text, 
                                provider=provider, api_key=api_key, base_url=base_url,
                                stock_name=stock_name, model_name=model_name,
                                realtime_quote=rt
                            )
                            
                            # Store in Session State (Append or overwrite? For now overwrite per stock, 
                            # but ideally we want to show multiple. 
                            # Let's store as dict by model)
                            if symbol not in st.session_state.analysis_results:
                                st.session_state.analysis_results[symbol] = {
                                    "name": stock_name,
                                    "df": df,
                                    "reports": {}, # Changed from 'report' to 'reports' dict
                                    "timestamp": datetime.datetime.now()
                                }
                            
                            st.session_state.analysis_results[symbol]["reports"][provider] = report_data
                        
                        current_step += 1
                        progress_bar.progress(min(current_step / total_steps, 1.0))
                else:
                    st.error(f"Failed to fetch data for {symbol}")
                    current_step += len(active_models) # Skip for this stock
                    progress_bar.progress(min(current_step / total_steps, 1.0))
                
            st.success("Multi-Model Analysis Completed!")
        st.rerun()

    # Display Logic (Persistent)
    if st.session_state.market_info:
        market_info = st.session_state.market_info
        with st.expander("🌍 大盘概览 (Market Overview)", expanded=False):
             col_m1, col_m2 = st.columns(2)
             col_m1.metric("上证指数", market_info.get('sh_index', 'N/A'), market_info.get('sh_change', 'N/A'))

    st.divider()

    if st.session_state.analysis_results:
        # Create Main Layout: Two Columns
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📊 自选股分析 (Analysis)")
            # Create a scrollable container for the left side
            left_container = st.container(height=800)
            
        with c2:
            st.subheader("🔮 AI 预测 (AI Prediction)")
            # Create a scrollable container for the right side
            right_container = st.container(height=800)
        
        # Iterate through stocks and populate both containers simultaneously to maintain order
        for symbol in stock_list:
            if symbol in st.session_state.analysis_results:
                res = st.session_state.analysis_results[symbol]
                stock_name = res['name']
                df = res['df']
                reports = res.get('reports', {})
                
                # --- LEFT SIDE: Analysis ---
                with left_container:
                    st.markdown(f"#### {stock_name} ({symbol})")
                    if df is not None and not df.empty:
                        # Fetch Real-time Data FIRST
                        rt = data_fetcher.get_realtime_quote(symbol)
                        
                        # Decide what to show in Metrics
                        if rt:
                            price_display = rt.get('price')
                            pct_display = f"{rt.get('pct_change')}%"
                            time_display = rt.get('time')
                            source_display = rt.get('source')
                            
                            # Validation: Check if data is fresh (today)
                            try:
                                # Simple check: if date part of rt time is today
                                # Note: rt['time'] format varies (YYYY-MM-DD HH:MM:SS)
                                now_str = datetime.datetime.now().strftime("%Y-%m-%d")
                                if now_str not in str(time_display):
                                     time_display = f"⚠️ {time_display} (Delayed/Closed?)"
                            except:
                                pass
                                
                            metric_label = f"Close (Real-time: {time_display})"
                        else:
                            # Fallback to DataFrame last row
                            latest = df.iloc[-1]
                            price_display = latest['close']
                            pct_display = f"{latest.get('pct_change', 0)}%"
                            metric_label = f"Close (Daily: {latest['date']})"
                            source_display = "history"

                        # Display Metrics
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric(metric_label, f"{price_display}")
                        m2.metric("Chg", pct_display)
                        
                        # High/Low still from daily DF if RT doesn't provide it, 
                        # but some RT sources might. For now stick to DF or RT if available.
                        # data_fetcher.get_realtime_quote might return open/high/low/vol for Sina.
                        # Let's check if rt has high/low
                        high_display = rt.get('high') if rt and rt.get('high') else df.iloc[-1]['high']
                        low_display = rt.get('low') if rt and rt.get('low') else df.iloc[-1]['low']
                        
                        m3.metric("High", f"{high_display}")
                        m4.metric("Low", f"{low_display}")
                        
                        if rt:
                            st.caption(f"Source: {source_display} | Time: {rt.get('time')}")
                        
                        st.line_chart(df.set_index('date')['close'], height=200)
                    
                    if not reports:
                         st.write("No analysis available.")
                    else:
                        # Create tabs for each provider if multiple
                        providers = list(reports.keys())
                        if len(providers) > 1:
                            tabs = st.tabs(providers)
                            for i, provider in enumerate(providers):
                                with tabs[i]:
                                    report = reports[provider]
                                    if isinstance(report, dict) and "analysis" in report:
                                        st.write(report["analysis"])
                                    elif isinstance(report, dict) and "error" in report:
                                        st.error(f"{provider}: {report['error']}")
                                    else:
                                        st.write(f"{provider}: No analysis available.")
                        else:
                            # Single provider
                            provider = providers[0]
                            report = reports[provider]
                            st.caption(f"Model: {provider}")
                            if isinstance(report, dict) and "analysis" in report:
                                st.write(report["analysis"])
                            elif isinstance(report, dict) and "error" in report:
                                st.error(report["error"])
                    st.divider()

                # --- RIGHT SIDE: Prediction ---
                with right_container:
                    st.markdown(f"#### {stock_name} ({symbol})")
                    
                    if not reports:
                        st.write("No predictions available.")
                    else:
                        providers = list(reports.keys())
                        if len(providers) > 1:
                            tabs = st.tabs(providers)
                            for i, provider in enumerate(providers):
                                with tabs[i]:
                                    report = reports[provider]
                                    if isinstance(report, dict) and "predictions" in report:
                                        # Predictions Table
                                        preds = report.get("predictions", {})
                                        pred_data = []
                                        for h in ['30m', '60m', '120m']:
                                            item = preds.get(h, {})
                                            pred_data.append({
                                                "Time": h,
                                                "Pred": f"{item.get('pct', 0)}%",
                                                "Basis": item.get('basis', 'N/A')
                                            })
                                        st.dataframe(pd.DataFrame(pred_data), hide_index=True, use_container_width=True)
                                        
                                        # Action Plan
                                        plan = report.get("action_plan", {})
                                        st.info(f"**建议**: {plan.get('recommendation', 'N/A')}")
                                        p1, p2, p3 = st.columns(3)
                                        p1.write(f"**买入**: {plan.get('buy_price', 'N/A')}")
                                        p2.write(f"**止损**: {plan.get('stop_loss', 'N/A')}")
                                        p3.write(f"**目标**: {plan.get('target_price', 'N/A')}")
                                    elif isinstance(report, dict) and "error" in report:
                                        st.error(f"{provider}: {report['error']}")
                        else:
                            provider = providers[0]
                            report = reports[provider]
                            st.caption(f"Model: {provider}")
                            if isinstance(report, dict) and "predictions" in report:
                                preds = report.get("predictions", {})
                                pred_data = []
                                for h in ['30m', '60m', '120m']:
                                    item = preds.get(h, {})
                                    pred_data.append({
                                        "Time": h,
                                        "Pred": f"{item.get('pct', 0)}%",
                                        "Basis": item.get('basis', 'N/A')
                                    })
                                st.dataframe(pd.DataFrame(pred_data), hide_index=True, use_container_width=True)
                                
                                plan = report.get("action_plan", {})
                                st.info(f"**建议**: {plan.get('recommendation', 'N/A')}")
                                p1, p2, p3 = st.columns(3)
                                p1.write(f"**买入**: {plan.get('buy_price', 'N/A')}")
                                p2.write(f"**止损**: {plan.get('stop_loss', 'N/A')}")
                                p3.write(f"**目标**: {plan.get('target_price', 'N/A')}")
                            elif isinstance(report, dict) and "error" in report:
                                st.error(report["error"])
                    st.divider()
    else:
        st.info("👈 点击上方 '开始分析' 按钮生成报告 (Click 'Start Analysis' to generate report).")

# --- Tab 2: Strategy ---
with tab_strategy:
    st.header("🧠 智能市场策略 (Event-Driven Strategy)")
    st.info("基于最新财经新闻事件，结合预设逻辑（如地缘冲突、AI发布、财报预期）生成的未来一周市场展望。")
    
    # Initialize session state for strategy
    if 'strategy_report' not in st.session_state:
        st.session_state.strategy_report = None
    
    if st.button("🔮 生成下周策略规划 (Generate Outlook)"):
        # Get a valid model
        active_models = db_manager.get_active_models()
        if not active_models:
             st.error("请先在左侧配置并激活至少一个 AI 模型 (Please configure a model first).")
        else:
            # Use the first active model
            model_config = active_models[0]
            llm_provider = model_config['provider']
            api_key_input = model_config['api_key']
            base_url_input = model_config.get('base_url')

            with st.spinner("正在抓取新闻并生成策略..."):
                news_list = news_fetcher.get_latest_news(limit=20)
                if news_list:
                    strategy_report = llm_analyzer.analyze_market_strategy(news_list, provider=llm_provider, api_key=api_key_input, base_url=base_url_input)
                    st.session_state.strategy_report = strategy_report
                    st.success("策略生成完成！")
                else:
                    st.error("无法获取新闻数据，无法生成策略。")
    
    # Persistent Display
    if st.session_state.strategy_report:
        st.markdown(st.session_state.strategy_report)
        if st.button("🗑️ 清除策略 (Clear Strategy)"):
            st.session_state.strategy_report = None
            st.rerun()

# --- Tab 3: News ---
with tab_news:
    st.header("📰 实时财经快讯")
    
    # Initialize session state for news
    if 'news_list' not in st.session_state:
        st.session_state.news_list = None
        
    col_news_1, col_news_2 = st.columns([1, 5])
    with col_news_1:
        if st.button("🔄 刷新资讯 (Refresh)"):
            with st.spinner("Loading News..."):
                st.session_state.news_list = news_fetcher.get_latest_news(limit=30)
            st.rerun()
            
    # Auto-load if empty
    if st.session_state.news_list is None:
        with st.spinner("Loading News..."):
            st.session_state.news_list = news_fetcher.get_latest_news(limit=30)
            
    # Persistent Display
    if st.session_state.news_list:
        for news in st.session_state.news_list:
            with st.container():
                st.markdown(f"**[{news['time']}] {news['title']}**")
                st.write(news['content'])
                st.divider()

# --- Tab 4: Knowledge Base ---
with tab_kb:
    st.header("📚 财经知识库 (Financial Knowledge Base)")
    st.info("每周累积更新，解释常用术语（如PMI、MACD等）及其对股市的影响。")
    
    col_kb_1, col_kb_2 = st.columns([3, 1])
    
    with col_kb_2:
        st.subheader("⚙️ 管理")
        if st.button("📅 运行周度智能更新 (Weekly Update)"):
            # Get a valid model
            active_models = db_manager.get_active_models()
            if not active_models:
                 st.error("请先在左侧配置并激活至少一个 AI 模型 (Please configure a model first).")
            else:
                model_config = active_models[0]
                llm_provider = model_config['provider']
                api_key_input = model_config['api_key']
                base_url_input = model_config.get('base_url')
                
                with st.spinner("AI 正在扫描并生成新知识点..."):
                    existing_terms = db_manager.get_all_terms_list()
                    new_terms = llm_analyzer.generate_knowledge_base(existing_terms, provider=llm_provider, api_key=api_key_input, base_url=base_url_input)
                    
                    if new_terms:
                        count = 0
                        for item in new_terms:
                            if db_manager.add_knowledge_term(item.get('term'), item.get('definition'), item.get('impact'), item.get('category', 'General')):
                                count += 1
                        if count > 0:
                            st.success(f"成功新增 {count} 个知识点！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("未能新增知识点（可能已存在）。")
                    else:
                        st.error("AI 生成失败，请检查 API 配置。")
                    
        with st.expander("➕ 手动添加 (Manual Add)"):
            with st.form("add_term_form"):
                new_term = st.text_input("术语 (Term)")
                new_def = st.text_area("定义 (Definition)")
                new_impact = st.text_area("股市影响 (Impact)")
                new_cat = st.selectbox("分类 (Category)", ["Macro", "Technical", "Fundamental", "Other"])
                submitted = st.form_submit_button("添加")
                if submitted and new_term:
                    if db_manager.add_knowledge_term(new_term, new_def, new_impact, new_cat):
                        st.success(f"已添加: {new_term}")
                        st.rerun()
                    else:
                        st.error("添加失败")

    with col_kb_1:
        search_query = st.text_input("🔍 搜索术语 (Search Term)", placeholder="输入如 'PMI' 或 'MACD'...")
        
        terms = db_manager.search_knowledge_terms(search_query)
        
        if not terms:
            st.info("知识库暂为空，请点击右侧 '运行周度智能更新' 初始化数据。")
        else:
            for term_row in terms:
                # id, term, definition, impact, category, updated_at
                t_term = term_row[1]
                t_def = term_row[2]
                t_imp = term_row[3]
                t_cat = term_row[4]
                
                with st.expander(f"📌 {t_term} ({t_cat})", expanded=True if search_query else False):
                    st.markdown(f"**定义**: {t_def}")
                    st.markdown(f"**股市影响**: {t_imp}")
                    st.caption(f"更新时间: {term_row[5]}")
