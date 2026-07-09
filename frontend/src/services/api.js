import axios from 'axios'

const API = axios.create({
  baseURL: 'http://localhost:8001/api',
})

export const startPipeline = async (formData) => {
  const response = await API.post('/run-pipeline', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getPipelineStatus = async (jobId) => {
  const response = await API.get(`/status/${jobId}`)
  return response.data
}

export const getDownloadUrl = (filename) => {
  return `${API.defaults.baseURL}/download/${filename}`
}
