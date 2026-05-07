
import os
import sys
import glob
import ast
import importlib
import subprocess
import sqlite3
import pandas as pd

import sys
# Set stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_syntax():
    print_header("1. Code Syntax Check")
    files = glob.glob("*.py")
    issues = 0
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                source = f.read()
            ast.parse(source)
            print(f"[PASS] {file}")
        except SyntaxError as e:
            print(f"[FAIL] {file}: {e}")
            issues += 1
        except Exception as e:
            print(f"[WARN] {file}: Could not read - {e}")
            issues += 1
    
    if issues == 0:
        print("\n✅ All files passed syntax check.")
        return True
    else:
        print(f"\n❌ Found {issues} syntax issues.")
        return False

def check_dependencies():
    print_header("2. Dependency Check")
    if not os.path.exists("requirements.txt"):
        print("[FAIL] requirements.txt not found.")
        return False
    
    with open("requirements.txt", "r") as f:
        reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    installed = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode("utf-8")
    installed_packages = [line.split("==")[0].lower() for line in installed.splitlines()]
    
    missing = []
    for req in reqs:
        pkg_name = req.split("==")[0].split(">=")[0].lower()
        if pkg_name not in installed_packages:
            # Special mapping for some packages if needed (e.g. PIL -> Pillow)
            # For now simple check
            missing.append(req)
            
    if not missing:
        print("✅ All dependencies appear to be installed.")
        return True
    else:
        print(f"❌ Missing dependencies: {missing}")
        print("Run: pip install -r requirements.txt")
        return False

def check_database():
    print_header("3. Database Check")
    db_path = "predictions.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        required_tables = ['predictions', 'strategy_rules', 'model_configs', 'search_history', 'knowledge_base']
        missing = [t for t in required_tables if t not in tables]
        
        if not missing:
            print(f"✅ Database connection successful. Found tables: {tables}")
            
            # Check for content stats
            cursor.execute("SELECT count(*) FROM predictions WHERE status='pending'")
            pending_count = cursor.fetchone()[0]
            print(f"ℹ️  Pending predictions: {pending_count}")
            
            cursor.execute("SELECT count(*) FROM model_configs")
            model_count = cursor.fetchone()[0]
            print(f"ℹ️  Configured models: {model_count}")
            
            conn.close()
            return True
        else:
            print(f"❌ Missing tables: {missing}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_data_source():
    print_header("4. Data Source Check (Realtime + yfinance)")
    try:
        import data_fetcher
        # Realtime index overview
        print("Testing realtime market overview (Sina/Xueqiu/Tencent)...")
        rt_idx = data_fetcher.get_market_overview()
        if rt_idx and "error" not in rt_idx:
            sh = rt_idx.get("sh_index")
            sz = rt_idx.get("sz_index")
            print(f"✅ Realtime Index: SH={sh}, SZ={sz}")
        else:
            print(f"⚠️ Realtime market overview unavailable: {rt_idx.get('error') if isinstance(rt_idx, dict) else rt_idx}")
        
        # Test individual stock fetch (historical)
        print("Testing yfinance stock fetch (sh600519)...")
        stock_df = data_fetcher.get_stock_data("sh600519", limit=5)
        if stock_df is not None and not stock_df.empty:
            print("✅ yfinance historical fetch OK.")
        else:
            print("⚠️ yfinance fetch failed (network or symbol).")
        
        # Realtime freshness check
        print("Testing realtime quote freshness (sh600519)...")
        rt = data_fetcher.get_realtime_quote("sh600519")
        if rt and rt.get("time"):
            import datetime as _dt
            try:
                rt_time = _dt.datetime.strptime(rt["time"], "%Y-%m-%d %H:%M:%S")
                delta = _dt.datetime.now() - rt_time
                minutes = delta.total_seconds() / 60.0
                print(f"Realtime source: {rt.get('source')}, price: {rt.get('price')}, time: {rt.get('time')} (Δ {minutes:.1f} min)")
                if minutes <= 10:
                    print("✅ Freshness OK (≤10 min)")
                else:
                    print("⚠️ Freshness degraded (>10 min).")
            except Exception as e:
                print(f"⚠️ Unable to parse realtime time: {e}")
        else:
            print("⚠️ Realtime quote not available.")
        
        return True
    except Exception as e:
        print(f"❌ Data source error: {e}")
        return False

def check_llm_connectivity():
    print_header("5. LLM Connectivity Check")
    try:
        import db_manager
        import llm_analyzer
        db_manager.init_db()
        models = db_manager.get_active_models()
        
        if not models:
            print("⚠️ No active models in database. Checking .env...")
            # Logic to check .env could be here, but let's stick to DB for V2.1
            pass
        
        if not models:
            print("⚠️ No models configured. Please configure models in the UI.")
            return True # Not a failure, just a state
            
        success_count = 0
        for model in models:
            print(f"Testing {model['provider']} ({model['model_name']})...")
            is_valid, msg = llm_analyzer.validate_api_key(
                model['provider'], 
                model['api_key'], 
                model['base_url']
            )
            if is_valid:
                print(f"✅ {model['provider']}: Passed")
                success_count += 1
            else:
                print(f"❌ {model['provider']}: Failed - {msg}")
        
        if success_count == len(models):
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ LLM Check error: {e}")
        return False

def main():
    print("🚀 Starting Pre-Release Checklist...")
    
    results = {
        "Syntax": check_syntax(),
        "Dependencies": check_dependencies(),
        "Database": check_database(),
        "Data Source": check_data_source(),
        "LLM": check_llm_connectivity()
    }
    
    print_header("Summary")
    all_passed = True
    for key, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{key}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\n🎉 Ready for Deployment!")
        sys.exit(0)
    else:
        print("\n⚠️ Issues found. Please fix before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
