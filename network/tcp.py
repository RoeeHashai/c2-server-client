import logging
class Tcp:
    # data comes in bytes just like the sys call send
    @staticmethod
    def send(conn, data):
        conn.sendall(len(data).to_bytes(4, 'big') + data)
    # data comes in bytes just like the sys call recv
    @staticmethod
    def recive(conn):
        try:
            raw_len = b''
            while len(raw_len) < 4:
                packet = conn.recv(4 - len(raw_len))
                if not packet:
                    return None
                raw_len += packet
            msg_len = int.from_bytes(raw_len, 'big')
            data = b''
            while len(data) < msg_len:
                packet = conn.recv(msg_len - len(data))
                if not packet:
                    return
                data += packet
            return data
        except Exception as e:
            logging.warning(f"Error occurred while receiving data: {e}")
            return None
