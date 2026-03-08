import React, { useEffect, useState, useRef, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useStore } from './store'

const API_BASE = 'http://localhost:8000'

const nodeColors = {
  person: '#e91e63',
  place: '#9c27b0',
  concept: '#2196f3',
  preference: '#ff9800',
  company: '#4caf50',
  message: '#607d8b',
  topic: '#00bcd4',
  intent: '#ff5722',
  default: '#9e9e9e'
}

function App() {
  const { 
    knowledgeGraph,
    contextGraph,
    combinedGraph,
    stats,
    workingMemory,
    fetchGraphData, 
    fetchWorkingMemory,
    addEntity,
    clearWorkingMemory,
    resetDatabase,
    setSelectedNode,
    selectedNode,
    activeGraph,
    setActiveGraph,
    getCurrentGraphData,
    fetchEntityRelations
  } = useStore()

  const [input, setInput] = useState('')
  const [entityName, setEntityName] = useState('')
  const [entityType, setEntityType] = useState('person')
  const [activeTab, setActiveTab] = useState('chat')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [nodeDetails, setNodeDetails] = useState(null)
  const [linkDetails, setLinkDetails] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showDetails, setShowDetails] = useState(true)
  const graphRef = useRef()
  const chatEndRef = useRef()

  const graphData = getCurrentGraphData()

  useEffect(() => {
    fetchGraphData()
    fetchWorkingMemory()
    const interval = setInterval(fetchGraphData, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!graphRef.current) return

    const chargeForce = graphRef.current.d3Force('charge')
    if (chargeForce?.strength) {
      chargeForce.strength(-260)
    }

    const linkForce = graphRef.current.d3Force('link')
    if (linkForce?.distance && linkForce?.strength) {
      linkForce.distance(140)
      linkForce.strength(0.9)
    }

    graphRef.current.d3ReheatSimulation()
  }, [graphData.nodes.length, graphData.links.length, showDetails])

  const handleChat = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input
    setInput('')
    setIsLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const res = await fetch(`${API_BASE}/memory/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: userMessage, role: 'user' })
      })
      const data = await res.json()
      
      if (data.success) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.data.assistant_message,
          memoryInfo: data.data.memory_layers_updated
        }])
        setLastUpdate({
          time: new Date().toLocaleTimeString(),
          layers: data.data.memory_layers_updated
        })
        fetchGraphData()
        fetchWorkingMemory()
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + err.message }])
    }

    setIsLoading(false)
  }

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
    setNodeDetails(node)
    setLinkDetails(null)
  }, [])

  const handleLinkClick = useCallback((link) => {
    setLinkDetails(link)
    setNodeDetails(null)
  }, [])

  const filteredNodes = searchQuery 
    ? graphData.nodes.filter(n => n.name?.toLowerCase().includes(searchQuery.toLowerCase()))
    : graphData.nodes
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id))
  const visibleLinks = graphData.links.filter((link) => {
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source
    const targetId = typeof link.target === 'object' ? link.target.id : link.target
    return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId)
  })

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>🧠 Memory Graph</h1>
          <div style={styles.graphSelector}>
            <button 
              style={{...styles.graphBtn, ...(activeGraph === 'knowledge' ? styles.activeGraphBtn : {})}}
              onClick={() => setActiveGraph('knowledge')}
            >
              Knowledge Graph
            </button>
            <button 
              style={{...styles.graphBtn, ...(activeGraph === 'context' ? styles.activeGraphBtn : {})}}
              onClick={() => setActiveGraph('context')}
            >
              Context Graph
            </button>
            <button 
              style={{...styles.graphBtn, ...(activeGraph === 'combined' ? styles.activeGraphBtn : {})}}
              onClick={() => setActiveGraph('combined')}
            >
              Combined
            </button>
          </div>
        </div>
        <div style={styles.stats}>
          <span style={styles.statItem}>Nodes: {graphData.nodes.length}</span>
          <span style={styles.statItem}>Relations: {graphData.links.length}</span>
          {lastUpdate && <span style={{color: '#4caf50'}}>Last update: {lastUpdate.time}</span>}
        </div>
      </header>

      <div style={styles.main}>
        <div style={styles.graphPanel}>
          <div style={styles.graphToolbar}>
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={styles.searchInput}
            />
            <button 
              style={styles.iconBtn}
              onClick={() => graphRef.current?.zoomToFit(500)}
              title="Fit to screen"
            >
              ⊙
            </button>
            <button 
              style={styles.iconBtn}
              onClick={() => setShowDetails(!showDetails)}
              title="Toggle details panel"
            >
              ☰
            </button>
          </div>
          
          <ForceGraph2D
            ref={graphRef}
            graphData={{ nodes: filteredNodes, links: visibleLinks }}
            nodeLabel={(node) => null}
            nodeColor={(node) => nodeColors[node.type] || nodeColors.default}
            nodeVal={15}
            nodeRelSize={4}
            linkLabel={() => null}
            linkColor={() => 'rgba(255, 152, 0, 0.95)'}
            linkWidth={(link) => Math.max(2, (link.strength || 0.5) * 3)}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            backgroundColor="#1a1a2e"
            onNodeClick={handleNodeClick}
            onLinkClick={handleLinkClick}
            enableZoomPanInteraction={true}
            enableDragInteraction={true}
            width={showDetails ? window.innerWidth - 400 : window.innerWidth - 50}
            height={window.innerHeight - 120}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.name || node.type
              const fontSize = 10
              ctx.font = `bold ${fontSize}px Sans-Serif`
              
              ctx.fillStyle = nodeColors[node.type] || nodeColors.default
              ctx.beginPath()
              ctx.arc(node.x, node.y, 13, 0, 2 * Math.PI, false)
              ctx.fill()
              
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = '#fff'
              ctx.fillText(label.substring(0, 12), node.x, node.y)
              
              ctx.font = `${fontSize - 2}px Sans-Serif`
              ctx.fillStyle = '#888'
              ctx.fillText(node.type || '', node.x, node.y + 22)
            }}
            linkCanvasObjectMode={() => 'after'}
            linkCanvasObject={(link, ctx, globalScale) => {
              const label = link.type || 'related'
              const start = link.source
              const end = link.target
              if (!start || !end || start.x == null || end.x == null) return

              const fontSize = Math.max(6, 8 / globalScale)
              const midX = (start.x + end.x) / 2
              const midY = (start.y + end.y) / 2
              ctx.font = `600 ${fontSize}px Sans-Serif`
              const textWidth = ctx.measureText(label).width
              const pad = 3

              ctx.fillStyle = 'rgba(26, 26, 46, 0.9)'
              ctx.fillRect(midX - textWidth / 2 - pad, midY - fontSize / 2 - 2, textWidth + pad * 2, fontSize + 4)
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = '#ffd180'
              ctx.fillText(label, midX, midY)
            }}
          />
          
          {showDetails && linkDetails && (
            <div style={styles.detailsPanel}>
              <div style={styles.detailsHeader}>
                <h3>Relationship Details</h3>
                <button style={styles.closeBtn} onClick={() => setLinkDetails(null)}>×</button>
              </div>
              <div style={styles.detailsContent}>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Type:</span>
                  <span style={styles.detailValue}>{linkDetails.type || 'related'}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Strength:</span>
                  <span style={styles.detailValue}>{linkDetails.strength || 0.5}</span>
                </div>
                {linkDetails.properties && linkDetails.properties.why && (
                  <div style={styles.reasoningBox}>
                    <span style={styles.detailLabel}>Why:</span>
                    <p style={styles.reasoningText}>{linkDetails.properties.why}</p>
                  </div>
                )}
                {linkDetails.properties && linkDetails.properties.source_message && (
                  <div style={styles.reasoningBox}>
                    <span style={styles.detailLabel}>From message:</span>
                    <p style={styles.reasoningText}>{linkDetails.properties.source_message}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {showDetails && nodeDetails && (
            <div style={styles.detailsPanel}>
              <div style={styles.detailsHeader}>
                <h3>Node Details</h3>
                <button style={styles.closeBtn} onClick={() => setNodeDetails(null)}>×</button>
              </div>
              <div style={styles.detailsContent}>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>ID:</span>
                  <span style={styles.detailValue}>{nodeDetails.id?.substring(0, 8)}...</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Name:</span>
                  <span style={styles.detailValue}>{nodeDetails.name || 'N/A'}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Type:</span>
                  <span style={{...styles.detailValue, color: nodeColors[nodeDetails.type] || nodeColors.default}}>
                    {nodeDetails.type || 'unknown'}
                  </span>
                </div>
                {nodeDetails.val && (
                  <div style={styles.detailRow}>
                    <span style={styles.detailLabel}>Value:</span>
                    <span style={styles.detailValue}>{nodeDetails.val}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div style={styles.sidePanel}>
          <div style={styles.tabs}>
            <button 
              style={{...styles.tab, ...(activeTab === 'chat' ? styles.activeTab : {})}}
              onClick={() => setActiveTab('chat')}
            >
              💬 Chat
            </button>
            <button 
              style={{...styles.tab, ...(activeTab === 'graph' ? styles.activeTab : {})}}
              onClick={() => setActiveTab('graph')}
            >
              📊 Graph
            </button>
            <button 
              style={{...styles.tab, ...(activeTab === 'memory' ? styles.activeTab : {})}}
              onClick={() => setActiveTab('memory')}
            >
              💾 Memory
            </button>
          </div>

          {activeTab === 'chat' && (
            <div style={styles.chatPanel}>
              <div style={styles.chatMessages}>
                {messages.length === 0 && (
                  <div style={styles.welcome}>
                    <p>👋 Chat with the AI</p>
                    <p style={{fontSize: '12px', marginTop: '10px', color: '#888'}}>
                      Entities and relationships are extracted automatically and stored in the graph.
                    </p>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} style={{
                    ...styles.message,
                    ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage)
                  }}>
                    <div style={styles.messageRole}>{msg.role === 'user' ? 'You' : 'AI'}</div>
                    <div style={styles.messageContent}>{msg.content}</div>
                    {msg.memoryInfo && (
                      <div style={styles.memoryBadge}>
                        📊 {msg.memoryInfo.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && <div style={styles.loading}>Thinking...</div>}
                <div ref={chatEndRef} />
              </div>
              <form onSubmit={handleChat} style={styles.chatInput}>
                <input
                  type="text"
                  placeholder="Type a message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  style={styles.chatInputField}
                  disabled={isLoading}
                />
                <button type="submit" style={styles.sendBtn} disabled={isLoading}>
                  Send
                </button>
              </form>
            </div>
          )}

          {activeTab === 'graph' && (
            <div style={styles.panelContent}>
              <div style={styles.statsCard}>
                <h4 style={styles.cardTitle}>Graph Statistics</h4>
                <div style={styles.statGrid}>
                  <div style={styles.statBox}>
                    <span style={styles.statNumber}>{stats.knowledge_graph_entities || 0}</span>
                    <span style={styles.statLabel}>Entities</span>
                  </div>
                  <div style={styles.statBox}>
                    <span style={styles.statNumber}>{stats.knowledge_graph_relations || 0}</span>
                    <span style={styles.statLabel}>Relations</span>
                  </div>
                  <div style={styles.statBox}>
                    <span style={styles.statNumber}>{stats.context_graph_nodes || 0}</span>
                    <span style={styles.statLabel}>Context Nodes</span>
                  </div>
                  <div style={styles.statBox}>
                    <span style={styles.statNumber}>{stats.working_memory_count || 0}</span>
                    <span style={styles.statLabel}>Working Memory</span>
                  </div>
                </div>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); addEntity(entityName, entityType); setEntityName(''); }} style={styles.form}>
                <h4 style={styles.cardTitle}>Add Entity</h4>
                <input
                  type="text"
                  placeholder="Entity name"
                  value={entityName}
                  onChange={(e) => setEntityName(e.target.value)}
                  style={styles.input}
                />
                <select 
                  value={entityType} 
                  onChange={(e) => setEntityType(e.target.value)}
                  style={styles.select}
                >
                  <option value="person">Person</option>
                  <option value="place">Place</option>
                  <option value="concept">Concept</option>
                  <option value="preference">Preference</option>
                  <option value="company">Company</option>
                </select>
                <button type="submit" style={styles.button}>Add to Graph</button>
              </form>

              <div style={styles.legend}>
                <h4 style={styles.cardTitle}>Legend</h4>
                {Object.entries(nodeColors).map(([type, color]) => (
                  <div key={type} style={styles.legendItem}>
                    <span style={{...styles.legendColor, backgroundColor: color}}></span>
                    <span>{type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'memory' && (
            <div style={styles.panelContent}>
              <div style={styles.memoryList}>
                {workingMemory.length === 0 ? (
                  <p style={styles.empty}>No working memory</p>
                ) : (
                  workingMemory.slice().reverse().map((item, i) => (
                    <div key={i} style={styles.memoryItem}>
                      <span style={styles.role}>{item.role}</span>
                      <p style={styles.memoryContent}>{item.content}</p>
                    </div>
                  ))
                )}
              </div>
              <button onClick={clearWorkingMemory} style={styles.clearBtn}>
                Clear Working Memory
              </button>
              <button onClick={() => { if(confirm('Delete all memory and reset database?')) resetDatabase() }} style={styles.resetBtn}>
                🗑️ Reset Database
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    background: '#0f0f1a',
    color: '#eee',
    fontFamily: "'Segoe UI', Roboto, sans-serif",
  },
  header: {
    padding: '12px 20px',
    background: '#16213e',
    borderBottom: '1px solid #1a1a2e',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  title: {
    fontSize: '20px',
    fontWeight: '600',
    margin: 0,
    color: '#fff',
  },
  graphSelector: {
    display: 'flex',
    gap: '5px',
  },
  graphBtn: {
    padding: '6px 12px',
    background: 'transparent',
    border: '1px solid #333',
    borderRadius: '4px',
    color: '#888',
    cursor: 'pointer',
    fontSize: '12px',
  },
  activeGraphBtn: {
    background: '#2196f3',
    borderColor: '#2196f3',
    color: '#fff',
  },
  stats: {
    display: 'flex',
    gap: '20px',
    fontSize: '13px',
    color: '#888',
  },
  statItem: {
    padding: '4px 8px',
    background: '#1a1a2e',
    borderRadius: '4px',
  },
  main: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  graphPanel: {
    flex: 1,
    position: 'relative',
  },
  graphToolbar: {
    position: 'absolute',
    top: '10px',
    left: '10px',
    zIndex: 10,
    display: 'flex',
    gap: '8px',
  },
  searchInput: {
    padding: '8px 12px',
    background: 'rgba(22, 33, 62, 0.9)',
    border: '1px solid #333',
    borderRadius: '4px',
    color: '#eee',
    width: '200px',
  },
  iconBtn: {
    padding: '8px 12px',
    background: 'rgba(22, 33, 62, 0.9)',
    border: '1px solid #333',
    borderRadius: '4px',
    color: '#eee',
    cursor: 'pointer',
    fontSize: '16px',
  },
  detailsPanel: {
    position: 'absolute',
    top: '60px',
    left: '10px',
    width: '250px',
    background: 'rgba(22, 33, 62, 0.95)',
    border: '1px solid #333',
    borderRadius: '8px',
    zIndex: 10,
  },
  detailsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 15px',
    borderBottom: '1px solid #333',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#888',
    fontSize: '20px',
    cursor: 'pointer',
  },
  detailsContent: {
    padding: '15px',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  },
  detailLabel: {
    color: '#888',
    fontSize: '12px',
  },
  detailValue: {
    color: '#eee',
    fontSize: '12px',
  },
  reasoningBox: {
    marginTop: '12px',
    padding: '10px',
    background: '#0f0f1a',
    borderRadius: '6px',
    border: '1px solid #333',
  },
  reasoningText: {
    color: '#aaa',
    fontSize: '11px',
    marginTop: '5px',
    lineHeight: '1.4',
  },
  sidePanel: {
    width: '400px',
    background: '#16213e',
    borderLeft: '1px solid #1a1a2e',
    display: 'flex',
    flexDirection: 'column',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #1a1a2e',
  },
  tab: {
    flex: 1,
    padding: '12px',
    background: 'transparent',
    border: 'none',
    color: '#666',
    cursor: 'pointer',
    fontSize: '13px',
  },
  activeTab: {
    color: '#2196f3',
    borderBottom: '2px solid #2196f3',
  },
  chatPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  chatMessages: {
    flex: 1,
    overflow: 'auto',
    padding: '15px',
  },
  welcome: {
    textAlign: 'center',
    color: '#666',
    padding: '20px',
    border: '1px dashed #333',
    borderRadius: '8px',
  },
  message: {
    padding: '12px',
    marginBottom: '10px',
    borderRadius: '8px',
    maxWidth: '90%',
  },
  userMessage: {
    background: '#1976d2',
    marginLeft: 'auto',
  },
  assistantMessage: {
    background: '#1a1a2e',
  },
  messageRole: {
    fontSize: '11px',
    color: '#888',
    marginBottom: '4px',
  },
  messageContent: {
    fontSize: '14px',
    lineHeight: '1.4',
  },
  memoryBadge: {
    fontSize: '11px',
    color: '#4caf50',
    marginTop: '8px',
    paddingTop: '8px',
    borderTop: '1px solid #333',
  },
  loading: {
    color: '#666',
    fontStyle: 'italic',
    padding: '10px',
  },
  chatInput: {
    display: 'flex',
    padding: '10px',
    borderTop: '1px solid #1a1a2e',
    gap: '10px',
  },
  chatInputField: {
    flex: 1,
    padding: '10px',
    background: '#1a1a2e',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#eee',
  },
  sendBtn: {
    padding: '10px 20px',
    background: '#2196f3',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
  },
  panelContent: {
    padding: '15px',
    overflow: 'auto',
    flex: 1,
  },
  statsCard: {
    background: '#1a1a2e',
    borderRadius: '8px',
    padding: '15px',
    marginBottom: '20px',
  },
  cardTitle: {
    margin: '0 0 15px 0',
    fontSize: '14px',
    color: '#888',
  },
  statGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '10px',
  },
  statBox: {
    background: '#16213e',
    padding: '10px',
    borderRadius: '6px',
    textAlign: 'center',
  },
  statNumber: {
    display: 'block',
    fontSize: '20px',
    fontWeight: '600',
    color: '#2196f3',
  },
  statLabel: {
    fontSize: '11px',
    color: '#666',
  },
  form: {
    marginBottom: '20px',
  },
  input: {
    width: '100%',
    padding: '10px',
    marginBottom: '10px',
    background: '#1a1a2e',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#eee',
  },
  select: {
    width: '100%',
    padding: '10px',
    marginBottom: '10px',
    background: '#1a1a2e',
    border: '1px solid #333',
    borderRadius: '6px',
    color: '#eee',
  },
  button: {
    width: '100%',
    padding: '10px',
    background: '#2196f3',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '14px',
  },
  legend: {
    background: '#1a1a2e',
    borderRadius: '8px',
    padding: '15px',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '8px',
    fontSize: '12px',
  },
  legendColor: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
  },
  memoryList: {
    maxHeight: '400px',
    overflow: 'auto',
  },
  memoryItem: {
    padding: '10px',
    marginBottom: '8px',
    background: '#1a1a2e',
    borderRadius: '6px',
  },
  role: {
    fontSize: '11px',
    color: '#2196f3',
    textTransform: 'uppercase',
  },
  memoryContent: {
    fontSize: '12px',
    margin: '5px 0 0 0',
    color: '#ccc',
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    padding: '20px',
  },
  clearBtn: {
    width: '100%',
    padding: '10px',
    background: '#f44336',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    marginTop: '10px',
  },
  resetBtn: {
    width: '100%',
    padding: '10px',
    background: '#d32f2f',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    marginTop: '8px',
  }
}

export default App
