import { useState, useEffect } from 'react'
import { settingsAPI } from '../api/client'
import './Settings.css'

function Settings() {
    const [systemSettings, setSystemSettings] = useState({
        llm_provider: '',
        llm_api_key: '',
        llm_base_url: '',
        llm_model: '',
        weaviate_url: '',
        weaviate_api_key: ''
    })

    const [topHubSettings, setTopHubSettings] = useState({
        tophub_api_key: '',
        tophub_base_url: ''
    })

    const [embeddingSettings, setEmbeddingSettings] = useState({
        model: '',
        api_key: '',
        base_url: '',
        dimensions: 1536
    })

    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadSettings()
    }, [])

    const loadSettings = async () => {
        try {
            const [systemRes, topHubRes, embeddingRes] = await Promise.all([
                settingsAPI.getSystem(),
                settingsAPI.getTopHub(),
                settingsAPI.getEmbedding()
            ])
            setSystemSettings(systemRes.data)
            setTopHubSettings(topHubRes.data)
            setEmbeddingSettings(embeddingRes.data)
        } catch (error) {
            console.error('Failed to load settings:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveSystem = async () => {
        try {
            await settingsAPI.updateSystem(systemSettings)
            alert('System settings saved successfully')
        } catch (error) {
            console.error('Failed to save system settings:', error)
            alert('Failed to save settings')
        }
    }

    const handleSaveTopHub = async () => {
        try {
            await settingsAPI.updateTopHub(topHubSettings)
            alert('TopHub settings saved successfully')
        } catch (error) {
            console.error('Failed to save TopHub settings:', error)
            alert('Failed to save settings')
        }
    }

    const handleSaveEmbedding = async () => {
        try {
            await settingsAPI.updateEmbedding(embeddingSettings)
            alert('Embedding settings saved successfully')
        } catch (error) {
            console.error('Failed to save embedding settings:', error)
            alert('Failed to save settings')
        }
    }

    if (loading) {
        return <div className="loading">Loading settings...</div>
    }

    return (
        <div className="settings">
            <h1 className="page-title">Settings</h1>
            <p className="page-subtitle">Configure system and news engines</p>

            <div className="settings-grid">
                <div className="settings-section">
                    <h2 className="section-title">System Configuration</h2>
                    <div className="form-group">
                        <label>LLM Provider</label>
                        <input
                            type="text"
                            value={systemSettings.llm_provider}
                            onChange={(e) => setSystemSettings({ ...systemSettings, llm_provider: e.target.value })}
                            className="input"
                        />
                    </div>
                    <div className="form-group">
                        <label>LLM API Key</label>
                        <input
                            type="password"
                            value={systemSettings.llm_api_key}
                            onChange={(e) => setSystemSettings({ ...systemSettings, llm_api_key: e.target.value })}
                            className="input"
                        />
                    </div>
                    <div className="form-group">
                        <label>LLM Base URL</label>
                        <input
                            type="text"
                            value={systemSettings.llm_base_url}
                            onChange={(e) => setSystemSettings({ ...systemSettings, llm_base_url: e.target.value })}
                            className="input"
                        />
                    </div>
                    <div className="form-group">
                        <label>LLM Model</label>
                        <input
                            type="text"
                            value={systemSettings.llm_model}
                            onChange={(e) => setSystemSettings({ ...systemSettings, llm_model: e.target.value })}
                            className="input"
                        />
                    </div>
                    <button className="btn btn-primary" onClick={handleSaveSystem}>
                        Save System Settings
                    </button>
                </div>

                <div className="settings-section">
                    <h2 className="section-title">Embedding Model</h2>
                    <div className="form-group">
                        <label>Model</label>
                        <select
                            value={embeddingSettings.model}
                            onChange={(e) => setEmbeddingSettings({ ...embeddingSettings, model: e.target.value })}
                            className="input"
                        >
                            <option value="text-embedding-3-small">text-embedding-3-small (8191 tokens)</option>
                            <option value="text-embedding-3-large">text-embedding-3-large (8191 tokens)</option>
                            <option value="text-embedding-ada-002">text-embedding-ada-002 (8191 tokens)</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>API Key</label>
                        <input
                            type="password"
                            value={embeddingSettings.api_key}
                            onChange={(e) => setEmbeddingSettings({ ...embeddingSettings, api_key: e.target.value })}
                            className="input"
                            placeholder="Leave empty to use LLM API Key"
                        />
                    </div>
                    <div className="form-group">
                        <label>Base URL</label>
                        <input
                            type="text"
                            value={embeddingSettings.base_url}
                            onChange={(e) => setEmbeddingSettings({ ...embeddingSettings, base_url: e.target.value })}
                            className="input"
                        />
                    </div>
                    <div className="form-group">
                        <label>Dimensions</label>
                        <input
                            type="number"
                            value={embeddingSettings.dimensions}
                            onChange={(e) => setEmbeddingSettings({ ...embeddingSettings, dimensions: parseInt(e.target.value) })}
                            className="input"
                        />
                    </div>
                    <button className="btn btn-primary" onClick={handleSaveEmbedding}>
                        Save Embedding Settings
                    </button>
                </div>

                <div className="settings-section">
                    <h2 className="section-title">TopHub Engine</h2>
                    <div className="form-group">
                        <label>API Key</label>
                        <input
                            type="password"
                            value={topHubSettings.tophub_api_key}
                            onChange={(e) => setTopHubSettings({ ...topHubSettings, tophub_api_key: e.target.value })}
                            className="input"
                        />
                    </div>
                    <div className="form-group">
                        <label>Base URL</label>
                        <input
                            type="text"
                            value={topHubSettings.tophub_base_url}
                            onChange={(e) => setTopHubSettings({ ...topHubSettings, tophub_base_url: e.target.value })}
                            className="input"
                        />
                    </div>
                    <button className="btn btn-primary" onClick={handleSaveTopHub}>
                        Save TopHub Settings
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Settings
