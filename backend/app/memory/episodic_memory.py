from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import numpy as np
from ..storage.database import get_db

class VectorStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectors = []
        self.metadata = []
    
    def add(self, vector: np.ndarray, metadata: Dict):
        if len(vector) != self.dimension:
            vector = np.random.randn(self.dimension)
        
        self.vectors.append(vector)
        self.metadata.append(metadata)
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict]:
        if not self.vectors:
            return []
        
        query_vector = query_vector.reshape(1, -1)
        vectors = np.array(self.vectors)
        
        similarities = np.dot(vectors, query_vector.T).flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.metadata[i] for i in top_indices]
    
    def delete(self, idx: int):
        if 0 <= idx < len(self.vectors):
            self.vectors.pop(idx)
            self.metadata.pop(idx)

class EpisodicMemory:
    def __init__(self):
        self.vector_store = VectorStore()
    
    def _generate_mock_embedding(self, content: str) -> np.ndarray:
        np.random.seed(hash(content) % (2**32))
        return np.random.randn(self.dimension)
    
    @property
    def dimension(self):
        return self.vector_store.dimension
    
    def add(self, content: str, metadata: Optional[Dict] = None):
        item_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        metadata = metadata or {}
        metadata["id"] = item_id
        metadata["content"] = content
        metadata["created_at"] = now
        
        embedding = self._generate_mock_embedding(content)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO episodes (id, content, embedding_id, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (item_id, content, item_id, str(metadata), now)
        )
        conn.commit()
        conn.close()
        
        self.vector_store.add(embedding, metadata)
        
        return {"id": item_id, "content": content, "created_at": now}
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self._generate_mock_embedding(query)
        return self.vector_store.search(query_embedding, top_k)
    
    def get_all(self, limit: int = 100) -> List[Dict]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM episodes ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete(self, episode_id: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
        conn.commit()
        conn.close()
    
    def clear(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM episodes")
        conn.commit()
        conn.close()
        self.vector_store = VectorStore()
