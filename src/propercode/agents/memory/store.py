import sqlite3
from pathlib import Path
import threading

class MemoryStore:
    '''
    Handles all database operations for the agent memory
    '''
    _thread_local = threading.local()

    def __init__(self):
        config_path = Path.cwd() / ".propercode"
        self.db_path = config_path / "memory.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialize_db()
    
    def _get_conn(self) ->sqlite3.Connection:
        '''
        Gets a connection from thread-local storage or creates a new one
        '''
        if not hasattr(self._thread_local,"connection"):
            self._thread_local.connection = sqlite3.connect(self.db_path,check_same_thread=False)
            self._thread_local.connection.row_factory = sqlite3.Row
            cursor = self._thread_local.connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            self._thread_local.connection.commit()
        return self._thread_local.connection
    
    def close_conn(self):
        '''
        Closes the connection of the current thread
        '''
        if hasattr(self._thread_local,"connection"):
            self._thread_local.connection.close()
            del self._thread_local.connection
    
    def _initialize_db(self):
        '''
        Creates the tables for short and long term if they doesn't exits
        '''
        try:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prompt TEXT NOT NULL,
                full_history_json TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS derived_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                memory_type TEXT NOT NULL CHECK(memory_type IN ('summary','fact')),
                content TEXT NOT NULL,
                metadata_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversations (session_id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type ON derived_memories (memory_type);            
            """)

            conn.commit()
        except sqlite3.Error as e:
            raise e
    
    def save_conversation(self,session_id:str,user_prompt:str,history_json:str):
        '''
        Saves the full conversation history for a given session
        '''
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO conversations (session_id,user_prompt,full_history_json) VALUES (?,?,?)               
            """,(session_id,user_prompt,history_json))
            conn.commit()
        except sqlite3.Error as e:
            raise e
    
    def prune_old_memories(self,days_to_keep:int=30):
        '''
        Deleted old memories
        '''
        if days_to_keep <= 0:
            days_to_keep = 1
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()

            cutoff_date_str = f"{days_to_keep} days"

            cursor.execute("DELETE FROM derived_memories WHERE timestamp < date('now','-' || ?)",(cutoff_date_str,))
            cursor.execute("DELETE FROM conversations WHERE timestamp < date('now','-' || ?)",(cutoff_date_str,))

            conn.commit()
        except sqlite3.Error as _:
            pass