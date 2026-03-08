from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
from ..storage.database import get_db

class BufferMemory:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
    
    def add(self, content: str, buffer_type: str = "fact", metadata: Optional[Dict] = None):
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO buffers (id, content, buffer_type, created_at) VALUES (?, ?, ?, ?)",
            (item_id, content, buffer_type, now)
        )
        
        cursor.execute("SELECT COUNT(*) FROM buffers")
        count = cursor.fetchone()[0]
        
        if count > self.max_items:
            cursor.execute(
                "DELETE FROM buffers WHERE id IN (SELECT id FROM buffers ORDER BY created_at ASC LIMIT ?)",
                (count - self.max_items,)
            )
        
        conn.commit()
        conn.close()
        
        return {"id": item_id, "content": content, "buffer_type": buffer_type, "created_at": now}
    
    def get_all(self, limit: int = 50) -> List[Dict]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buffers ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_recent(self, n: int = 10) -> List[Dict]:
        return self.get_all(n)
    
    def clear(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM buffers")
        conn.commit()
        conn.close()
