from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import numpy as np
from ..storage.database import get_db

class ProceduralMemory:
    def __init__(self):
        self.vectors = []
        self.metadata = []
    
    def _generate_mock_embedding(self, pattern: str) -> np.ndarray:
        np.random.seed(hash(pattern) % (2**32))
        return np.random.randn(384)
    
    def add(self, pattern: str, metadata: Optional[Dict] = None):
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        metadata = metadata or {}
        metadata["id"] = item_id
        metadata["pattern"] = pattern
        metadata["created_at"] = now
        
        embedding = self._generate_mock_embedding(pattern)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO procedural_memories (id, pattern, embedding_id, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, pattern, item_id, str(metadata), now)
        )
        conn.commit()
        conn.close()
        
        self.vectors.append(embedding)
        self.metadata.append(metadata)
        
        return {"id": item_id, "pattern": pattern, "created_at": now}
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.vectors:
            return []
        
        query_embedding = self._generate_mock_embedding(query)
        vectors = np.array(self.vectors)
        
        similarities = np.dot(vectors, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.metadata[i] for i in top_indices if i < len(self.metadata)]
    
    def get_all(self) -> List[Dict]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procedural_memories ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete(self, pattern_id: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM procedural_memories WHERE id = ?", (pattern_id,))
        conn.commit()
        conn.close()
    
    def clear(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM procedural_memories")
        conn.commit()
        conn.close()
        self.vectors = []
        self.metadata = []
