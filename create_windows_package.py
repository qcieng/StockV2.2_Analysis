import os
import shutil
import subprocess
import sys

def create_dist_package():
    dist_dir = "dist/StockV2.3_Portable"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 1. Copy Source Files
    files_to_copy = [
        "app.py", "data_fetcher.py", "llm_analyzer.py", "db_manager.py",
        "config.py", "news_fetcher.py", "requirements.txt", "README.md",
        ".env.example"
    ]
    
    print("Copying files...")
    for f in files_to_copy:
        if os.path.exists(f):
            shutil.copy(f, os.path.join(dist_dir, f))
        else:
            print(f"Warning: {f} not found.")
            
    # Copy DB if exists (as a template, though usually we want fresh)
    # Actually, let's NOT copy the DB to ensure fresh start for users, 
    # OR copy it if it contains critical config. 
    # V2.3 stores model configs in DB. So we SHOULD copy it if it has basic data.
    # But user data might be sensitive. 
    # Let's create an empty DB or just let app init it.
    # We will copy 'predictions.db' if it exists, assuming it's the "template"
    if os.path.exists("predictions.db"):
        shutil.copy("predictions.db", os.path.join(dist_dir, "predictions.db"))

    # 2. Create Start Script (Windows Batch)
    bat_content = r"""@echo off
title StockV2.3 AI Dashboard
echo ===================================================
echo      StockV2.3 AI Intelligent Decision System
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)

echo [1/3] Checking environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo [2/3] Activating environment & Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt -q

echo [3/3] Starting Application...
echo.
echo Opening Dashboard in your browser...
echo Press Ctrl+C to stop the server.
echo.
streamlit run app.py --server.headless true

pause
"""
    with open(os.path.join(dist_dir, "start_app.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    print(f"Portable package created at: {dist_dir}")
    
    # 3. Zip it
    shutil.make_archive("StockV2.3_Portable", 'zip', "dist")
    print("Zipped to StockV2.3_Portable.zip")

if __name__ == "__main__":
    create_dist_package()
