from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import networkx as nx
from ..storage.database import get_db

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_entity(self, name: str, entity_type: str, properties: Optional[Dict] = None) -> Dict:
        entity_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        entity_data = {
            "id": entity_id,
            "name": name,
            "entity_type": entity_type,
            "properties": properties or {},
            "created_at": now,
            "updated_at": now
        }
        
        self.graph.add_node(entity_id, **entity_data)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entities (id, name, entity_type, properties, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, name, entity_type, str(properties), now, now)
        )
        conn.commit()
        conn.close()
        
        return entity_data
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str, 
                     properties: Optional[Dict] = None, confidence: float = 1.0) -> Dict:
        if source_id not in self.graph or target_id not in self.graph:
            raise ValueError("Source or target entity not found")
        
        relation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        relation_data = {
            "id": relation_id,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            "properties": properties or {},
            "confidence": confidence,
            "created_at": now
        }
        
        self.graph.add_edge(source_id, target_id, **relation_data)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO relations (id, source_id, target_id, relation_type, properties, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (relation_id, source_id, target_id, relation_type, str(properties), confidence, now)
        )
        conn.commit()
        conn.close()
        
        return relation_data
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        if entity_id in self.graph.nodes:
            return dict(self.graph.nodes[entity_id])
        return None
    
    def get_all_entities(self) -> List[Dict]:
        return [dict(self.graph.nodes[node]) for node in self.graph.nodes]
    
    def get_all_relations(self) -> List[Dict]:
        relations = []
        for source, target, data in self.graph.edges(data=True):
            relations.append({
                "source": source,
                "target": target,
                **data
            })
        return relations
    
    def get_neighbors(self, entity_id: str) -> List[Dict]:
        if entity_id not in self.graph:
            return []
        
        neighbors = []
        for neighbor in self.graph.neighbors(entity_id):
            neighbors.append(dict(self.graph.nodes[neighbor]))
        return neighbors
    
    def get_entity_relations(self, entity_id: str) -> List[Dict]:
        if entity_id not in self.graph:
            return []
        
        relations = []
        for source, target, data in self.graph.edges(data=True):
            if source == entity_id or target == entity_id:
                relations.append({
                    "source": source,
                    "target": target,
                    **data
                })
        return relations
    
    def delete_entity(self, entity_id: str):
        if entity_id in self.graph:
            self.graph.remove_node(entity_id)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
        cursor.execute("DELETE FROM relations WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
        conn.commit()
        conn.close()
    
    def search(self, query: str) -> List[Dict]:
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if query.lower() in data.get("name", "").lower():
                results.append(dict(data))
        return results
    
    def to_visualization_data(self) -> Dict:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": data.get("name"),
                "type": data.get("entity_type"),
                "val": 1
            })
        
        links = []
        for source, target, data in self.graph.edges(data=True):
            links.append({
                "source": source,
                "target": target,
                "type": data.get("relation_type"),
                "strength": data.get("confidence", 1.0)
            })
        
        return {"nodes": nodes, "links": links}
    
    def load_from_db(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM entities")
        rows = cursor.fetchall()
        for row in rows:
            entity = dict(row)
            properties = entity.pop("properties", "{}")
            if isinstance(properties, str):
                import json
                try:
                    properties = json.loads(properties)
                except:
                    properties = {}
            entity["properties"] = properties
            self.graph.add_node(entity["id"], **entity)
        
        cursor.execute("SELECT * FROM relations")
        rows = cursor.fetchall()
        for row in rows:
            relation = dict(row)
            properties = relation.pop("properties", "{}")
            if isinstance(properties, str):
                import json
                try:
                    properties = json.loads(properties)
                except:
                    properties = {}
            relation["properties"] = properties
            self.graph.add_edge(relation["source_id"], relation["target_id"], **relation)
        
        conn.close()
