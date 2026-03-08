from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from ..storage.database import get_db

class WorkingMemory:
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self._memory = deque(maxlen=max_items)
    
    def add(self, content: str, role: str = "user", metadata: Optional[Dict] = None):
        item = {
            "id": str(uuid.uuid4()),
            "content": content,
            "role": role,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        self._memory.append(item)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO working_memory (id, content, role, created_at) VALUES (?, ?, ?, ?)",
            (item["id"], item["content"], item["role"], item["created_at"])
        )
        conn.commit()
        conn.close()
        
        return item
    
    def get_all(self) -> List[Dict]:
        return list(self._memory)
    
    def get_recent(self, n: int = 5) -> List[Dict]:
        return list(self._memory)[-n:]
    
    def clear(self):
        self._memory.clear()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM working_memory")
        conn.commit()
        conn.close()
    
    def load_from_db(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM working_memory ORDER BY created_at DESC LIMIT ?", (self.max_items,))
        rows = cursor.fetchall()
        conn.close()
        self._memory.clear()
        for row in rows:
            self._memory.append(dict(row))
