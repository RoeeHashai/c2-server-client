import sqlite3
import logging
from datetime import datetime
class DBLogger(logging.Handler):
    def __init__(self, db_path='c2_logs.db'):
        super().__init__()
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    timestamp TEXT,
                    level TEXT,
                    message TEXT
                )
            ''')
            conn.commit()
    def emit(self, record):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            log_msg = record.getMessage()
            log_level = record.levelname
            log_timestampe = datetime.fromtimestamp(record.created).isoformat()
            cursor.execute("INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)", (log_timestampe, log_level, log_msg))
            conn.commit()