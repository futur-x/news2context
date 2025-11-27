import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { taskAPI } from '../api/client'
import './Dashboard.css'

interface Task {
    name: string
    scene: string
    collection: string
    sources: any[]
    status: {
        enabled: boolean
        last_run: string | null
        total_runs: number
    }
    created_at: string
}

function Dashboard() {
    const [tasks, setTasks] = useState<Task[]>([])
    const [loading, setLoading] = useState(true)

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
                <button className="btn btn-primary">
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
                            <span className={`badge ${task.status.enabled ? 'badge-success' : 'badge-warning'}`}>
                                {task.status.enabled ? 'Active' : 'Paused'}
                            </span>
                        </div>

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
        </div>
    )
}

export default Dashboard
