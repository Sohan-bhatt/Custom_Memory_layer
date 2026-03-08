from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

memory_router = APIRouter(prefix="/memory", tags=["memory"])

class AddMemoryRequest(BaseModel):
    content: str
    role: Optional[str] = "user"
    metadata: Optional[Dict] = None

memory_manager = None

def set_memory_manager(manager):
    global memory_manager
    memory_manager = manager

@memory_router.post("/add")
async def add_memory(request: AddMemoryRequest):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    result = memory_manager.process_input(
        content=request.content,
        role=request.role or "user",
        metadata=request.metadata
    )
    
    return {
        "success": True,
        "data": result
    }

@memory_router.get("/retrieve")
async def retrieve_memory(query: str, memory_types: Optional[str] = None):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    types = memory_types.split(",") if memory_types else None
    results = memory_manager.retrieve(query, types)
    
    return {
        "success": True,
        "data": results
    }

@memory_router.get("/working")
async def get_working_memory():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    return {
        "success": True,
        "data": memory_manager.working_memory.get_all()
    }

@memory_router.post("/working/clear")
async def clear_working_memory():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    memory_manager.working_memory.clear()
    
    return {"success": True, "message": "Working memory cleared"}

@memory_router.get("/buffer")
async def get_buffer_memory(limit: int = 50):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    return {
        "success": True,
        "data": memory_manager.buffer_memory.get_all(limit)
    }

@memory_router.get("/episodic")
async def get_episodic_memory(limit: int = 100):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    return {
        "success": True,
        "data": memory_manager.episodic_memory.get_all(limit)
    }

@memory_router.get("/episodic/search")
async def search_episodic(query: str, top_k: int = 5):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    results = memory_manager.episodic_memory.search(query, top_k)
    
    return {
        "success": True,
        "data": results
    }

@memory_router.get("/procedural")
async def get_procedural_memory():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    return {
        "success": True,
        "data": memory_manager.procedural_memory.get_all()
    }

@memory_router.post("/clear")
async def clear_all_memory():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    memory_manager.clear_all()
    
    return {"success": True, "message": "All memory cleared"}

@memory_router.delete("/reset")
async def reset_database():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    memory_manager.clear_all()
    
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "memory_graph.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    from app.storage.database import init_db
    init_db()
    
    memory_manager.knowledge_graph.load_from_db()
    
    return {"success": True, "message": "Database reset - all memory deleted"}

@memory_router.post("/chat")
async def chat(request: AddMemoryRequest):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    from app.api.chat_service import chat_with_memory
    
    result = await chat_with_memory(request.content, memory_manager)
    
    return {
        "success": True,
        "data": result
    }
