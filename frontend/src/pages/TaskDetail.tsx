import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { taskAPI, externalAPI } from '../api/client'
import './TaskDetail.css'

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
                <button className="btn btn-primary" onClick={() => taskAPI.run(taskName!)}>
                    ▶ Run Now
                </button>
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
                </div>
            </div>
        </div>
    )
}

export default TaskDetail
