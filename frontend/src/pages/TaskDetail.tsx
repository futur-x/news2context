
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { taskAPI, externalAPI, chatAPI } from '../api/client'
import api from '../api/client'
import SourceSelector from '../components/SourceSelector'
import ScheduleEditor from '../components/ScheduleEditor'
import { cronToHumanReadable } from '../utils/cronUtils'
import './TaskDetail.css'
import './TaskDetailExtras.css'

interface Task {
    name: string
    scene: string
    collection: string
    sources: any[]
    status: any
    schedule?: {
        enabled: boolean
        cron: string
    }
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
    const [kbPage, setKbPage] = useState(1)
    const [kbTotal, setKbTotal] = useState(0)
    const kbPageSize = 24  // 每页显示 24 条（4列 × 6行）
    const [selectedKbItem, setSelectedKbItem] = useState<any>(null)
    const [showKbDetailModal, setShowKbDetailModal] = useState(false)
    const [itemToDelete, setItemToDelete] = useState<any>(null)
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
    const [showDeleteTaskConfirm, setShowDeleteTaskConfirm] = useState(false)
    const [showScheduleModal, setShowScheduleModal] = useState(false)
    const [scheduleConfig, setScheduleConfig] = useState({ enabled: false, cron: '0 9 * * *' })

    // Source management state
    const [showAddSourceModal, setShowAddSourceModal] = useState(false)
    const [addingSources, setAddingSources] = useState(false)
    const [selectedNewSources, setSelectedNewSources] = useState<string[]>([])

    // Task execution status polling
    const [taskStatus, setTaskStatus] = useState<any>(null)
    const [pollingInterval, setPollingInterval] = useState<number | null>(null)

