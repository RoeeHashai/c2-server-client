import logging
from enum import Enum

class ReciveType(Enum):
    DATA = 1
    NO_DATA = 2
    DISCONNECTED = 3

class Tcp:
    # data comes in bytes just like the sys call send
    @staticmethod
    def send(conn, data):
        conn.sendall(len(data).to_bytes(4, 'big') + data)
    # data comes in bytes just like the sys call recv
    @staticmethod
    def send_heartbeat(conn):
        conn.sendall((0).to_bytes(4, 'big'))
    @staticmethod
    def recive(conn):
        raw_len = b''
        while len(raw_len) < 4:
            packet = conn.recv(4 - len(raw_len))
            if not packet:
                return (ReciveType.DISCONNECTED, b"")
            raw_len += packet
        msg_len = int.from_bytes(raw_len, 'big')
        if msg_len == 0:
            return (ReciveType.NO_DATA, b"")
        else:
            data = b''
            while len(data) < msg_len:
                packet = conn.recv(msg_len - len(data))
                if not packet:
                    return (ReciveType.DISCONNECTED, b"")
                data += packet
            return (ReciveType.DATA, data)