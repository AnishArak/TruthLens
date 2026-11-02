import axios from 'axios'

// In dev, Vite proxies /api to Flask. Set VITE_API_URL to point somewhere else (e.g. a deployed backend).
const http = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api', timeout: 120000 })

/** Turn any axios failure into a readable Error carrying the backend's code/status. */
function unwrap(promise) {
  return promise
    .then((r) => r.data)
    .catch((err) => {
      const apiErr = err.response?.data?.error
      const e = new Error(
        apiErr?.message ||
          (err.code === 'ERR_NETWORK' ? 'Cannot reach the backend. Is Flask running on port 5000?' : err.message)
      )
      e.code = apiErr?.code || err.code
      e.status = err.response?.status
      throw e
    })
}

export const api = {
  health: () => unwrap(http.get('/health')),
  dashboard: () => unwrap(http.get('/dashboard')),
  modelMetrics: () => unwrap(http.get('/model-metrics')),
  analyze: (payload) => unwrap(http.post('/analyze', payload)),
  analyzeUrl: (url) => unwrap(http.post('/analyze-url', { url })),
  source: (url) => unwrap(http.post('/source', { url })),
  history: (params) => unwrap(http.get('/history', { params })),
  historyItem: (id) => unwrap(http.get(`/history/${id}`)),
  deleteHistory: (id) => unwrap(http.delete(`/history/${id}`)),
}