    useEffect(() => {
        if (taskName) {
            loadTask()
            loadTaskStatus()
            loadKnowledgeBase()
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
            loadKnowledgeBase()
        } catch (error) {
            console.error('Failed to load task:', error)
        } finally {
            setLoading(false)
        }
    }

    const loadKnowledgeBase = async (page: number = 1) => {
        if (!taskName) return
        setLoadingKb(true)
        try {
            const offset = (page - 1) * kbPageSize
            const res = await taskAPI.browse(taskName!, { limit: kbPageSize, offset })
            setKbContent(res.data.items || [])
            setKbTotal(res.data.total || 0)
            setKbPage(page)
        } catch (err) {
            console.error('Failed to load KB content:', err)
        } finally {
            setLoadingKb(false)
        }
    }

    const handleDeleteClick = (item: any, e: React.MouseEvent) => {
        e.stopPropagation()
        setItemToDelete(item)
        setShowDeleteConfirm(true)
    }

    const handleConfirmDelete = async () => {
        if (!itemToDelete) return

        try {
            await api.delete(`/tasks/${taskName}/items/${itemToDelete.id}`)
            setShowDeleteConfirm(false)
            setItemToDelete(null)
            // 删除后刷新列表
            await loadKnowledgeBase(kbPage)
        } catch (error) {
            console.error('Failed to delete item:', error)
            alert('删除失败')
            setShowDeleteConfirm(false)
            setItemToDelete(null)
        }
    }

    const handleCancelDelete = () => {
        setShowDeleteConfirm(false)
        setItemToDelete(null)
    }

    const handleViewKbItem = (item: any) => {
        setSelectedKbItem(item)
        setShowKbDetailModal(true)
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

    const handleDeleteTask = () => {
        setShowDeleteTaskConfirm(true)
    }

    const handleConfirmDeleteTask = async () => {
        try {
            await taskAPI.delete(taskName!)
            setShowDeleteTaskConfirm(false)
            navigate('/')
        } catch (error) {
            console.error('Failed to delete task:', error)
            setShowDeleteTaskConfirm(false)
        }
    }

    const handleCancelDeleteTask = () => {
        setShowDeleteTaskConfirm(false)
    }

    const handleEditSchedule = () => {
        if (task?.schedule) {
            setScheduleConfig(task.schedule)
        }
        setShowScheduleModal(true)
    }

    const handleSaveSchedule = async () => {
        try {
            await taskAPI.update(taskName!, {
                schedule: scheduleConfig
            })

            // Optimistically update local state immediately
            if (task) {
                setTask({ ...task, schedule: scheduleConfig })
            }

            setShowScheduleModal(false)

            // Refetch after a short delay to ensure backend has processed the update
            setTimeout(() => {
                loadTask()
            }, 500)
        } catch (error) {
            console.error('Failed to update schedule:', error)
        }
    }

    const handleCancelSchedule = () => {
        setShowScheduleModal(false)
    }

    const handleRemoveSource = async (sourceHashId: string) => {
        if (!task) return

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

                {/* Schedule Settings Section */}
                <div className="detail-section">
                    <div className="section-header">
                        <h2 className="section-title">⏰ Schedule Settings</h2>
                        <button className="btn btn-secondary btn-sm" onClick={handleEditSchedule}>
                            Edit Schedule
                        </button>
                    </div>
                    <div className="schedule-info">
                        {task.schedule?.enabled ? (
                            <>
                                <div className="schedule-status enabled">
                                    <span className="status-dot">●</span>
                                    <span>Enabled</span>
                                </div>
                                <div className="schedule-details">
                                    <div className="schedule-detail-item">
                                        <span className="label">执行计划:</span>
                                        <span className="schedule-description">{cronToHumanReadable(task.schedule.cron)}</span>
                                    </div>
                                    <div className="schedule-detail-item">
                                        <span className="label">Cron 表达式:</span>
                                        <code className="cron-expression">{task.schedule.cron}</code>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="schedule-status disabled">
                                <span className="status-dot">○</span>
                                <span>Disabled - Task will not run automatically</span>
                            </div>
                        )}
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
                    <h2 className="section-title">📚 Knowledge Base Content ({kbTotal} total items)</h2>
                    {loadingKb ? (
                        <div className="loading">Loading content...</div>
                    ) : kbContent.length > 0 ? (
                        <>
                            <div className="kb-content-grid">
                                {kbContent.map((item, idx) => (
                                    <div key={idx} className="kb-card" onClick={() => handleViewKbItem(item)}>
                                        <button
                                            className="kb-card-delete"
                                            onClick={(e) => handleDeleteClick(item, e)}
                                            title="删除"
                                        >
                                            ×
                                        </button>
                                        <h4 className="kb-card-title">{item.title}</h4>
                                        <div className="kb-card-content">
                                            {item.content?.substring(0, 150)}...
                                        </div>
                                        <div className="kb-card-meta">
                                            <span className="kb-source">📰 {item.source_name}</span>
                                            {item.published_at && (
                                                <span className="kb-date">📅 {new Date(item.published_at).toLocaleDateString()}</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="pagination">
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => loadKnowledgeBase(kbPage - 1)}
                                    disabled={kbPage === 1}
                                >
                                    ← Previous
                                </button>
                                <span className="pagination-info">
                                    Page {kbPage} of {Math.ceil(kbTotal / kbPageSize)} ({kbTotal} items)
                                </span>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => loadKnowledgeBase(kbPage + 1)}
                                    disabled={kbPage >= Math.ceil(kbTotal / kbPageSize)}
                                >
                                    Next →
                                </button>
                            </div>
                        </>
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
  -d '{
    "query": "AI news",
    "limit": 5,
    "search_mode": "hybrid",
    "alpha": 0.7,
    "min_score": 0.3
  }'`}
                            </code>
                        </div>

                        <div className="api-params-doc">
                            <label>API Parameters</label>
                            <ul className="params-list">
                                <li><code>query</code> (required): 查询问题</li>
                                <li><code>limit</code> (optional, 1-20, default: 5): 返回结果数量</li>
                                <li><code>search_mode</code> (optional, default: "hybrid"): 搜索模式
                                    <ul>
                                        <li>"hybrid" - 混合搜索</li>
                                        <li>"semantic" - 纯语义搜索</li>
                                        <li>"keyword" - 纯关键词搜索</li>
                                    </ul>
                                </li>
                                <li><code>alpha</code> (optional, 0.0-1.0, default: 0.5): 混合搜索权重
                                    <ul>
                                        <li>0.0 = 纯关键词</li>
                                        <li>1.0 = 纯语义</li>
                                        <li>0.5 = 平衡</li>
                                    </ul>
                                </li>
                                <li><code>min_score</code> (optional, 0.0-1.0, default: 0.0): 最低分数阈值（低于此分数的结果不返回）</li>
                            </ul>
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

                {/* Schedule Edit Modal */}
                {showScheduleModal && (
                    <div className="modal-overlay" onClick={handleCancelSchedule}>
                        <div className="modal-content schedule-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>Edit Schedule Settings</h2>
                                <button className="modal-close" onClick={handleCancelSchedule}>×</button>
                            </div>
                            <div className="modal-body">
                                <ScheduleEditor
                                    schedule={scheduleConfig}
                                    onChange={setScheduleConfig}
                                    onSave={handleSaveSchedule}
                                    onCancel={handleCancelSchedule}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Knowledge Base Item Detail Modal */}
            {
                showKbDetailModal && selectedKbItem && (
                    <div className="modal-overlay" onClick={() => setShowKbDetailModal(false)}>
                        <div className="modal-content kb-detail-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>{selectedKbItem.title}</h2>
                                <button className="modal-close" onClick={() => setShowKbDetailModal(false)}>×</button>
                            </div>
                            <div className="modal-body">
                                <div className="kb-detail-meta">
                                    <span className="kb-detail-source">📰 {selectedKbItem.source_name}</span>
                                    {selectedKbItem.published_at && (
                                        <span className="kb-detail-date">📅 {new Date(selectedKbItem.published_at).toLocaleString()}</span>
                                    )}
                                </div>
                                <div className="kb-detail-content">
                                    {selectedKbItem.content}
                                </div>
                                {selectedKbItem.url && (
                                    <div className="kb-detail-actions">
                                        <a href={selectedKbItem.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline">
                                            查看原文 →
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Delete Confirmation Modal */}
            {
                showDeleteConfirm && itemToDelete && (
                    <div className="modal-overlay" onClick={handleCancelDelete}>
                        <div className="modal-content delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>确认删除</h2>
                                <button className="modal-close" onClick={handleCancelDelete}>×</button>
                            </div>
                            <div className="modal-body">
                                <p>确定要删除以下内容吗？</p>
                                <div className="delete-item-preview">
                                    <strong>{itemToDelete.title}</strong>
                                    <div className="delete-item-meta">
                                        <span>📰 {itemToDelete.source_name}</span>
                                    </div>
                                </div>
                                <p className="delete-warning">此操作无法撤销</p>
                            </div>
                            <div className="modal-footer">
                                <button className="btn btn-secondary" onClick={handleCancelDelete}>
                                    取消
                                </button>
                                <button className="btn btn-danger" onClick={handleConfirmDelete}>
                                    确认删除
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Delete Task Confirmation Modal */}
            {
                showDeleteTaskConfirm && (
                    <div className="modal-overlay" onClick={handleCancelDeleteTask}>
                        <div className="modal-content delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>确认删除任务</h2>
                                <button className="modal-close" onClick={handleCancelDeleteTask}>×</button>
                            </div>
                            <div className="modal-body">
                                <p>确定要删除任务 <strong>"{taskName}"</strong> 吗？</p>
                                <div className="delete-item-preview">
                                    <p>此操作将删除：</p>
                                    <ul>
                                        <li>任务配置</li>
                                        <li>所有知识库内容</li>
                                        <li>任务调度设置</li>
                                    </ul>
                                </div>
                                <p className="delete-warning">⚠️ 此操作无法撤销！</p>
                            </div>
                            <div className="modal-footer">
                                <button className="btn btn-secondary" onClick={handleCancelDeleteTask}>
                                    取消
                                </button>
                                <button className="btn btn-danger" onClick={handleConfirmDeleteTask}>
                                    确认删除任务
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    )
}

export default TaskDetail
