import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { taskAPI } from '../api/client'
import SourceSelector from '../components/SourceSelector'
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
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [creating, setCreating] = useState(false)
    const [newTask, setNewTask] = useState({
        name: '',
        scene: '',
        sources: [] as string[],
        cron: '0 8 * * *'
    })

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

    const handleCreateTask = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!newTask.name || !newTask.scene || newTask.sources.length === 0) {
            alert('Please fill in all required fields')
            return
        }

        setCreating(true)
        try {
            // Convert selected source hashids to TaskSource objects
            // Note: The backend expects a list of source objects with name and hashid
            // But SourceSelector only gives us hashids. We rely on the backend to look up details 
            // OR we need to fetch source details here. 
            // Actually, looking at CreateTaskRequest in models.py, it expects 'sources: List[TaskSource]'.
            // So we need to map hashids to full source objects.
            // Let's fetch sources first or pass full objects from SourceSelector.
            // For simplicity, let's modify SourceSelector to return full objects or fetch them here.
            // Wait, SourceSelector fetches sources internally. 
            // Let's assume for now we can get source details. 
            // Actually, the backend might accept just hashids if we modify it, but let's stick to the contract.
            // I'll fetch sources in Dashboard to map them.

            // Re-fetching sources here to map hashids to names
            const settingsRes = await import('../api/client').then(m => m.settingsAPI.getTopHub())
            const allSources = settingsRes.data.sources || []
            const selectedSourceObjects = allSources
                .filter((s: any) => newTask.sources.includes(s.hashid))
                .map((s: any) => ({
                    name: s.name,
                    hashid: s.hashid,
                    category: s.category
                }))

            await taskAPI.create({
                ...newTask,
                sources: selectedSourceObjects,
                date_range: 'today',
                engine_name: 'tophub'
            })

            setShowCreateModal(false)
            setNewTask({ name: '', scene: '', sources: [], cron: '0 8 * * *' })
            loadTasks()
        } catch (error) {
            console.error('Failed to create task:', error)
            alert('Failed to create task')
        } finally {
            setCreating(false)
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
                <button
                    className="btn btn-primary"
                    onClick={() => setShowCreateModal(true)}
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

            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2>Create New Knowledge Base</h2>
                            <button
                                className="close-btn"
                                onClick={() => setShowCreateModal(false)}
                            >
                                ×
                            </button>
                        </div>
                        <form onSubmit={handleCreateTask}>
                            <div className="form-group">
                                <label>Name (English ID)</label>
                                <input
                                    type="text"
                                    value={newTask.name}
                                    onChange={e => setNewTask({ ...newTask, name: e.target.value })}
                                    placeholder="e.g., tech-news"
                                    required
                                    pattern="[a-zA-Z0-9-_]+"
                                />
                                <small>Only letters, numbers, hyphens and underscores</small>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <input
                                    type="text"
                                    value={newTask.scene}
                                    onChange={e => setNewTask({ ...newTask, scene: e.target.value })}
                                    placeholder="e.g., Latest technology trends"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Sources</label>
                                <SourceSelector
                                    selectedSources={newTask.sources}
                                    onChange={(sources) => setNewTask({ ...newTask, sources })}
                                    scene={newTask.scene}
                                />
                            </div>
                            <div className="form-group">
                                <label>Schedule (Cron)</label>
                                <input
                                    type="text"
                                    value={newTask.cron}
                                    onChange={e => setNewTask({ ...newTask, cron: e.target.value })}
                                    placeholder="0 8 * * *"
                                    required
                                />
                            </div>
                            <div className="modal-actions">
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={() => setShowCreateModal(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={creating}
                                >
                                    {creating ? 'Creating...' : 'Create Task'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Dashboard
