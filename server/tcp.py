import logging
class Tcp:
    # data comes in bytes just like the sys call send
    @staticmethod
    def send(conn, data):
        try:
            conn.sendall(len(data).to_bytes(4, 'big') + data)
        except (BrokenPipeError, ConnectionResetError) as e:
            logging.warning(f"Error in connection occurred while sending data: {e}, killing client")
            self.kill(conn)
        except Exception as e:
            logging.warning(f"Error occurred while sending data: {e}")
    # data comes in bytes just like the sys call recv
    @staticmethod
    def recive(conn):
        try:
            raw_len = conn.recv(4)
            if not raw_len:
                return None
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
