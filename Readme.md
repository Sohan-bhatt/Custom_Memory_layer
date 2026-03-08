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
│  │ Graph View  │  │ Chat Panel  │  │ Memory Details      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                         REST API
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
│  │  (NetworkX)      │  │     (Conversation Links)        │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (SQLite)                          │
│  - memory_graph.db                                        │
└─────────────────────────────────────────────────────────────┘
```

## 3. Memory Layers

### 3.1 Working Memory (Short-term)
- **Purpose**: Current conversation context
- **Capacity**: Last N messages (configurable, default: 10)
- **Storage**: In-memory deque + SQLite
- **TTL**: Cleared after conversation ends or timeout

### 3.2 Buffer Memory
- **Purpose**: Quick facts, recent interactions
- **Capacity**: Last 50 items
- **Storage**: SQLite table
- **Features**: FIFO eviction, timestamp-based

### 3.3 Episodic Memory
- **Purpose**: Past conversations, events
- **Storage**: SQLite + In-memory vector index
- **Retrieval**: Semantic similarity search
- **Metadata**: timestamps, session_id

### 3.4 Semantic Memory
- **Purpose**: Facts, preferences, knowledge about user/world
- **Storage**: Knowledge Graph (NetworkX) + SQLite
- **Structure**: Entities with attributes and relations
- **Operations**: Add entities, create relationships

### 3.5 Procedural Memory
- **Purpose**: Learned patterns, behaviors
- **Storage**: In-memory vector store + SQLite
- **Content**: Embeddings of patterns

## 4. Graph Systems

### 4.1 Knowledge Graph
```
Nodes: Entity
  - id: UUID
  - name: str
  - entity_type: str (person|place|concept|preference|company|skill)
  - properties: dict (includes source_message, why)
  - created_at: datetime
  - updated_at: datetime

Edges: Relationship
  - source_id: UUID
  - target_id: UUID
  - relation_type: str (knows, likes, lives_in, works_at, uses, related_to)
  - properties: dict (includes why, source_message, confidence)
  - confidence: float (0-1)
  - created_at: datetime
```

### 4.2 Context Graph
- **Purpose**: Shows conversational relationships between entities
- **Nodes**: Same entities as Knowledge Graph
- **Edges**: Conversational links (e.g., `conversational_likes`, `conversational_works_at`)
- **Context**: Each node stores the message context where it was mentioned

### 4.3 Decision Logic
- **Entity extraction**: AI Agent extracts entities from user messages
- **Relationship building**: Agent proposes relationships, validates against existing ones
- **Storage**: If no clear relationship → store in Episodic Memory (vector DB)

## 5. AI Agents

### Agent 1: Entity Extraction
- Extracts ONLY entities from user messages
- No relationships at this stage
- Types: person, place, concept, preference, company, skill

### Agent 2: Relationship Proposer
- Checks existing entities and relations
- Proposes NEW relationships only
- Validates against existing knowledge

### Agent 3: Entity Explainer (LLM)
- When user clicks "Explain with AI" on a node
- Queries LLM to explain what the entity means in the graph
- Shows neighbors and relationships

## 6. API Endpoints

### Memory Operations
```
POST /memory/add              - Add new memory
GET  /memory/working         - Get working memory
POST /memory/chat           - Chat with AI (with memory)
POST /memory/working/clear   - Clear working memory
DELETE /memory/reset        - Reset entire database
```

### Graph Operations
```
GET  /graph/visualize       - Get all graph data for visualization
GET  /graph/knowledge       - Get knowledge graph
POST /graph/entity          - Add entity
GET  /graph/entity/{id}    - Get entity details
DELETE /graph/entity/{id}  - Delete entity
POST /graph/relation       - Add relationship
GET  /graph/entity/{id}/explain - Explain entity using AI
```

## 7. Frontend Visualization

### Layout
- **Left Panel**: Graph visualization (full width minus side panel)
- **Right Panel**: Chat + Graph controls + Memory details
- **Header**: Graph selector (Knowledge/Context/Combined)

### Graph Features
- **Node labels**: Always visible (entity name inside, type below)
- **Edge labels**: Always visible (relationship type on the line)
- **Color coding**:
  - person: #e91e63
  - place: #9c27b0
  - concept: #2196f3
  - preference: #ff9800
  - company: #4caf50
- **Edge color**: Orange (#ff9800)
- **Interactions**:
  - Click node → Show details + "Explain with AI" button
  - Click edge → Show why relationship exists
  - Drag nodes → Reposition
  - Zoom/Pan → Navigate graph

### Real-time Updates
- Graph auto-refreshes every 3 seconds
- New entities appear immediately

## 8. Tech Stack

### Backend
- **Framework**: FastAPI
- **Graph**: NetworkX
- **Vector Store**: Simple in-memory numpy
- **Database**: SQLite
- **LLM**: OpenAI API (GPT-4o for extraction, GPT-3.5-turbo for chat)

### Frontend
- **Framework**: React + Vite
- **Graph**: react-force-graph-2d
- **State**: Zustand
- **Styling**: Inline CSS (dark theme)

## 9. Data Models

### SQLite Schema
```sql
-- Entities
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    properties TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Relations
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES entities(id),
    target_id TEXT REFERENCES entities(id),
    relation_type TEXT,
    properties TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP
);

-- Episodes (conversations)
CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding_id TEXT,
    metadata TEXT,
    created_at TIMESTAMP
);

-- Buffers
CREATE TABLE buffers (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    buffer_type TEXT,
    created_at TIMESTAMP
);

-- Working Memory
CREATE TABLE working_memory (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP
);
```

## 10. How It Works

1. **User sends message** in chat
2. **Agent 1** extracts entities (John, Google, Python)
3. **Agent 2** proposes relationships (John → works_at → Google, John → likes → Python)
4. **System checks** if relationships already exist
5. **Stores** in Knowledge Graph + Context Graph
6. **LLM responds** using retrieved context
7. **User sees** entities and relationships in graph
8. **Click node** → "Explain with AI" for LLM-powered explanation
9. **Click edge** → See why relationship was created

## 11. Key Features

- ✅ AI-powered entity extraction (no manual rules)
- ✅ Duplicate relationship prevention
- ✅ Entity explanation with LLM
- ✅ Edge reasoning visibility
- ✅ Knowledge Graph + Context Graph views
- ✅ Reset database functionality
- ✅ Dark theme visualization
- ✅ Always-visible labels (no hover required)
- ✅ Static graph (user controls positioning)

---

*This spec reflects the complete implementation of the memory graph system.*
