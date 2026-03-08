from typing import List, Dict, Any, Optional
from .working_memory import WorkingMemory
from .buffer_memory import BufferMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import KnowledgeGraph
from .procedural_memory import ProceduralMemory
from .context_graph import ContextGraph

class MemoryManager:
    def __init__(self):
        self.working_memory = WorkingMemory(max_items=10)
        self.buffer_memory = BufferMemory(max_items=50)
        self.episodic_memory = EpisodicMemory()
        self.knowledge_graph = KnowledgeGraph()
        self.procedural_memory = ProceduralMemory()
        self.context_graph = ContextGraph()
    
    def process_input(self, content: str, role: str = "user", metadata: Optional[Dict] = None) -> Dict:
        self.working_memory.add(content, role, metadata)
        
        message_id = self.context_graph.add_message_node(content, role, metadata)
        
        return {
            "content": content,
            "layers": ["working", "context_graph"],
            "message_id": message_id
        }
    
    def process_context_from_agent(self, topics: List[Dict], intents: List[Dict]):
        for topic in topics:
            topic_id = self.context_graph.add_topic_node(
                topic.get("name", ""),
                topic.get("confidence", 0.5)
            )
        
        for intent in intents:
            intent_id = self.context_graph.add_intent_node(
                intent.get("intent", ""),
                intent.get("entities", [])
            )
    
    def retrieve(self, query: str, memory_types: Optional[List[str]] = None) -> Dict:
        memory_types = memory_types or ["working", "buffer", "episodic", "knowledge_graph", "context_graph"]
        
        results = {}
        
        if "working" in memory_types:
            results["working"] = self.working_memory.get_recent(5)
        
        if "buffer" in memory_types:
            results["buffer"] = self.buffer_memory.get_recent(5)
        
        if "episodic" in memory_types:
            results["episodic"] = self.episodic_memory.search(query, top_k=5)
        
        if "knowledge_graph" in memory_types:
            results["knowledge_graph"] = self.knowledge_graph.search(query)
        
        if "procedural" in memory_types:
            results["procedural"] = self.procedural_memory.search(query, top_k=5)
        
        if "context_graph" in memory_types:
            results["context_graph"] = {
                "messages": self.context_graph.get_recent_messages(5),
                "topics": self.context_graph.get_topics(),
                "flow": self.context_graph.get_conversation_flow()
            }
        
        return results
    
    def get_visualization_data(self) -> Dict:
        kg_data = self.knowledge_graph.to_visualization_data()
        cg_data = self.context_graph.to_visualization_data()
        
        return {
            "knowledge_graph": kg_data,
            "context_graph": cg_data,
            "combined": {
                "nodes": kg_data["nodes"] + cg_data["nodes"],
                "links": kg_data["links"] + cg_data["links"]
            },
            "stats": {
                "working_memory_count": len(self.working_memory.get_all()),
                "buffer_count": len(self.buffer_memory.get_all()),
                "episodic_count": len(self.episodic_memory.get_all()),
                "knowledge_graph_entities": len(kg_data["nodes"]),
                "knowledge_graph_relations": len(kg_data["links"]),
                "context_graph_nodes": len(cg_data["nodes"]),
                "context_graph_links": len(cg_data["links"]),
                "procedural_count": len(self.procedural_memory.get_all()),
            }
        }
    
    def clear_all(self):
        self.working_memory.clear()
        self.buffer_memory.clear()
        self.episodic_memory.clear()
        self.procedural_memory.clear()
        self.context_graph.clear()
