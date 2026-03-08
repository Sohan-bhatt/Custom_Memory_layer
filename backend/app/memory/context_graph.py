from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import networkx as nx

class ContextGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_entity_node(self, entity_id: str, entity_name: str, entity_type: str, context: str = "") -> str:
        existing = None
        for node_id, data in self.graph.nodes(data=True):
            if data.get("entity_id") == entity_id:
                existing = node_id
                break
        
        if existing:
            return existing
        
        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        node_data = {
            "id": node_id,
            "entity_id": entity_id,
            "name": entity_name,
            "entity_type": entity_type,
            "context": context,
            "node_type": "entity",
            "created_at": now
        }
        
        self.graph.add_node(node_id, **node_data)
        
        return node_id
    
    def link_entities(self, source_entity_id: str, target_entity_id: str, relation_type: str, context: str = "", confidence: float = 0.8):
        source_node_id = None
        target_node_id = None
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get("entity_id") == source_entity_id:
                source_node_id = node_id
            if data.get("entity_id") == target_entity_id:
                target_node_id = node_id
        
        if source_node_id and target_node_id and source_node_id != target_node_id:
            self.graph.add_edge(
                source_node_id, 
                target_node_id, 
                link_type=relation_type,
                context=context,
                confidence=confidence,
                created_at=datetime.now().isoformat()
            )
    
    def get_all_nodes(self) -> List[Dict]:
        return [dict(data) for _, data in self.graph.nodes(data=True)]
    
    def get_all_edges(self) -> List[Dict]:
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": dict(self.graph.nodes[source]) if source in self.graph.nodes else {},
                "target": dict(self.graph.nodes[target]) if target in self.graph.nodes else {},
                "link_type": data.get("link_type", "related"),
                "context": data.get("context", ""),
                "confidence": data.get("confidence", 0.5),
                "created_at": data.get("created_at", "")
            })
        return edges
    
    def get_node_by_entity_id(self, entity_id: str) -> Optional[Dict]:
        for node_id, data in self.graph.nodes(data=True):
            if data.get("entity_id") == entity_id:
                return dict(data)
        return None
    
    def get_node_relations(self, node_id: str) -> List[Dict]:
        relations = []
        
        for _, target, data in self.graph.out_edges(node_id, data=True):
            relations.append({
                "direction": "outgoing",
                "target": dict(self.graph.nodes[target]) if target in self.graph.nodes else {},
                "link_type": data.get("link_type", "related"),
                "context": data.get("context", ""),
                "confidence": data.get("confidence", 0.5)
            })
        
        for source, _, data in self.graph.in_edges(node_id, data=True):
            relations.append({
                "direction": "incoming",
                "target": dict(self.graph.nodes[source]) if source in self.graph.nodes else {},
                "link_type": data.get("link_type", "related"),
                "context": data.get("context", ""),
                "confidence": data.get("confidence", 0.5)
            })
        
        return relations
    
    def to_visualization_data(self) -> Dict:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            color_map = {
                "entity": "#2196f3"
            }
            nodes.append({
                "id": node_id,
                "entity_id": data.get("entity_id"),
                "name": data.get("name", ""),
                "type": data.get("entity_type", node_type),
                "context": data.get("context", ""),
                "val": 15,
                "color": color_map.get(node_type, "#8b949e")
            })
        
        links = []
        for source, target, data in self.graph.edges(data=True):
            links.append({
                "source": source,
                "target": target,
                "type": data.get("link_type", "related"),
                "context": data.get("context", ""),
                "confidence": data.get("confidence", 0.5)
            })
        
        return {"nodes": nodes, "links": links}
    
    def clear(self):
        self.graph.clear()
