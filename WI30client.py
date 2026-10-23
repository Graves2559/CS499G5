'''Client'''

import socket
import sys

server_ip = "127.0.0.1"
port = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((server_ip, port))
    response = s.recv(1024).decode()
    print("Server: ", response)