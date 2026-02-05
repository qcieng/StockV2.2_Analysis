import sqlite3
import datetime
import os

DB_NAME = "predictions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT,
            stock_name TEXT,
            prediction_time DATETIME,
            horizon TEXT,
            predicted_pct REAL,
            basis TEXT,
            actual_pct REAL,
            status TEXT DEFAULT 'pending',
            error_pct REAL
        )
    ''')
    
    # Knowledge Base Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            definition TEXT,
            impact TEXT,
            category TEXT,
            updated_at DATETIME
        )
    ''')

    # Search History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            last_searched DATETIME
        )
    ''')

    # Strategy Rules Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS strategy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            weight REAL DEFAULT 1.0,
            created_at DATETIME,
            source_info TEXT
        )
    ''')
    
    # Check if 'weight' column exists in predictions, if not add it
    try:
        c.execute("SELECT weight FROM predictions LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE predictions ADD COLUMN weight REAL DEFAULT 1.0")
        
    # Check if 'model_provider' column exists in predictions, if not add it
    try:
        c.execute("SELECT model_provider FROM predictions LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE predictions ADD COLUMN model_provider TEXT DEFAULT 'unknown'")

    # Model Configs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT,
            api_key TEXT,
            base_url TEXT,
            model_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME
        )
    ''')

    conn.commit()
    conn.close()
    
    # Seed initial strategies if empty
    seed_initial_strategies()

def seed_initial_strategies():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM strategy_rules")
    if c.fetchone()[0] == 0:
        initial_rules = [
            "关注MACD金叉且成交量放大的股票，短期上涨概率较大。",
            "当RSI指标低于30时，通常视为超卖信号，可能存在反弹机会。",
            "均线多头排列（5日>10日>20日）是强势股的重要特征。"
        ]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for rule in initial_rules:
            c.execute("INSERT INTO strategy_rules (content, weight, created_at, source_info) VALUES (?, ?, ?, ?)", 
                      (rule, 1.0, now, "System Seed"))
        conn.commit()
    conn.close()

def add_model_config(provider, api_key, base_url, model_name=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Check if exists
    c.execute("SELECT id FROM model_configs WHERE provider=? AND api_key=?", (provider, api_key))
    if c.fetchone():
        c.execute("UPDATE model_configs SET base_url=?, model_name=?, is_active=1, created_at=? WHERE provider=? AND api_key=?",
                  (base_url, model_name, now, provider, api_key))
    else:
        c.execute("INSERT INTO model_configs (provider, api_key, base_url, model_name, created_at) VALUES (?, ?, ?, ?, ?)",
                  (provider, api_key, base_url, model_name, now))
    conn.commit()
    conn.close()

def get_active_models():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, provider, api_key, base_url, model_name FROM model_configs WHERE is_active=1")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "provider": r[1], "api_key": r[2], "base_url": r[3], "model_name": r[4]} for r in rows]

def delete_model_config(model_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM model_configs WHERE id=?", (model_id,))
    conn.commit()
    conn.close()

def add_search_history(term):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO search_history (term, last_searched) VALUES (?, ?)", (term, now))
    conn.commit()
    conn.close()

def get_search_history(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT term FROM search_history ORDER BY last_searched DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_top_strategies(limit=3):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT content FROM strategy_rules ORDER BY weight DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_strategy_rule(content, weight=1.0, source="Initial"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Avoid duplicates
    c.execute("SELECT id FROM strategy_rules WHERE content=?", (content,))
    if not c.fetchone():
        c.execute("INSERT INTO strategy_rules (content, weight, created_at, source_info) VALUES (?, ?, ?, ?)", 
                  (content, weight, now, source))
    conn.commit()
    conn.close()

def update_prediction_weight(pred_id, increment=0.01):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE predictions SET weight = weight + ? WHERE id=?", (increment, pred_id))
    conn.commit()
    conn.close()
    
def get_successful_prediction_bases(limit=20):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get bases of verified predictions with low error (e.g., < 1.0%)
    c.execute("SELECT basis FROM predictions WHERE status='verified' AND error_pct < 1.0 ORDER BY prediction_time DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_knowledge_term(term, definition, impact, category="General"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute('''
            INSERT OR REPLACE INTO knowledge_base (term, definition, impact, category, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (term, definition, impact, category, now))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding term {term}: {e}")
        return False
    finally:
        conn.close()

def search_knowledge_terms(query=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if query:
        search = f"%{query}%"
        c.execute("SELECT * FROM knowledge_base WHERE term LIKE ? OR definition LIKE ? ORDER BY term", (search, search))
    else:
        c.execute("SELECT * FROM knowledge_base ORDER BY term")
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_terms_list():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT term FROM knowledge_base")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_prediction(stock_code, stock_name, horizon, predicted_pct, basis, model_provider="unknown"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO predictions (stock_code, stock_name, prediction_time, horizon, predicted_pct, basis, status, weight, model_provider)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', 1.0, ?)
    ''', (stock_code, stock_name, now, horizon, predicted_pct, basis, model_provider))
    conn.commit()
    conn.close()

def get_pending_predictions(stock_code=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if stock_code:
        c.execute("SELECT * FROM predictions WHERE status='pending' AND stock_code=?", (stock_code,))
    else:
        c.execute("SELECT * FROM predictions WHERE status='pending'")
    rows = c.fetchall()
    conn.close()
    return rows

def update_prediction_result(pred_id, actual_pct):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Get predicted_pct to calculate error
    c.execute("SELECT predicted_pct FROM predictions WHERE id=?", (pred_id,))
    row = c.fetchone()
    if row:
        predicted_pct = row[0]
        error_pct = abs(predicted_pct - actual_pct)
        
        c.execute('''
            UPDATE predictions 
            SET actual_pct=?, status='verified', error_pct=?
            WHERE id=?
        ''', (actual_pct, error_pct, pred_id))
        
        # If error is small, increase weight
        if error_pct < 1.0:
            c.execute("UPDATE predictions SET weight = weight + 0.01 WHERE id=?", (pred_id,))
            
        conn.commit()
    conn.close()

def get_learning_context(stock_code, limit=5):
    """
    Retrieve past verified predictions (both good and bad) to help the LLM learn.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Get recent verified predictions, ordered by error rate (descending to show mistakes, or mix)
    # Let's get a mix of high errors (to correct) and low errors (to reinforce)
    c.execute('''
        SELECT horizon, predicted_pct, actual_pct, basis, error_pct 
        FROM predictions 
        WHERE stock_code=? AND status='verified'
        ORDER BY prediction_time DESC 
        LIMIT ?
    ''', (stock_code, limit))
    rows = c.fetchall()
    conn.close()
    
    context_str = ""
    for r in rows:
        horizon, pred, act, basis, err = r
        context_str += f"- [{horizon}] Predicted {pred}%, Actual {act}%. Error: {err:.2f}%. Basis: {basis}\n"
    
    return context_str

if __name__ == "__main__":
    init_db()
