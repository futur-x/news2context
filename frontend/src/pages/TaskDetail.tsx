import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { taskAPI, externalAPI, chatAPI } from '../api/client'
import api from '../api/client'
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
    const [task, setTask] = useState<Task | null>(null)
    const [apiToken, setApiToken] = useState<string>('')
    const [loading, setLoading] = useState(true)

    // Search state
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState<any[]>([])
    const [searching, setSearching] = useState(false)

    // Chat state
    const [chatMessage, setChatMessage] = useState('')
    const [chatHistory, setChatHistory] = useState<any[]>([])
    const [chatting, setChatting] = useState(false)

    useEffect(() => {
        if (taskName) {
            loadTask()
        }
    }, [taskName])

    const loadTask = async () => {
        try {
            const response = await taskAPI.get(taskName!)
            setTask(response.data)
        } catch (error) {
            console.error('Failed to load task:', error)
        } finally {
            setLoading(false)
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
        if (!confirm(`确定要删除任务 "${taskName}" 吗？此操作不可撤销。`)) {
            return
        }

        try {
            await taskAPI.delete(taskName!)
            alert('任务已删除')
            window.location.href = '/'
        } catch (error) {
            console.error('Failed to delete task:', error)
            alert('删除失败')
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
                limit: 5
            })
            setSearchResults(response.data.results || [])
        } catch (error) {
            console.error('Search failed:', error)
            alert('搜索失败')
        } finally {
            setSearching(false)
        }
    }

    const handleChat = async () => {
        if (!chatMessage.trim()) return

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
                    <button className="btn btn-primary" onClick={() => taskAPI.run(taskName!)}>
                        ▶ Run Now
                    </button>
                    <button className="btn btn-secondary" style={{ color: 'var(--color-accent-error)' }} onClick={handleDeleteTask}>
                        🗑️ Delete
                    </button>
                </div>
            </div>

            <div className="detail-grid">
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
                                    onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                                    disabled={chatting}
                                />
                                <button
                                    className="btn btn-primary"
                                    onClick={handleChat}
                                    disabled={chatting || !chatMessage.trim()}
                                >
                                    发送
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TaskDetail
