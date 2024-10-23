import logging
import logging.config
import colorlog
import sqlite3

class SQLiteHandler(logging.Handler):
    def __init__(self, db='log.db'):
        logging.Handler.__init__(self)
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created TEXT,
                name TEXT,
                loglevel TEXT,
                message TEXT
            )
        ''')
        self.conn.commit()

    
    def format_time(self, record):
        return self.formatter.formatTime(record, self.formatter.datefmt)

    
    def emit(self, record):
        log_entry = self.format(record)
        self.cursor.execute('''
            INSERT INTO logs (created, name, loglevel, message)
            VALUES (?, ?, ?, ?)
        ''', (self.format_time(record), record.name, record.levelname, log_entry))
        self.conn.commit()

    def close(self):
        self.conn.close()
        super().close()
        
    
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'colored_console': {
            'level': 'DEBUG',
            'class': 'colorlog.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'app.log',
            'mode': 'a',
        },
        'db': {
            'level': 'DEBUG',
            'class': 'setup_logging.SQLiteHandler',  # Replace with the appropriate import path
            'formatter': 'standard',
        },
    },
    'loggers': {
        'urllib3.connectionpool': {
            'handlers': ['colored_console'],
            'level': 'ERROR',
            'propagate': False
        },
        'httpcore.http11': {
            'handlers': ['colored_console'],
            'level': 'ERROR',
            'propagate': False
        },
        'httpx': {
            'handlers': ['colored_console'],
            'level': 'ERROR',
            'propagate': False
        },
        'filelock': {
            'handlers': ['colored_console'],
            'level': 'ERROR',
            'propagate': False
        },
        "httpcore.connection": {
            'handlers': ['colored_console'],
            'level': 'ERROR',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['colored_console'],  # Set 'console' as the default handler
        'level': 'DEBUG',       # Set the default logging level
    }
}

logging.config.dictConfig(LOGGING_CONFIG)