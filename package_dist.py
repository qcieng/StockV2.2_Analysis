import os
import zipfile
import datetime

def package_project():
    # Project root is current directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    output_filename = f"StockV2.2_Dist_{timestamp}.zip"
    
    # Files/Dirs to exclude
    exclude_dirs = {
        '__pycache__', 
        '.git', 
        '.idea', 
        '.vscode', 
        'venv', 
        'env',
        'StockV2.1_env_backup',
        'StockV2.1_db_backup'
    }
    
    exclude_files = {
        output_filename,
        '.env',                 # Security: Don't share secrets
        'predictions.db',       # Data: Don't share local data
        'knowledge.db',
        'test_predictions.db',
        'test_knowledge.db',
        '.DS_Store'
    }
    
    print(f"📦 Packaging project into {output_filename}...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Filter directories in-place
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith(('.pyc', '.pyo', '.log', '.tar', '.zip')):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                
                print(f"  Adding: {arcname}")
                zipf.write(file_path, arcname)
                
    print("\n" + "="*50)
    print(f"✅ Package created successfully: {output_filename}")
    print(f"Size: {os.path.getsize(output_filename) / 1024:.2f} KB")
    print("="*50)
    print("Content includes source code, requirements, and documentation.")
    print("Note: .env and database files were excluded for security/cleanliness.")

if __name__ == "__main__":
    package_project()
