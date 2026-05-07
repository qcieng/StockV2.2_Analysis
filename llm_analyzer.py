import openai
import os
import config
import json
import db_manager
import re

def analyze_stock(symbol, data_df, market_info=None, provider=None, api_key=None, base_url=None, stock_name=None, model_name=None, realtime_quote=None):
    """
    Analyze stock data using LLM with short-term predictions and self-learning context.
    """
    if data_df is None or data_df.empty:
        return {"error": "No data available for analysis."}

    # Use config defaults if not provided
    if not provider:
        provider = config.LLM_PROVIDER
    
    # Ensure DB is initialized
    db_manager.init_db()
    
    # Get Learning Context
    learning_context = db_manager.get_learning_context(symbol)
    
    # Get Top Strategies
    top_strategies = db_manager.get_top_strategies(limit=5)
    strategy_text = "\n".join([f"- {s}" for s in top_strategies])
    
    latest = data_df.iloc[-1]
    prev = data_df.iloc[-2]
    
    # Determine current data to show (Real-time vs Historical)
    current_price = latest['close']
    current_date = latest['date']
    pct_change = latest.get('pct_change', 'N/A')
    data_source_note = "Historical Data (Yesterday's Close)"
    
    if realtime_quote:
        current_price = realtime_quote.get('price', current_price)
        current_date = realtime_quote.get('time', current_date)
        pct_change = realtime_quote.get('pct_change', pct_change)
        data_source_note = f"Real-time Data (Source: {realtime_quote.get('source', 'Unknown')})"
    
    summary = f"""
    Symbol: {symbol} ({stock_name if stock_name else symbol})
    Current Date/Time: {current_date}
    Data Source: {data_source_note}
    
    **Current Price**: {current_price}
    **Daily Pct Change**: {pct_change}%
    
    Historical Context (Latest Daily Bar):
    Date: {latest['date']}
    Close: {latest['close']}
    Open: {latest['open']}
    High: {latest['high']}
    Low: {latest['low']}
    Volume: {latest['volume']}
    
    Previous Close: {prev['close']}
    """
    
    prompt = f"""
    You are a professional stock trader. Analyze the following stock data for {symbol} ({stock_name}).
    
    Data:
    {summary}
    
    Market Context:
    {market_info if market_info else "No specific market context."}
    
    **Algorithm & Strategy Context (High Weight Rules)**:
    Use the following proven strategies to guide your prediction:
    {strategy_text if strategy_text else "No specific strategies yet. Use general technical analysis."}
    
    **Historical Performance & Self-Correction**:
    The following are your past verified predictions and their errors. Use this to adjust your algorithm:
    {learning_context if learning_context else "No historical data yet."}
    
    **Task**:
    1. Analyze the technical trend and volume.
    2. **Predict the price change percentage (+/- X.X%) for the next 0.5 hour (30m), 1 hour (60m), and 2 hours (120m).**
    3. Provide the **Basis** (Reasoning) for your predictions.
    
    **Output Format**:
    You must output a JSON object inside a code block ```json ... ``` with the following structure:
    {{
        "analysis": "Brief technical analysis...",
        "predictions": {{
            "30m": {{ "pct": 0.5, "basis": "Reason..." }},
            "60m": {{ "pct": 1.2, "basis": "Reason..." }},
            "120m": {{ "pct": -0.3, "basis": "Reason..." }}
        }},
        "action_plan": {{
            "recommendation": "Buy/Sell/Hold",
            "buy_price": "...",
            "stop_loss": "...",
            "target_price": "..."
        }}
    }}
    """
    
    try:
        # Determine credentials based on provider
        final_api_key = api_key
        final_base_url = base_url
        final_model = model_name

        if provider == "deepseek":
            if not final_api_key: final_api_key = config.DEEPSEEK_API_KEY
            if not final_base_url: final_base_url = config.DEEPSEEK_BASE_URL
            if not final_model: final_model = "deepseek-chat"
        elif provider == "openai":
            if not final_api_key: final_api_key = config.OPENAI_API_KEY
            if not final_base_url: final_base_url = config.OPENAI_BASE_URL
            if not final_model: final_model = "gpt-3.5-turbo"
        elif provider == "gemini":
             if not final_api_key: final_api_key = config.GEMINI_API_KEY
             if not final_model: final_model = "gemini-pro"
        elif provider == "kimi":
             if not final_base_url: final_base_url = "https://api.moonshot.cn/v1"
             if not final_model: final_model = "moonshot-v1-8k"
        
        # Fallback if still empty
        if not final_model:
            final_model = "gpt-3.5-turbo"
        
        # If still using hardcoded defaults and they are empty, this might fail if not using the new Model Config logic passed in
        # But if 'api_key' was passed from the caller (which iterates over active models), we are good.

        if not final_api_key:
            return {"error": f"Error: Missing API Key for {provider}."}

        client = openai.OpenAI(
            api_key=final_api_key,
            base_url=final_base_url
        )
        
        response = client.chat.completions.create(
            model=final_model, 
            messages=[
                {"role": "system", "content": "You are a helpful financial analyst. You always output valid JSON inside ```json``` blocks."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                
                # Save predictions to DB
                preds = data.get("predictions", {})
                for horizon, info in preds.items():
                    # Handle pct as float (remove % if present)
                    pct_val = info.get("pct", 0)
                    if isinstance(pct_val, str):
                        try:
                            pct_val = float(pct_val.replace('%', ''))
                        except ValueError:
                            pct_val = 0.0
                    
                    db_manager.add_prediction(
                        stock_code=symbol,
                        stock_name=stock_name,
                        horizon=horizon,
                        predicted_pct=pct_val,
                        basis=info.get("basis", ""),
                        model_provider=provider # Record which model made this prediction
                    )
                
                return data

            except json.JSONDecodeError:
                return {"error": f"Error parsing JSON from LLM: {content}"}
        else:
            return {"error": "No JSON found", "raw": content}

    except Exception as e:
        import traceback
        import sys
        print(f"LLM Analysis Error for symbol {symbol}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"error": str(e)}

def optimize_algorithm(successful_bases):
    """
    Summarize successful prediction bases into general rules.
    """
    if not successful_bases:
        return "No successful bases to learn from."
        
    bases_text = "\n".join([f"- {b}" for b in successful_bases])
    
    prompt = f"""
    You are an AI Algorithm Optimizer. Below are the reasoning/bases for successful stock predictions (where the prediction was accurate).
    
    **Successful Prediction Bases**:
    {bases_text}
    
    **Task**:
    1. Identify common patterns, indicators, or logic that led to success.
    2. Abstract these into 3-5 concise, high-level **Strategic Rules** for future predictions.
    3. The rules should be actionable (e.g., "When MACD crosses above signal line with volume > 2x average, predict +1.5%").
    
    **Output**:
    Return ONLY a JSON list of strings, like:
    ["Rule 1...", "Rule 2...", "Rule 3..."]
    """
    
    try:
        # Reuse config for provider (default to openai or deepseek)
        api_key = config.DEEPSEEK_API_KEY or config.OPENAI_API_KEY
        base_url = config.DEEPSEEK_BASE_URL or config.OPENAI_BASE_URL
        model = "deepseek-chat" if config.DEEPSEEK_API_KEY else "gpt-3.5-turbo"
        
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                 {"role": "system", "content": "You are a helpful AI optimizer. Output JSON list."},
                 {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        
        # Parse JSON
        import json
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
             rules = json.loads(json_match.group(0))
             count = 0
             for rule in rules:
                 db_manager.add_strategy_rule(rule, weight=1.0, source="Optimization")
                 count += 1
             return f"Successfully generated {count} new rules."
        else:
             return f"Failed to parse rules from LLM: {content}"
             
    except Exception as e:
        return f"Error during optimization: {e}"
        return {"error": f"LLM Analysis failed: {e}"}

def analyze_market_strategy(news_list, provider=None, api_key=None, base_url=None):
    """
    Analyze market strategy based on news events.
    """
    if not news_list:
        return "No news available for strategy analysis."
        
    # Prepare news text
    news_text = "\n".join([f"- [{n['time']}] {n['content'][:100]}..." for n in news_list[:15]])
    
    prompt = f"""
    You are a strategic market strategist. Based on the following recent news events, provide a "One Week Ahead" market outlook.
    
    Recent News:
    {news_text}
    
    Logic Rules to Apply:
    1. Geopolitical Conflict -> Defense/Gold/Energy sectors may rise.
    2. AI Tech Releases (e.g., DeepSeek, OpenAI) -> AI/Compute/Chip sectors may rise.
    3. Earnings Miss/Bad Data -> Related sector drop.
    4. Policy Stimulus -> Infrastructure/Consumer/Finance rise.
    
    Output Format:
    
    ### 📅 Weekly Market Outlook
    
    **🚨 Critical Warnings**:
    - [Event] -> [Risk Level] -> [Impacted Sector]
    
    **🚀 Opportunity Radar**:
    - [Event] -> [Bullish Sector] -> [Reasoning]
    
    **📉 Risk Alerts**:
    - [Event] -> [Bearish Sector] -> [Reasoning]
    
    **🗓️ Planning for Next Week**:
    - Monday-Wednesday Focus: ...
    - Key Levels to Watch: ...
    """
    
    try:
        # Reuse validate logic or just call API
        final_base_url = base_url
        model = "gpt-3.5-turbo"
        
        if provider == "deepseek":
            if not final_base_url: final_base_url = config.DEEPSEEK_BASE_URL
            model = "deepseek-chat"
        elif provider == "openai":
            if not final_base_url: final_base_url = config.OPENAI_BASE_URL
            model = "gpt-3.5-turbo"
        elif provider == "kimi":
            if not final_base_url: final_base_url = "https://api.moonshot.cn/v1"
            model = "moonshot-v1-8k"
            
        client = openai.OpenAI(api_key=api_key, base_url=final_base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional market strategist."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Strategy Analysis Failed: {e}"

def validate_api_key(provider, api_key, base_url=None):
    """
    Returns (is_valid, message)
    """
    try:
        final_base_url = base_url
        model = "gpt-3.5-turbo"
        
        if provider == "deepseek":
            if not final_base_url: final_base_url = config.DEEPSEEK_BASE_URL
            model = "deepseek-chat"
        elif provider == "openai":
            if not final_base_url: final_base_url = config.OPENAI_BASE_URL
            model = "gpt-3.5-turbo"
        elif provider == "gemini":
            if not final_base_url: final_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/" # Approximate
            model = "gemini-pro"
        elif provider == "kimi":
            if not final_base_url: final_base_url = "https://api.moonshot.cn/v1"
            model = "moonshot-v1-8k"

        client = openai.OpenAI(
            api_key=api_key,
            base_url=final_base_url
        )
        
        # Simple test request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hi"}
            ],
            max_tokens=5
        )
        return True, "API Key is valid! Connection successful."
        
    except openai.AuthenticationError:
        return False, "Authentication Error: Invalid API Key."
    except openai.RateLimitError:
        return False, "Rate Limit Error: Insufficient quota or rate limit exceeded."
    except openai.APIConnectionError:
        return False, "Connection Error: Unable to connect to API endpoint."
    except Exception as e:
        return False, f"Validation Failed: {str(e)}"

def generate_knowledge_base(existing_terms, provider=None, api_key=None, base_url=None):
    """
    Generate new financial terms for the knowledge base.
    """
    existing_str = ", ".join(existing_terms) if existing_terms else "None"
    
    prompt = f"""
    You are a financial educator. Your goal is to expand a knowledge base of financial terms, stock market indicators, and economic abbreviations.
    
    Current terms in database: {existing_str}
    
    **Task**:
    1. Identify 5-8 NEW important financial terms, abbreviations, or indicators that are NOT in the current list.
    2. Focus on terms useful for stock trading (e.g., PMI, CPI, PPI, MACD, KDJ, BOLL, RSI, PE Ratio, PB Ratio, ROE, etc.).
    3. For each term, provide:
       - **Term**: The abbreviation or name.
       - **Definition**: A clear, concise explanation (in Chinese).
       - **Impact**: How it affects the stock market (in Chinese).
       - **Category**: e.g., "Macro", "Technical", "Fundamental".
       
    **Output Format**:
    Return ONLY a JSON array inside ```json ... ``` blocks.
    [
        {{
            "term": "PMI",
            "definition": "采购经理指数...",
            "impact": "PMI > 50 表示经济扩张...",
            "category": "Macro"
        }},
        ...
    ]
    """
    
    try:
        final_base_url = base_url
        model = "gpt-3.5-turbo"
        
        if provider == "deepseek":
            if not final_base_url: final_base_url = config.DEEPSEEK_BASE_URL
            model = "deepseek-chat"
        elif provider == "openai":
            if not final_base_url: final_base_url = config.OPENAI_BASE_URL
            model = "gpt-3.5-turbo"
        elif provider == "kimi":
            if not final_base_url: final_base_url = "https://api.moonshot.cn/v1"
            model = "moonshot-v1-8k"
            
        client = openai.OpenAI(api_key=api_key, base_url=final_base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant who outputs valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to parse entire content if no code block
        try:
            return json.loads(content)
        except:
            return []
            
    except Exception as e:
        print(f"Knowledge Generation Error: {e}")
        return []

