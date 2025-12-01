import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { taskAPI } from '../api/client'
import TaskWizard from '../components/TaskWizard'
import './Dashboard.css'

interface Task {
    name: string
    scene: string
    collection: string
    sources: any[]
    status: {
        enabled: boolean
        running?: boolean
        current_status?: string
        progress?: {
            total_sources: number
            processed_sources: number
            collected_articles: number
            start_time: string
        }
        last_run: string | null
        total_runs: number
        last_success_count?: number
        last_error?: string | null
    }
    created_at: string
}

function Dashboard() {
    const [tasks, setTasks] = useState<Task[]>([])
    const [loading, setLoading] = useState(true)
    const [showWizard, setShowWizard] = useState(false)
    const navigate = useNavigate()

    useEffect(() => {
        loadTasks()
    }, [])

    const loadTasks = async () => {
        try {
            const response = await taskAPI.list()
            setTasks(response.data.tasks)
        } catch (error) {
            console.error('Failed to load tasks:', error)
        } finally {
            setLoading(false)
        }
    }

    // Removed unused handleTaskCreated function
    // Now using onSuccess callback in TaskWizard directly

    if (loading) {
        return (
            <div className="dashboard">
                <div className="loading">Loading tasks...</div>
            </div>
        )
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <div>
                    <h1 className="page-title">Knowledge Bases</h1>
                    <p className="page-subtitle">Manage your news knowledge bases</p>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => setShowWizard(true)}
                >
                    + Create New
                </button>
            </div>

            <div className="task-grid">
                {tasks.map((task) => (
                    <Link
                        key={task.name}
                        to={`/tasks/${task.name}`}
                        className="task-card"
                    >
                        <div className="task-card-header">
                            <h3 className="task-name">{task.name}</h3>
                            <div className="status-badges">
                                {task.status.running && (
                                    <span className="badge badge-running">● Running</span>
                                )}
                                {!task.status.running && task.status.current_status === 'success' && (
                                    <span className="badge badge-success">✓ Success</span>
                                )}
                                {!task.status.running && task.status.current_status === 'error' && (
                                    <span className="badge badge-error">✗ Error</span>
                                )}
                                {task.status.enabled && !task.status.running && task.status.current_status === 'idle' && (
                                    <span className="badge badge-idle">Idle</span>
                                )}
                            </div>
                        </div>

                        {task.status.running && task.status.progress && (
                            <div className="task-progress">
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{
                                            width: `${(task.status.progress.processed_sources / task.status.progress.total_sources) * 100}%`
                                        }}
                                    />
                                </div>
                                <div className="progress-text">
                                    {task.status.progress.processed_sources}/{task.status.progress.total_sources} sources •
                                    {task.status.progress.collected_articles} articles
                                </div>
                            </div>
                        )}

                        <p className="task-scene">{task.scene}</p>

                        <div className="task-stats">
                            <div className="stat">
                                <span className="stat-label">Sources</span>
                                <span className="stat-value">{task.sources.length}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Runs</span>
                                <span className="stat-value">{task.status.total_runs}</span>
                            </div>
                            {task.status.last_success_count && task.status.last_success_count > 0 && (
                                <div className="stat">
                                    <span className="stat-label">Last</span>
                                    <span className="stat-value">{task.status.last_success_count}</span>
                                </div>
                            )}
                        </div>

                        {task.status.last_run && (
                            <div className="task-footer">
                                <span className="last-run">
                                    Last run: {new Date(task.status.last_run).toLocaleDateString()}
                                </span>
                            </div>
                        )}
                    </Link>
                ))}
            </div>

            {tasks.length === 0 && (
                <div className="empty-state">
                    <h3>No knowledge bases yet</h3>
                    <p>Create your first knowledge base to get started</p>
                </div>
            )}

            {showWizard && (
                <TaskWizard
                    onClose={() => setShowWizard(false)}
                    onSuccess={() => loadTasks()}
                />
            )}
        </div>
    )
}

export default Dashboard
