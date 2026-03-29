# C2 Server-Client Exercise
## Overview
This project is a C2 (Command and Control) server that listens for incoming connections and has the ability to send commands to clients and receive their output. The server can also be managed through a simple command-line interface. Both the server and the client are multi-threaded. I will explain shortly the different threads and their purposes. The server supports secure communication with clients using AES encryption and RSA for key exchange. Additionally, the server writes logs to a file and also stores them in a SQLite database.

## Server
### CLI Interface
The commands that our server supports are the following:
- help: Displays a help message. Usage: help
- exit: Exits the server. Usage: exit
- clients: Displays active clients. Usage: clients
- send: Sends a command to a client. Usage: send <client_id> <command>
- kill: Kills a client. Usage: kill <client_id>
- info: Displays information about the server. Usage: info

### Threads
The server has the following threads:
- Main thread: Responsible for managing the CLI interface.
- Listen thread: Responsible for listening for incoming connections and adding new connections to the active clients list.
- Heartbeat thread: Responsible for cleaning up inactive clients and removing them from the active clients list.
- Thread pool: Handles communication with clients and sends commands to them.

### Secure Communication
On top of our TCP communication, there is a layer of security. We use RSA for key exchange and AES for encrypting communication between the server and the clients. When a new client connects to the server, the client generates a random symmetric key, encrypts it with the server's public key, and sends it to the server. The server then decrypts the symmetric key with its private key and uses it for encrypting and decrypting communication with that client. All of this key exchange happens during the handshake, and after the handshake is complete, all communication between the server and the client is encrypted with AES.

# Client
### Threads
The client's threads are a bit simpler. The client has the following threads:
- Main thread: Listens for incoming commands from the server.
- Thread pool: After a new command is received from the server, the client submits the command to the thread pool, where the bash command is executed as a new subprocess and the output is sent back to the server.

# Usage
First, install the requirements:
```
pip install -r requirements.txt
```

To run the server, use the following command:
```
python3 server/server.py
```
This will run the server on "127.0.0.1" and port 12345 by default. You can change the IP and port by passing them as arguments:
```
python3 server/server.py --ip <ip> --port <port>
```
Similarly, to run the client, use the following command:
```
python3 client/client.py
```
The same flags are relevant here as well.

# Inputs And Outputs Examples
## Example 1
### Server
```
(venv) roeehashai@roeeh c2-server-client $ python3 server/server.py
cli> clients
Client ID: 1, Address: 127.0.0.1:51845
cli> send 1 echo "Hello World!"
cli> send 1 pwd
cli> send 2 echo "BAD!!"
Non existing client
cli> info
Server Info:
  IP: 127.0.0.1
  Port: 12345
cli> help
help: Displays a help message, usage: help
exit: Exits the server, usage: exit
clients: Displays active clients, usage: clients
send: Sends a command to a client, usage: send <client_id> <command>
kill: Kills a client, usage: kill <client_id>
info: Displays information about the server, usage: info
cli> kill 1
cli> clients
No active clients.
cli> exit
```
### Client
```
(venv) roeehashai@roeeh c2-server-client $ python3 client/client.py
Received command: echo "Hello World!"
Hello World!

Received command: pwd
/Users/roeehashai/projects/c2-server-client
```

### Logging
```
2026-03-29 19:15:32,137 [INFO] New connection accepted in address 127.0.0.1:51845
2026-03-29 19:15:47,738 [INFO] Sending command to client 1: echo "Hello World!"
2026-03-29 19:15:47,753 [INFO] Received data from client 1: Hello World!

2026-03-29 19:15:57,409 [INFO] Sending command to client 1: pwd
2026-03-29 19:15:57,417 [INFO] Received data from client 1: /Users/roeehashai/projects/c2-server-client

2026-03-29 19:16:13,712 [WARNING] Non existing client: 2 cannot send command: echo "BAD!!"
2026-03-29 19:16:42,114 [INFO] Removing client 1 from security manager
2026-03-29 19:16:42,119 [INFO] Killed client 1 at address 127.0.0.1:51845
2026-03-29 19:16:57,152 [INFO] Exiting server...
```

