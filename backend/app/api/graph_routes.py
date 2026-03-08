from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

graph_router = APIRouter(prefix="/graph", tags=["graph"])

memory_manager = None

def set_memory_manager(manager):
    global memory_manager
    memory_manager = manager

class AddEntityRequest(BaseModel):
    name: str
    entity_type: str
    properties: Optional[Dict] = None

class AddRelationRequest(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    properties: Optional[Dict] = None
    confidence: float = 1.0

@graph_router.get("/knowledge")
async def get_knowledge_graph():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    entities = memory_manager.knowledge_graph.get_all_entities()
    relations = memory_manager.knowledge_graph.get_all_relations()
    
    return {
        "success": True,
        "data": {
            "entities": entities,
            "relations": relations
        }
    }

@graph_router.get("/visualize")
async def visualize_graph():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    return {
        "success": True,
        "data": memory_manager.get_visualization_data()
    }

@graph_router.post("/entity")
async def add_entity(request: AddEntityRequest):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        entity = memory_manager.knowledge_graph.add_entity(
            name=request.name,
            entity_type=request.entity_type,
            properties=request.properties
        )
        
        return {
            "success": True,
            "data": entity
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@graph_router.get("/entity/{entity_id}")
async def get_entity(entity_id: str):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    entity = memory_manager.knowledge_graph.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    relations = memory_manager.knowledge_graph.get_entity_relations(entity_id)
    
    return {
        "success": True,
        "data": {
            "entity": entity,
            "relations": relations
        }
    }

@graph_router.delete("/entity/{entity_id}")
async def delete_entity(entity_id: str):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    memory_manager.knowledge_graph.delete_entity(entity_id)
    
    return {
        "success": True,
        "message": "Entity deleted"
    }

@graph_router.post("/relation")
async def add_relation(request: AddRelationRequest):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        relation = memory_manager.knowledge_graph.add_relation(
            source_id=request.source_id,
            target_id=request.target_id,
            relation_type=request.relation_type,
            properties=request.properties,
            confidence=request.confidence
        )
        
        return {
            "success": True,
            "data": relation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@graph_router.get("/entity/{entity_id}/neighbors")
async def get_neighbors(entity_id: str):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    neighbors = memory_manager.knowledge_graph.get_neighbors(entity_id)
    
    return {
        "success": True,
        "data": neighbors
    }
