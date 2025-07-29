import socket
import subprocess
import os
from time import time

SERVER_ADDRESS = ('localhost', 65432)

def connect_to_server():
    """Establish a connection to the server."""

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(SERVER_ADDRESS)
            print("Connected to server at", SERVER_ADDRESS)
            return sock
        except socket.error as e:
            print(f"Connection failed: {e}. Retrying in 2 seconds...")
            sock.close()
            time.sleep(2)