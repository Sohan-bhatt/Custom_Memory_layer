from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import networkx as nx

class ContextGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_message_node(self, content: str, role: str = "user", metadata: Optional[Dict] = None) -> str:
        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        node_data = {
            "id": node_id,
            "name": content[:60] if content else "",
            "content": content,
            "role": role,
            "metadata": metadata or {},
            "node_type": "message",
            "created_at": now
        }

        previous_messages = [
            (nid, data) for nid, data in self.graph.nodes(data=True)
            if data.get("node_type") == "message"
        ]
        previous_messages.sort(key=lambda item: item[1].get("created_at", ""))

        self.graph.add_node(node_id, **node_data)

        if previous_messages:
            prev_id = previous_messages[-1][0]
            self.graph.add_edge(prev_id, node_id, link_type="next", strength=1.0)

        return node_id
    
    def add_topic_node(self, topic: str, confidence: float = 1.0) -> str:
        existing = None
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "topic" and data.get("name", "").lower() == topic.lower():
                existing = node_id
                break
        
        if existing:
            return existing
        
        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        node_data = {
            "id": node_id,
            "name": topic,
            "node_type": "topic",
            "confidence": confidence,
            "created_at": now
        }
        
        self.graph.add_node(node_id, **node_data)
        
        return node_id
    
    def add_intent_node(self, intent: str, entities: List[str]) -> str:
        existing = None
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "intent" and data.get("intent", "").lower() == intent.lower():
                existing = node_id
                break
        
        if existing:
            return existing
        
        node_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        node_data = {
            "id": node_id,
            "intent": intent,
            "entities": entities,
            "node_type": "intent",
            "created_at": now
        }
        
        self.graph.add_node(node_id, **node_data)
        
        return node_id
    
    def link_topics(self, topic1_id: str, topic2_id: str):
        self.graph.add_edge(topic1_id, topic2_id, link_type="related_to", strength=0.5)
    
    def get_topics(self) -> List[Dict]:
        topics = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "topic":
                topics.append(dict(data))
        return topics
    
    def get_intents(self) -> List[Dict]:
        intents = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("node_type") == "intent":
                intents.append(dict(data))
        return intents

    def get_recent_messages(self, limit: int = 5) -> List[Dict]:
        messages = [
            dict(data) for _, data in self.graph.nodes(data=True)
            if data.get("node_type") == "message"
        ]
        messages.sort(key=lambda item: item.get("created_at", ""))
        return messages[-limit:]

    def get_conversation_flow(self) -> List[Dict]:
        flow = []
        for source, target, data in self.graph.edges(data=True):
            if data.get("link_type") == "next":
                flow.append({
                    "source": source,
                    "target": target,
                    "type": "next",
                    "strength": data.get("strength", 1.0)
                })
        return flow
    
    def to_visualization_data(self) -> Dict:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            color_map = {
                "topic": "#f78166",
                "intent": "#7ee787",
                "message": "#607d8b"
            }
            nodes.append({
                "id": node_id,
                "name": data.get("name") or data.get("intent", ""),
                "type": node_type,
                "val": 3,
                "color": color_map.get(node_type, "#8b949e")
            })
        
        links = []
        for source, target, data in self.graph.edges(data=True):
            links.append({
                "source": source,
                "target": target,
                "type": data.get("link_type", "related"),
                "strength": data.get("strength", 0.5)
            })
        
        return {"nodes": nodes, "links": links}
    
    def clear(self):
        self.graph.clear()
