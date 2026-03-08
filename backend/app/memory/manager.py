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
    
    def add_entity_to_context_graph(self, entity_id: str, entity_name: str, entity_type: str, context: str = ""):
        return self.context_graph.add_entity_node(entity_id, entity_name, entity_type, context)
    
    def link_entities_in_context(self, source_entity_id: str, target_entity_id: str, relation_type: str, context: str = ""):
        self.context_graph.link_entities(source_entity_id, target_entity_id, relation_type, context)
    
    def process_input(self, content: str, role: str = "user", metadata: Optional[Dict] = None) -> Dict:
        self.working_memory.add(content, role, metadata)
        
        return {
            "content": content,
            "layers": ["working", "context_graph"]
        }
    
    def process_context_from_agent(self, topics: List[Dict], intents: List[Dict], entities: List[Dict] = None):
        if entities:
            for entity in entities:
                self.context_graph.add_entity_node(
                    entity.get("id", ""),
                    entity.get("name", ""),
                    entity.get("entity_type", "concept"),
                    entity.get("properties", {}).get("source_message", "")[:100]
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
                "nodes": self.context_graph.get_all_nodes(),
                "edges": self.context_graph.get_all_edges()
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
    
    def get_entity_for_explanation(self, entity_id: str) -> Optional[Dict]:
        entity = self.knowledge_graph.get_entity(entity_id)
        if entity:
            relations = self.knowledge_graph.get_entity_relations(entity_id)
            neighbors = self.knowledge_graph.get_neighbors(entity_id)
            return {
                "entity": entity,
                "relations": relations,
                "neighbors": neighbors
            }
        return None
    
    def clear_all(self):
        self.working_memory.clear()
        self.buffer_memory.clear()
        self.episodic_memory.clear()
        self.procedural_memory.clear()
        self.context_graph.clear()
