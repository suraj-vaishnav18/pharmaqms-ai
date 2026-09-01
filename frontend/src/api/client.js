import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export const listComplaints = () => api.get('/complaints/').then(r => r.data)
export const getComplaint = (id) => api.get(`/complaints/${id}`).then(r => r.data)
export const createComplaint = (payload) => api.post('/complaints/', payload).then(r => r.data)
export const runAiPipeline = (id) => api.post(`/complaints/${id}/run-ai-pipeline`).then(r => r.data)
export const getAiTrace = (id) => api.get(`/complaints/${id}/ai-trace`).then(r => r.data)
export const createCapa = (payload) => api.post('/capa/', payload).then(r => r.data)
export const listCapaForComplaint = (id) => api.get(`/capa/by-complaint/${id}`).then(r => r.data)

// AI Intake Copilot
export const copilotExtractText = (text) => api.post('/copilot/extract-text', { text }).then(r => r.data)
export const copilotExtractFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/copilot/extract-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
export const copilotChat = (message, currentFields) =>
  api.post('/copilot/chat', { message, current_fields: currentFields }).then(r => r.data)
