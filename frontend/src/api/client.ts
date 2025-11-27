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
    run: (name: string) => api.post(`/tasks/${name}/run`)
}

// Settings API
export const settingsAPI = {
    getSystem: () => api.get('/settings/system'),
    updateSystem: (data: any) => api.put('/settings/system', data),
    getTopHub: () => api.get('/settings/engines/tophub'),
    updateTopHub: (data: any) => api.put('/settings/engines/tophub', data)
}

// External API
export const externalAPI = {
    generateToken: () => api.post('/external/tokens'),
    listTokens: () => api.get('/external/tokens')
}

export default api
