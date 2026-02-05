
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
    print_header("4. Data Source Check (yfinance)")
    try:
        import data_fetcher
        print("Testing connection to yfinance...")
        # Try a robust index
        df = data_fetcher.get_market_overview()
        if df and "error" not in df:
            print("✅ Market overview fetched successfully.")
            
            # Test individual stock fetch
            print("Testing individual stock fetch (sh600519)...")
            stock_df = data_fetcher.get_stock_data("sh600519", limit=5)
            if stock_df is not None and not stock_df.empty:
                 print("✅ Individual stock fetched successfully.")
                 return True
            else:
                 print("⚠️ Individual stock fetch failed (could be market hours or network).")
                 return True # Don't fail the whole check for this
        else:
            print(f"❌ Failed to fetch market overview: {df.get('error')}")
            return False
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
