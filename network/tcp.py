import logging
class Tcp:
    # data comes in bytes just like the sys call send
    @staticmethod
    def send(conn, data):
        conn.sendall(len(data).to_bytes(4, 'big') + b'\x01' + data) # the b'\x01' is a simple marker to indicate that this is not a heartbeat message
    # data comes in bytes just like the sys call recv
    def send_heartbeat(conn):
        conn.sendall((0).to_bytes(4, 'big') + b'\x00') # the b'\x00' is a simple marker to indicate that this is a heartbeat message
    @staticmethod
    def recive(conn):
        raw_len = b''
        while len(raw_len) < 4:
            packet = conn.recv(4 - len(raw_len))
            if not packet:
                return
            raw_len += packet
        msg_len = int.from_bytes(raw_len, 'big')
        heartbeat_marker = conn.recv(1)
        if not heartbeat_marker:
            return
        if heartbeat_marker == b'\x00':
            return b"\x00"
        else:
            data = b''
            while len(data) < msg_len:
                packet = conn.recv(msg_len - len(data))
                if not packet:
                    return
                data += packet
            return data