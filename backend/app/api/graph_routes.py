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

@graph_router.get("/entity/{entity_id}/explain")
async def explain_entity(entity_id: str):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    data = memory_manager.get_entity_for_explanation(entity_id)
    if not data:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = data["entity"]
    relations = data["relations"]
    neighbors = data["neighbors"]
    
    relations_str = ""
    for r in relations[:5]:
        source = r.get("source", "")
        target = r.get("target", "")
        rel_type = r.get("relation_type", "related")
        relations_str += f"- {source} --[{rel_type}]--> {target}\n"
    
    neighbors_str = ", ".join([n.get("name", "") for n in neighbors[:5]])
    
    from openai import OpenAI
    import os
    from pathlib import Path
    
    app_dir = Path(__file__).resolve().parents[1]
    backend_dir = app_dir.parent
    from dotenv import load_dotenv
    load_dotenv(app_dir / ".env")
    load_dotenv(backend_dir / ".env")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""You are a knowledge graph explainer. Explain what this entity means in the graph.

Entity: {entity.get("name")} (type: {entity.get("entity_type")})

Connected to: {neighbors_str}

Relationships:
{relations_str}

Provide a clear, concise explanation (2-3 sentences) about who/what this entity is and how it connects to others in the graph."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        explanation = response.choices[0].message.content
    except Exception as e:
        explanation = f"This entity connects to: {neighbors_str}. {str(e)}"
    
    return {
        "success": True,
        "data": {
            "entity": entity,
            "neighbors": neighbors,
            "relations": relations,
            "explanation": explanation
        }
    }
