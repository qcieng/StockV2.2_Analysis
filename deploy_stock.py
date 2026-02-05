import paramiko
import os
import time
import tarfile

# Configuration
HOST = '192.168.137.68'
USER = 'host'
PASS = 'Huawei@123'
REMOTE_DIR = '/home/host/StockV2.1'
LOCAL_TAR = 'StockV2.2.tar'

def create_tar():
    base = os.getcwd()
    exclude_dirs = {'media', '__pycache__', '.git', 'venv', 'StockV2.1_env_backup', 'StockV2.1_db_backup'}
    if os.path.exists(LOCAL_TAR):
        os.remove(LOCAL_TAR)
    print(f"Creating {LOCAL_TAR}...", flush=True)
    with tarfile.open(LOCAL_TAR, 'w') as tar:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith(('.pyc', '.pyo')) or f == os.path.basename(LOCAL_TAR):
                    continue
                fullpath = os.path.join(root, f)
                relpath = os.path.relpath(fullpath, base)
                tar.add(fullpath, arcname=relpath)

def deploy():
    create_tar()
    print(f"Connecting to {HOST}...", flush=True)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)
    
    sftp = ssh.open_sftp()
    print(f"Ensuring remote directory {REMOTE_DIR} exists...", flush=True)
    try:
        sftp.stat(REMOTE_DIR)
    except IOError:
        sftp.mkdir(REMOTE_DIR)
    sftp.close()

    print("Stopping old process...", flush=True)
    # Kill streamlit process
    ssh.exec_command(f'echo {PASS} | sudo -S pkill -f streamlit')
    time.sleep(2)

    print("Backing up remote .env and database if exists...", flush=True)
    # Check if .env exists before moving
    stdin, stdout, stderr = ssh.exec_command(f'test -f {REMOTE_DIR}/.env && echo "exists"')
    if stdout.read().decode().strip() == "exists":
        print("Found existing .env, backing up...", flush=True)
        ssh.exec_command(f'cp {REMOTE_DIR}/.env {REMOTE_DIR}/.env.bak')
        ssh.exec_command(f'mv {REMOTE_DIR}/.env {REMOTE_DIR}_env_backup')
    else:
        print("No existing .env found, skipping backup.", flush=True)

    # Check if predictions.db exists before moving
    stdin, stdout, stderr = ssh.exec_command(f'test -f {REMOTE_DIR}/predictions.db && echo "exists"')
    if stdout.read().decode().strip() == "exists":
        print("Found existing predictions.db, backing up...", flush=True)
        ssh.exec_command(f'mv {REMOTE_DIR}/predictions.db {REMOTE_DIR}_db_backup')
    else:
        print("No existing predictions.db found.", flush=True)
    
    print("Cleaning remote directory...", flush=True)
    stdin, stdout, stderr = ssh.exec_command(f'echo {PASS} | sudo -S rm -rf {REMOTE_DIR}/*')
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Error cleaning project: {stderr.read().decode()}", flush=True)
    
    print("Uploading archive...", flush=True)
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_TAR, f'{REMOTE_DIR}/{LOCAL_TAR}')
    sftp.close()

    print("Executing remote setup...", flush=True)
    commands = [
        f'cd {REMOTE_DIR} && tar -xf {LOCAL_TAR}',
        # Restore .env only if backup exists
        f'if [ -f {REMOTE_DIR}_env_backup ]; then mv {REMOTE_DIR}_env_backup {REMOTE_DIR}/.env; fi',
        # Restore predictions.db if backup exists
        f'if [ -f {REMOTE_DIR}_db_backup ]; then mv {REMOTE_DIR}_db_backup {REMOTE_DIR}/predictions.db; fi',
        # Check if requirements.txt exists before installing
        f'cd {REMOTE_DIR} && if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi',
        # Run checklist for verification
        f'cd {REMOTE_DIR} && python3 checklist.py',
        # Run streamlit on port 8080
        f'cd {REMOTE_DIR} && nohup python3 -m streamlit run app.py --server.port 8080 --server.address 0.0.0.0 > app.log 2>&1 &'
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}", flush=True)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        if 'nohup' not in cmd:
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                err = stderr.read().decode()
                print(f"Error executing command: {cmd}")
                print(f"Details: {err}")
            else:
                print(stdout.read().decode())
        else:
            time.sleep(5) # Wait for startup
            
    print("\n" + "="*50)
    print("✅ 部署脚本执行完毕 (Deployment Script Finished)")
    print(f"请尝试访问: http://{HOST}:8080")
    print("="*50)
            
    ssh.close()
    if os.path.exists(LOCAL_TAR):
        os.remove(LOCAL_TAR)

if __name__ == "__main__":
    deploy()
