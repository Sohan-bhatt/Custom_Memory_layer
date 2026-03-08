from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.storage.database import init_db
from app.memory.manager import MemoryManager
from app.api.memory_routes import memory_router, set_memory_manager as set_memory_router_manager
from app.api.graph_routes import graph_router, set_memory_manager as set_graph_router_manager

app = FastAPI(title="Memory Graph API", description="AI Memory System with Knowledge Graph")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_manager = None

@app.on_event("startup")
async def startup_event():
    global memory_manager
    
    init_db()
    
    memory_manager = MemoryManager()
    memory_manager.knowledge_graph.load_from_db()
    memory_manager.working_memory.load_from_db()
    
    set_memory_router_manager(memory_manager)
    set_graph_router_manager(memory_manager)

@app.get("/")
async def root():
    return {
        "message": "Memory Graph API",
        "version": "1.0.0",
        "endpoints": {
            "memory": "/memory",
            "graph": "/graph"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(memory_router)
app.include_router(graph_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
