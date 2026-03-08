# Memory Graph System - Technical Specification

## 1. System Overview

A personal AI memory system inspired by Letta/Zep/Mem0 that manages multiple memory layers with dual storage:
- **Structured Memory**: Knowledge Graph + Context Graph (for entity-rich conversations)
- **Unstructured Memory**: Vector-based storage (for messy/natural conversations)
- **Visualization**: Real-time interactive graph showing memory formation

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Graph View  │  │ Memory Panel│  │ Timeline/History    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                         WebSocket + REST
                              │
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Memory Engine                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │    │
│  │  │ Working  │ │ Semantic │ │Episodic  │ │Buffer │  │    │
│  │  │ Memory   │ │ Memory   │ │ Memory   │ │Memory │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │  Knowledge Graph │  │     Context Graph               │  │
│  │  (NetworkX)      │  │     (Conversation State)        │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Vector Store (FAISS/In-Memory)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (SQLite)                          │
│  - memories.db (all memory layers)                         │
└─────────────────────────────────────────────────────────────┘
```

## 3. Memory Layers

### 3.1 Working Memory (Short-term)
- **Purpose**: Current conversation context
- **Capacity**: Last N messages (configurable, default: 10)
- **Storage**: In-memory deque
- **TTL**: Cleared after conversation ends or timeout

### 3.2 Buffer Memory
- **Purpose**: Quick facts, recent interactions
- **Capacity**: Last 50 items
- **Storage**: SQLite table
- **Features**: FIFO eviction, timestamp-based

### 3.3 Episodic Memory
- **Purpose**: Past conversations, events
- **Storage**: SQLite + Vector index
- **Retrieval**: Hybrid (keyword + semantic similarity)
- **Metadata**: timestamps, session_id, sentiment

### 3.4 Semantic Memory
- **Purpose**: Facts, preferences, knowledge about user/world
- **Storage**: Knowledge Graph (NetworkX) + SQLite
- **Structure**: Entities with attributes and relations
- **Operations**: Merge, update, infer

### 3.5 Procedural Memory
- **Purpose**: Learned patterns, behaviors, embeddings
- **Storage**: Vector store + SQLite
- **Content**: Embeddings of patterns, routines

## 4. Graph Systems

### 4.1 Knowledge Graph
```
Nodes: Entity (person, place, concept, preference)
  - id: UUID
  - type: str (person|place|concept|preference|preference_category)
  - name: str
  - properties: dict
  - created_at: datetime
  - updated_at: datetime

Edges: Relationship
  - source_id: UUID
  - target_id: UUID
  - relation_type: str (knows, likes, located_at, part_of, etc.)
  - properties: dict
  - confidence: float (0-1)
  - created_at: datetime
```

### 4.2 Context Graph
```
Nodes: ConversationElement
  - id: UUID
  - type: (message|entity|intent|topic)
  - content: str
  - metadata: dict

Edges: ContextLink
  - source_id: UUID
  - target_id: UUID
  - link_type: (refers_to|related_to|causes|implies)
  - strength: float (0-1)
```

### 4.3 Decision Logic
- **Entity-rich input** → Parse entities → Store in Knowledge/Context Graph
- **Messy/natural input** → Embed → Store in Vector DB (Episodic)
- **Hybrid**: Store in both if content has both structured and unstructured elements

## 5. API Endpoints

### Memory Operations
```
POST /memory/add              - Add new memory
GET  /memory/retrieve         - Retrieve by query (hybrid)
GET  /memory/search           - Semantic search
POST /memory/delete           - Delete memory
GET  /memory/list             - List all memories
```

### Graph Operations
```
GET  /graph/knowledge         - Get knowledge graph
GET  /graph/context          - Get context graph
POST /graph/entity            - Add entity
POST /graph/relation          - Add relation
GET  /graph/entity/{id}       - Get entity details
DELETE /graph/entity/{id}     - Delete entity
```

### Visualization
```
GET  /graph/visualize         - Get graph data for visualization
WS   /ws/graph-updates        - Real-time graph updates
```

## 6. Frontend Visualization

### Layout
- **Left Panel**: Graph visualization (60% width)
- **Right Panel**: Memory details, entity inspector (40% width)
- **Bottom Bar**: Quick actions, recent memories

### Graph View Features
- Force-directed layout (react-force-graph-2d)
- Node types with distinct colors/shapes
- Zoom, pan, drag nodes
- Click to expand details
- Filter by node type, date
- Hierarchical clustering option

### Real-time Updates
- WebSocket connection for live graph changes
- Animated node additions
- Highlight new connections

## 7. Tech Stack

### Backend
- **Framework**: FastAPI
- **Graph**: NetworkX
- **Vector Store**: FAISS (or simple numpy for MVP)
- **Database**: SQLite (via SQLAlchemy)
- **Embedding**: sentence-transformers (all-MiniLM-L6-v2)
- **NLP**: spaCy or regex for entity extraction

### Frontend
- **Framework**: React + Vite
- **Graph**: react-force-graph-2d
- **State**: Zustand
- **Styling**: Tailwind CSS
- **WebSocket**: native WebSocket API

## 8. Data Models

### SQLite Schema
```sql
-- Entities
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    properties JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Relations
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES entities(id),
    target_id TEXT REFERENCES entities(id),
    relation_type TEXT,
    properties JSON,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP
);

-- Episodes (conversations)
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB,
    metadata JSON,
    created_at TIMESTAMP
);

-- Buffers
CREATE TABLE buffers (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    buffer_type TEXT,
    created_at TIMESTAMP
);
```

## 9. Implementation Priority

1. **Phase 1**: Core infrastructure (FastAPI + SQLite + basic memory classes)
2. **Phase 2**: Knowledge Graph with entity extraction
3. **Phase 3**: Vector store integration for episodic memory
4. **Phase 4**: Context Graph for conversation state
5. **Phase 5**: React frontend with visualization
6. **Phase 6**: Real-time WebSocket updates
7. **Phase 7**: Polish and optimizations

## 10. Key Design Decisions

- **Local-first**: All data stored locally (SQLite)
- **Hybrid storage**: Graph for structured, vectors for unstructured
- **Entity detection**: Rule-based + embedding similarity for mess detection
- **No LLM required**: Can work standalone (optional: integrate for entity extraction)
- **Real-time viz**: WebSocket for live graph updates

---

*This spec provides a complete blueprint for building a personal memory graph system with visualization.*
