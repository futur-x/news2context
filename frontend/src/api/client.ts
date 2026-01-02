import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json'
    }
})

// Task API
export const taskAPI = {
    list: () => api.get('/tasks'),
    get: (name: string) => api.get(`/tasks/${name}`),
    create: (data: any) => api.post('/tasks', data),
    update: (name: string, data: any) => api.put(`/tasks/${name}`, data),
    delete: (name: string) => api.delete(`/tasks/${name}`),
    run: (name: string) => api.post(`/tasks/${name}/run`),
    status: (name: string) => api.get(`/tasks/${name}/status`),
    browse: (name: string, options?: { limit?: number; offset?: number }) =>
        api.get(`/tasks/${name}/browse`, { params: options }),
    addSources: (name: string, sources: string[]) => api.post(`/tasks/${name}/sources`, { sources })
}

// Settings API
export const settingsAPI = {
    getSystem: () => api.get('/settings/system'),
    updateSystem: (data: any) => api.put('/settings/system', data),
    getTopHub: () => api.get('/settings/engines/tophub'),
    updateTopHub: (data: any) => api.put('/settings/engines/tophub', data),
    getEmbedding: () => api.get('/settings/embedding'),
    updateEmbedding: (data: any) => api.put('/settings/embedding', data)
}

// External API
export const externalAPI = {
    generateToken: () => api.post('/external/tokens'),
    listTokens: () => api.get('/external/tokens'),
    deleteToken: (tokenHash: string) => api.delete(`/external/tokens/${tokenHash}`),
    updateTokenNote: (tokenHash: string, note: string | null) => api.put(`/external/tokens/${tokenHash}/note`, { note }),
    query: (taskName: string, data: any) => api.post(`/external/${taskName}/query`, data)
}

// Chat API
export const sourcesAPI = {
    list: () => api.get('/sources'),
    recommend: (scene: string, maxSources: number = 10) => api.post('/sources/recommend', { scene, max_sources: maxSources })
}

export const chatAPI = {
    sendMessage: (data: any) => api.post('/chat', data)
}

export default api