## Example 2
### Server
```
(venv) roeehashai@roeeh c2-server-client $ python3 server/server.py --port 11112
cli> display
Invalid command or incorrect number of arguments. Type 'help' for a list of commands.
cli> clients
Client ID: 1, Address: 127.0.0.1:52402
Client ID: 2, Address: 127.0.0.1:52403
cli> send 1 pwd
cli> send 2 ls -la
cli> send 1 sleep 10 | echo "done-10"
cli> send 1 sleep 15 | echo "done-15"
cli> send 1 sleep 20 | echo "done-20"
cli> send 2 pwd
cli> kill 2
cli> exit
```
### Client 1
```
(venv) roeehashai@roeeh c2-server-client $ python3 client/client.py --port 11112
Received command: pwd
/Users/roeehashai/projects/c2-server-client

Received command: sleep 10 | echo "done-10"
done-10

Received command: sleep 15 | echo "done-15"
Received command: sleep 20 | echo "done-20"
done-15

done-20
```
### Client 2
```
(venv) roeehashai@roeeh c2-server-client $ python3 client/client.py --port 11112
Received command: ls -la
total 104
drwxr-xr-x  11 roeehashai  staff    352 Mar 29 20:11 .
drwxr-xr-x@ 25 roeehashai  staff    800 Mar 29 11:09 ..
drwxr-xr-x  16 roeehashai  staff    512 Mar 29 20:05 .git
-rw-r--r--   1 roeehashai  staff     79 Mar 29 17:25 .gitignore
-rw-r--r--   1 roeehashai  staff  32768 Mar 29 20:11 c2_logs.db
drwxr-xr-x   6 roeehashai  staff    192 Mar 29 19:56 client
-rw-r--r--   1 roeehashai  staff    520 Mar 29 20:11 logfile.log
-rw-r--r--   1 roeehashai  staff   4547 Mar 29 19:18 readme.md
-rw-r--r--   1 roeehashai  staff     81 Mar 29 19:03 requirements.txt
drwxr-xr-x   7 roeehashai  staff    224 Mar 29 19:55 server
drwxr-xr-x   7 roeehashai  staff    224 Mar 29 14:50 venv

Received command: pwd
/Users/roeehashai/projects/c2-server-client
```

### Logging
```
2026-03-29 20:11:09,569 [INFO] New connection accepted in address 127.0.0.1:52402
2026-03-29 20:11:13,398 [INFO] New connection accepted in address 127.0.0.1:52403
2026-03-29 20:11:16,312 [WARNING] Invalid command or incorrect number of arguments. Type 'help' for a list of commands.
2026-03-29 20:11:38,530 [INFO] Sending command to client 1: pwd
2026-03-29 20:11:38,550 [INFO] Received data from client 1: /Users/roeehashai/projects/c2-server-client

2026-03-29 20:11:44,815 [INFO] Sending command to client 2: ls -la
2026-03-29 20:11:44,837 [INFO] Received data from client 2: total 104
drwxr-xr-x  11 roeehashai  staff    352 Mar 29 20:11 .
drwxr-xr-x@ 25 roeehashai  staff    800 Mar 29 11:09 ..
drwxr-xr-x  16 roeehashai  staff    512 Mar 29 20:05 .git
-rw-r--r--   1 roeehashai  staff     79 Mar 29 17:25 .gitignore
-rw-r--r--   1 roeehashai  staff  32768 Mar 29 20:11 c2_logs.db
drwxr-xr-x   6 roeehashai  staff    192 Mar 29 19:56 client
-rw-r--r--   1 roeehashai  staff    520 Mar 29 20:11 logfile.log
-rw-r--r--   1 roeehashai  staff   4547 Mar 29 19:18 readme.md
-rw-r--r--   1 roeehashai  staff     81 Mar 29 19:03 requirements.txt
drwxr-xr-x   7 roeehashai  staff    224 Mar 29 19:55 server
drwxr-xr-x   7 roeehashai  staff    224 Mar 29 14:50 venv

2026-03-29 20:12:20,256 [INFO] Sending command to client 1: sleep 10 | echo "done-10"
2026-03-29 20:12:30,270 [INFO] Received data from client 1: done-10

2026-03-29 20:12:30,897 [INFO] Sending command to client 1: sleep 15 | echo "done-15"
2026-03-29 20:12:45,274 [INFO] Sending command to client 1: sleep 20 | echo "done-20"
2026-03-29 20:12:45,926 [INFO] Received data from client 1: done-15

2026-03-29 20:12:53,239 [INFO] Sending command to client 2: pwd
2026-03-29 20:12:53,247 [INFO] Received data from client 2: /Users/roeehashai/projects/c2-server-client

2026-03-29 20:13:05,285 [INFO] Received data from client 1: done-20

2026-03-29 20:13:11,508 [INFO] Removing client 2 from security manager
2026-03-29 20:13:11,511 [INFO] Killed client 2 at address 127.0.0.1:52403
2026-03-29 20:13:12,985 [INFO] Exiting server...
2026-03-29 20:13:12,988 [INFO] Removing client 1 from security manager
2026-03-29 20:13:12,991 [INFO] Killed client 1 at address 127.0.0.1:52402
```