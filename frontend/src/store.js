import { create } from 'zustand'

const API_BASE = 'http://localhost:8000'

export const useStore = create((set, get) => ({
  knowledgeGraph: { nodes: [], links: [] },
  contextGraph: { nodes: [], links: [] },
  combinedGraph: { nodes: [], links: [] },
  stats: {},
  workingMemory: [],
  bufferMemory: [],
  episodicMemory: [],
  selectedNode: null,
  isLoading: false,
  activeGraph: 'combined',
  
  fetchGraphData: async () => {
    set({ isLoading: true })
    try {
      const res = await fetch(`${API_BASE}/graph/visualize`)
      const data = await res.json()
      if (data.success) {
        const kg = data.data.knowledge_graph
        const cg = data.data.context_graph
        const combined = data.data.combined
        
        set({
          knowledgeGraph: {
            nodes: kg.nodes.map(n => ({ ...n, id: n.id })),
            links: kg.links.map(l => ({ ...l, id: `${l.source}-${l.target}` }))
          },
          contextGraph: {
            nodes: cg.nodes.map(n => ({ ...n, id: n.id })),
            links: cg.links.map(l => ({ ...l, id: `${l.source}-${l.target}` }))
          },
          combinedGraph: {
            nodes: combined.nodes.map(n => ({ ...n, id: n.id })),
            links: combined.links.map(l => ({ ...l, id: `${l.source}-${l.target}` }))
          },
          stats: data.data.stats
        })
      }
    } catch (e) {
      console.error('Failed to fetch graph:', e)
    }
    set({ isLoading: false })
  },

  setActiveGraph: (graph) => set({ activeGraph: graph }),

  getCurrentGraphData: () => {
    const state = get()
    if (state.activeGraph === 'knowledge') return state.knowledgeGraph
    if (state.activeGraph === 'context') return state.contextGraph
    return state.combinedGraph
  },
  
  addMemory: async (content, role = 'user') => {
    try {
      const res = await fetch(`${API_BASE}/memory/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, role })
      })
      const data = await res.json()
      if (data.success) {
        get().fetchGraphData()
        get().fetchWorkingMemory()
      }
      return data
    } catch (e) {
      console.error('Failed to add memory:', e)
    }
  },

  fetchWorkingMemory: async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/working`)
      const data = await res.json()
      if (data.success) {
        set({ workingMemory: data.data })
      }
    } catch (e) {
      console.error('Failed to fetch working memory:', e)
    }
  },

  fetchBufferMemory: async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/buffer`)
      const data = await res.json()
      if (data.success) {
        set({ bufferMemory: data.data })
      }
    } catch (e) {
      console.error('Failed to fetch buffer memory:', e)
    }
  },

  fetchEpisodicMemory: async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/episodic`)
      const data = await res.json()
      if (data.success) {
        set({ episodicMemory: data.data })
      }
    } catch (e) {
      console.error('Failed to fetch episodic memory:', e)
    }
  },

  addEntity: async (name, entityType, properties = {}) => {
    try {
      const res = await fetch(`${API_BASE}/graph/entity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, entity_type: entityType, properties })
      })
      const data = await res.json()
      if (data.success) {
        get().fetchGraphData()
      }
      return data
    } catch (e) {
      console.error('Failed to add entity:', e)
    }
  },

  addRelation: async (sourceId, targetId, relationType) => {
    try {
      const res = await fetch(`${API_BASE}/graph/relation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_id: sourceId, target_id: targetId, relation_type: relationType })
      })
      const data = await res.json()
      if (data.success) {
        get().fetchGraphData()
      }
      return data
    } catch (e) {
      console.error('Failed to add relation:', e)
    }
  },

  clearWorkingMemory: async () => {
    try {
      await fetch(`${API_BASE}/memory/working/clear`, { method: 'POST' })
      get().fetchWorkingMemory()
    } catch (e) {
      console.error('Failed to clear working memory:', e)
    }
  },

  resetDatabase: async () => {
    try {
      const res = await fetch(`${API_BASE}/memory/reset`, { method: 'DELETE' })
      const data = await res.json()
      if (data.success) {
        get().fetchGraphData()
        get().fetchWorkingMemory()
        set({ selectedNode: null })
      }
      return data
    } catch (e) {
      console.error('Failed to reset database:', e)
    }
  },

  setSelectedNode: (node) => set({ selectedNode: node }),

  fetchEntityRelations: async (entityId) => {
    try {
      const res = await fetch(`${API_BASE}/graph/entity/${entityId}`)
      const data = await res.json()
      if (data.success) {
        return data.data
      }
      return null
    } catch (e) {
      console.error('Failed to fetch entity relations:', e)
      return null
    }
  },
}))
