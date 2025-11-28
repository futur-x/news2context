
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { taskAPI, externalAPI, chatAPI } from '../api/client'
import api from '../api/client'
import SourceSelector from '../components/SourceSelector'
import './TaskDetail.css'
import './TaskDetailExtras.css'

interface Task {
    name: string
    scene: string
    collection: string
    sources: any[]
    status: any
}

function TaskDetail() {
    const { taskName } = useParams<{ taskName: string }>()
    const navigate = useNavigate()
    const [task, setTask] = useState<Task | null>(null)
    const [apiToken, setApiToken] = useState<string>('')
    const [loading, setLoading] = useState(true)

    // Search state
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState<any[]>([])
    const [searching, setSearching] = useState(false)
    const [searchMode, setSearchMode] = useState('hybrid') // hybrid, semantic, keyword

    // Chat state
    const [chatMessage, setChatMessage] = useState('')
    const [chatHistory, setChatHistory] = useState<any[]>([])
    const [chatting, setChatting] = useState(false)

    // Knowledge base content
    const [kbContent, setKbContent] = useState<any[]>([])
    const [loadingKb, setLoadingKb] = useState(false)

    // Source management state
    const [showAddSourceModal, setShowAddSourceModal] = useState(false)
    const [addingSources, setAddingSources] = useState(false)
    const [selectedNewSources, setSelectedNewSources] = useState<string[]>([])

    // Task execution status polling
    const [taskStatus, setTaskStatus] = useState<any>(null)
    const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null)

    useEffect(() => {
        if (taskName) {
            loadTask()
            loadTaskStatus()
        }
    }, [taskName])

    // Poll task status when running
    useEffect(() => {
        if (taskStatus?.running) {
            const interval = setInterval(() => {
                loadTaskStatus()
            }, 2000) // Poll every 2 seconds
            setPollingInterval(interval)
            return () => clearInterval(interval)
        } else if (pollingInterval) {
            clearInterval(pollingInterval)
            setPollingInterval(null)
        }
    }, [taskStatus?.running])

    const loadTask = async () => {
        try {
            const response = await taskAPI.get(taskName!)
            setTask(response.data)
            // Load knowledge base content
            loadKbContent()
        } catch (error) {
            console.error('Failed to load task:', error)
        } finally {
            setLoading(false)
        }
    }

    const loadKbContent = async () => {
        setLoadingKb(true)
        try {
            const response = await taskAPI.browse(taskName!, 20)
            setKbContent(response.data.items || [])
        } catch (error) {
            console.error('Failed to load KB content:', error)
        } finally {
            setLoadingKb(false)
        }
    }

    const loadTaskStatus = async () => {
        try {
            const response = await api.get(`/tasks/${taskName}/status`)
            setTaskStatus(response.data)
            // Reload full task if status changed from running to not running
            if (taskStatus?.running && !response.data.running) {
                loadTask()
            }
        } catch (error) {
            console.error('Failed to load task status:', error)
        }
    }

    const handleRunTask = async () => {
        try {
            await taskAPI.run(taskName!)
            // Immediately poll status
            setTimeout(() => loadTaskStatus(), 500)
        } catch (error) {
            console.error('Failed to run task:', error)
            alert('Failed to start task')
        }
    }

    const handleGenerateToken = async () => {
        try {
            const response = await externalAPI.generateToken()
            setApiToken(response.data.token)
        } catch (error) {
            console.error('Failed to generate token:', error)
        }
    }

    const handleDeleteTask = async () => {
        if (!confirm(`Are you sure you want to delete task "${taskName}" ? This action cannot be undone.`)) {
            return
        }

        try {
            await taskAPI.delete(taskName!)
            navigate('/')
        } catch (error) {
            console.error('Failed to delete task:', error)
            alert('Failed to delete task')
        }
    }

    const handleRemoveSource = async (sourceHashId: string) => {
        if (!task) return
        if (!confirm('Are you sure you want to remove this source?')) return

        try {
            const updatedSources = task.sources.filter((s: any) => s.hashid !== sourceHashId)
            await taskAPI.update(taskName!, {
                sources: updatedSources
            })
            loadTask()
        } catch (error) {
            console.error('Failed to remove source:', error)
            alert('Failed to remove source')
        }
    }

    const handleAddSources = async () => {
        if (!task || selectedNewSources.length === 0) return

        setAddingSources(true)
        try {
            // Fetch source details to map hashids
            const settingsRes = await import('../api/client').then(m => m.settingsAPI.getTopHub())
            const allSources = settingsRes.data.sources || []
            const newSourceObjects = allSources
                .filter((s: any) => selectedNewSources.includes(s.hashid))
                .map((s: any) => ({
                    name: s.name,
                    hashid: s.hashid,
                    category: s.category
                }))

            // Merge with existing sources, avoiding duplicates
            const existingHashIds = task.sources.map((s: any) => s.hashid)
            const sourcesToAdd = newSourceObjects.filter((s: any) => !existingHashIds.includes(s.hashid))

            if (sourcesToAdd.length === 0) {
                alert('Selected sources are already added')
                setShowAddSourceModal(false)
                return
            }

            const updatedSources = [...task.sources, ...sourcesToAdd]

            await taskAPI.update(taskName!, {
                sources: updatedSources
            })

            setShowAddSourceModal(false)
            setSelectedNewSources([])
            loadTask()
        } catch (error) {
            console.error('Failed to add sources:', error)
            alert('Failed to add sources')
        } finally {
            setAddingSources(false)
        }
    }

    const handleSearch = async () => {
        if (!searchQuery.trim()) return

        setSearching(true)
        try {
            // Use internal query API (no token required)
            const response = await api.post('/query', {
                query: searchQuery,
                task_name: taskName,
                limit: 5,
                search_mode: searchMode
            })
            setSearchResults(response.data.results || [])
        } catch (error) {
            console.error('Search failed:', error)
            alert('搜索失败')
        } finally {
            setSearching(false)
        }
    }

    const handleSendMessage = async (e: React.FormEvent) => { // Renamed from handleChat to handleSendMessage
        e.preventDefault() // Added to prevent default form submission
        if (!chatMessage.trim() || !task) return // Added !task check

        const userMessage = { role: 'user', content: chatMessage }
        setChatHistory([...chatHistory, userMessage])
        setChatMessage('')
        setChatting(true)

        try {
            const response = await chatAPI.sendMessage({
                task_name: taskName,
                message: chatMessage,
                history: chatHistory
            })

            const assistantMessage = {
                role: 'assistant',
                content: response.data.message,
                sources: response.data.sources
            }
            setChatHistory([...chatHistory, userMessage, assistantMessage])
        } catch (error) {
            console.error('Chat failed:', error)
            setChatHistory([...chatHistory, userMessage, {
                role: 'assistant',
                content: '抱歉，发生了错误。请稍后再试。'
            }])
        } finally {
            setChatting(false)
        }
    }

    if (loading) {
        return <div className="loading">Loading...</div>
    }

    if (!task) {
        return <div className="error">Task not found</div>
    }

    const apiUrl = `http://localhost:8000/api/external/${taskName}/query`

    return (
        <div className="task-detail">
            <div className="task-detail-header">
                <div>
                    <h1 className="page-title">{task.name}</h1>
                    <p className="page-subtitle">{task.scene}</p>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleRunTask}
                        disabled={taskStatus?.running}
                    >
                        {taskStatus?.running ? '⏸ Running...' : '▶ Run Now'}
                    </button>
                    <button className="btn btn-secondary" style={{ color: 'var(--color-accent-error)' }} onClick={handleDeleteTask}>
                        🗑️ Delete
                    </button>
                </div>
            </div>

            <div className="detail-grid">
                {/* Execution Status Section */}
                {(taskStatus?.running || taskStatus?.current_status === 'error') && (
                    <div className="detail-section execution-status">
                        <h2 className="section-title">🔄 Execution Status</h2>
                        <div className="status-content">
                            {taskStatus.running && (
                                <>
                                    <div className="status-badge running">● Running</div>
                                    {taskStatus.progress && (
                                        <>
                                            <div className="progress-bar-large">
                                                <div
                                                    className="progress-fill-large"
                                                    style={{
                                                        width: `${(taskStatus.progress.processed_sources / taskStatus.progress.total_sources) * 100}%`
                                                    }}
                                                />
                                            </div>
                                            <div className="progress-details">
                                                <div className="progress-item">
                                                    <span className="label">Processed:</span>
                                                    <span className="value">{taskStatus.progress.processed_sources}/{taskStatus.progress.total_sources} sources</span>
                                                </div>
                                                <div className="progress-item">
                                                    <span className="label">Collected:</span>
                                                    <span className="value">{taskStatus.progress.collected_articles} articles</span>
                                                </div>
                                                <div className="progress-item">
                                                    <span className="label">Started:</span>
                                                    <span className="value">{new Date(taskStatus.progress.start_time).toLocaleTimeString()}</span>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </>
                            )}
                            {taskStatus.current_status === 'error' && taskStatus.last_error && (
                                <div className="error-message">
                                    <strong>Error:</strong> {taskStatus.last_error}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                <div className="detail-section">
                    <h2 className="section-title">Overview</h2>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-label">Status</div>
                            <div className="stat-value">
                                <span className={`badge ${task.status.enabled ? 'badge-success' : 'badge-warning'}`}>
                                    {task.status.enabled ? 'Active' : 'Paused'}
                                </span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Sources</div>
                            <div className="stat-value">{task.sources.length}</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Total Runs</div>
                            <div className="stat-value">{task.status.total_runs}</div>
                        </div>
                    </div>
                </div>

                <div className="detail-section">
                    <div className="section-header">
                        <h2 className="section-title">Sources</h2>
                        <button
                            className="btn btn-sm btn-outline"
                            onClick={() => setShowAddSourceModal(true)}
                        >
                            + Add Source
                        </button>
                    </div>
                    <div className="sources-grid">
                        {task.sources.map((source: any) => (
                            <div key={source.hashid} className="source-card">
                                <div className="source-info">
                                    <div className="source-name">{source.name}</div>
                                    <div className="source-category">{source.category || 'News'}</div>
                                </div>
                                <button
                                    className="btn-icon remove-source-btn"
                                    onClick={() => handleRemoveSource(source.hashid)}
                                    title="Remove source"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="detail-section">
                    <h2 className="section-title">📚 Knowledge Base Content ({kbContent.length} items)</h2>
                    {loadingKb ? (
                        <div className="loading">Loading content...</div>
                    ) : kbContent.length > 0 ? (
                        <div className="kb-content-list">
                            {kbContent.map((item, idx) => (
                                <div key={idx} className="kb-item">
                                    <h4 className="kb-item-title">{item.title}</h4>
                                    <div className="kb-item-content">
                                        {item.content?.substring(0, 200)}...
                                    </div>
                                    <div className="kb-item-meta">
                                        <span>📰 {item.source_name}</span>
                                        {item.published_at && (
                                            <span>📅 {new Date(item.published_at).toLocaleDateString()}</span>
                                        )}
                                    </div>
                                    {item.url && (
                                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="kb-item-link">
                                            查看原文 →
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">暂无内容</div>
                    )}
                </div>

                <div className="detail-section">
                    <h2 className="section-title">External API</h2>
                    <div className="api-console">
                        <div className="api-endpoint">
                            <label>Endpoint URL</label>
                            <code className="code-block">{apiUrl}</code>
                        </div>

                        {!apiToken ? (
                            <button className="btn btn-secondary" onClick={handleGenerateToken}>
                                Generate API Token
                            </button>
                        ) : (
                            <div className="token-display">
                                <label>API Token (Save this securely)</label>
                                <code className="code-block token">{apiToken}</code>
                            </div>
                        )}

                        <div className="curl-example">
                            <label>Example cURL Command</label>
                            <code className="code-block">
                                {`curl -X POST "${apiUrl}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "AI news", "limit": 5}'`}
                            </code>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h2 className="section-title">🔍 Search Test</h2>
                        <div className="search-panel">
                            <div className="search-mode-selector">
                                <label>Search Mode:</label>
                                <select
                                    value={searchMode}
                                    onChange={(e) => setSearchMode(e.target.value)}
                                    className="mode-select"
                                >
                                    <option value="hybrid">Hybrid (推荐)</option>
                                    <option value="semantic">Semantic (语义)</option>
                                    <option value="keyword">Keyword (关键词)</option>
                                </select>
                            </div>

                            <div className="search-input-group">
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="输入关键词测试搜索..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                />
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSearch}
                                    disabled={searching}
                                >
                                    {searching ? '搜索中...' : '搜索'}
                                </button>
                            </div>

                            {searchResults.length > 0 && (
                                <div className="search-results">
                                    <h3>搜索结果 ({searchResults.length})</h3>
                                    {searchResults.map((result, idx) => (
                                        <div key={idx} className="search-result-item">
                                            <div className="result-score">
                                                Score: {result.score ? (result.score * 100).toFixed(1) : 'N/A'}%
                                            </div>
                                            <h4 className="result-title">{result.title}</h4>
                                            <div className="result-content">
                                                {result.content?.substring(0, 300)}...
                                            </div>
                                            <div className="result-meta">
                                                <span>📰 {result.source_name}</span>
                                                {result.published_at && (
                                                    <span>📅 {new Date(result.published_at).toLocaleDateString()}</span>
                                                )}
                                            </div>
                                            {result.url && (
                                                <a href={result.url} target="_blank" rel="noopener noreferrer" className="result-link">
                                                    查看原文 →
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="detail-section">
                        <h2 className="section-title">💬 Knowledge Base Chat</h2>
                        <div className="chat-panel">
                            <div className="chat-messages">
                                {chatHistory.length === 0 ? (
                                    <div className="chat-empty">
                                        开始对话，向知识库提问...
                                    </div>
                                ) : (
                                    chatHistory.map((msg, idx) => (
                                        <div key={idx} className={`chat-message ${msg.role}`}>
                                            <div className="message-role">
                                                {msg.role === 'user' ? '👤 You' : '🤖 Assistant'}
                                            </div>
                                            <div className="message-content">{msg.content}</div>
                                            {msg.sources && msg.sources.length > 0 && (
                                                <div className="message-sources">
                                                    <strong>参考来源:</strong>
                                                    {msg.sources.map((src: any, i: number) => (
                                                        <div key={i} className="source-item">
                                                            • {src.content}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                                {chatting && (
                                    <div className="chat-message assistant">
                                        <div className="message-role">🤖 Assistant</div>
                                        <div className="message-content">思考中...</div>
                                    </div>
                                )}
                            </div>

                            <div className="chat-input-group">
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="输入您的问题..."
                                    value={chatMessage}
                                    onChange={(e) => setChatMessage(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(e)}
                                    disabled={chatting}
                                />
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSendMessage}
                                    disabled={chatting || !chatMessage.trim()}
                                >
                                    发送
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                {showAddSourceModal && (
                    <div className="modal-overlay">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h2>Add News Sources</h2>
                                <button
                                    className="close-btn"
                                    onClick={() => setShowAddSourceModal(false)}
                                >
                                    ×
                                </button>
                            </div>
                            <div className="modal-body" style={{ padding: 'var(--space-lg)', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '400px' }}>
                                <div className="source-selector-container" style={{ flex: 1 }}>
                                    <SourceSelector
                                        selectedSources={selectedNewSources}
                                        onChange={setSelectedNewSources}
                                        scene={task?.scene}
                                    />
                                </div>
                            </div>
                            <div className="modal-actions">
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={() => setShowAddSourceModal(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="button"
                                    className="btn btn-primary"
                                    onClick={handleAddSources}
                                    disabled={addingSources || selectedNewSources.length === 0}
                                >
                                    {addingSources ? 'Adding...' : `Add ${selectedNewSources.length} Sources`}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default TaskDetail
