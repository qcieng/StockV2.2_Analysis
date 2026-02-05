import paramiko
import time

HOST = '192.168.137.68'
USER = 'host'
PASS = 'Huawei@123'
REMOTE_DIR = '/home/host/StockV2.1'

def check_server():
    print(f"Connecting to {HOST}...", flush=True)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS)

    print("\n[Checking Directory Content]")
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {REMOTE_DIR}")
    print(stdout.read().decode())

    print("\n[Checking Process]")
    stdin, stdout, stderr = ssh.exec_command("ps -ef | grep streamlit | grep -v grep")
    process = stdout.read().decode().strip()
    if process:
        print("✅ Streamlit process found:")
        print(process)
    else:
        print("❌ Streamlit process NOT found!")

    print("\n[Checking Port 8080]")
    stdin, stdout, stderr = ssh.exec_command("netstat -tuln | grep 8080")
    port_status = stdout.read().decode().strip()
    if port_status:
        print("✅ Port 8080 is listening:")
        print(port_status)
    else:
        print("❌ Port 8080 is NOT listening!")

    print("\n[Checking Logs (tail -n 50)]")
    stdin, stdout, stderr = ssh.exec_command(f"tail -n 50 {REMOTE_DIR}/app.log")
    logs = stdout.read().decode()
    if logs:
        print(logs)
    else:
        print("Log file empty or not found.")

    print("\n[Checking Connectivity to DeepSeek API]")
    # Run the test_llm_connection.py script
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR} && python3 test_llm_connection.py")
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(out)
    if err:
        print("STDERR:")
        print(err)
        
    print("\n[Inspecting .env file keys]")
    # Print keys only, mask values
    stdin, stdout, stderr = ssh.exec_command(f"grep -o '^[^=]*' {REMOTE_DIR}/.env")
    keys = stdout.read().decode()
    print("Keys found in .env:")
    print(keys)
    
    ssh.close()

if __name__ == "__main__":
    check_server()
