import sqlite3
import json

from propercode.agents.memory.store import MemoryStore
from propercode.models.agents.memory_models import SearchMemoryToolInput,WriteMemoryToolInput

class SearchMemoryTool:
    '''
    A tool for searching the agent's memory
    '''
    def __init__(self,memory_store:MemoryStore):
        self.memory_store = memory_store

    async def run(self,params:SearchMemoryToolInput) -> str:
        '''
        Executes a seach query against the derived_memories table
        Returns a formatted string of results suitable for an LLM context
        '''
        try:
            conn = self.memory_store._get_conn()
            cursor = conn.cursor()

            query_sql = "SELECT content, timestamp FROM derived_memories WHERE content LIKE ? "
            query_params = [f"%{params.query}%"]

            if params.memory_type:
                query_sql += "AND memory_type = ? "
                query_params.append(params.memory_type)
            
            query_sql += "ORDER BY timestamp DESC LIMIT ?"
            query_params.append(str(params.limit))

            cursor.execute(query_sql,tuple(query_params))
            results = cursor.fetchall()

            if not results:
                return "No relevant memories found."
            
            formatted_results = [
                f"Memory from {row['timestamp']}:\n{row['content']}" for row in results
            ]
            return f"Found {len(results)} relevant memories:\n" + "\n".join(formatted_results)
        except sqlite3.Error as e:
            return f"Error: could not search memories to a database error: {e}"

class WriteMemoryTool:
    '''
    A tool for the writing new entires to the agent's memory
    '''
    def __init__(self,memory_store: MemoryStore):
        self.memory_store = memory_store

    async def run(self,params:WriteMemoryToolInput) -> str:
        '''
        Inserts a new record into the derived_memories table
        '''
        try:
            conn = self.memory_store._get_conn()
            cursor = conn.cursor()

            metadata_str = json.dumps(params.metadata) if params.metadata else None

            cursor.execute(
                """
                INSERT INTO derived_memories (session_id,content,memory_type,metadata_json)
                VALUES (?,?,?,?)
                """, (params.session_id,params.content,params.memory_type,metadata_str)
            )
            conn.commit()
            return 'Memory stored successfully'
        except sqlite3.Error as e:
            return f"Error: Could not store memory due to a database error : {e}"