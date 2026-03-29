import socket
import argparse
from crypto import Security

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.security = Security()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))
        print(f"Connected to server at {self.server_ip}:{self.server_port}")
        try:
            self.security.handshake(self.socket)
        except Exception as e:
            print(f"Failed handshake with: {e}")
        
    def execute_command(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                break
            data = data.replace(b'\x00', b'') 
            if data:
                command = self.security.decrypt(data).decode()
                print(f"Received command: {command}")
                ciphertext = self.security.encrypt(f"Executed command: {command}".encode())
                self.socket.sendall(ciphertext)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple client for connecting to the server")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address of the server to connect to")
    parser.add_argument("--port", type=int, default=12345, help="Port number of the server to connect to")
    args = parser.parse_args()
    client = Client(args.ip, args.port)
    client.execute_command()
    