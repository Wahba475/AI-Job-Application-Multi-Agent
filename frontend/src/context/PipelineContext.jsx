import { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

const PipelineContext = createContext()
const JOB_ID_KEY = 'applyai_job_id'
const POLL_INTERVAL = 3000

const apiBase = () => `${import.meta.env.VITE_API_URL}/api`

const authHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const handleAuthError = (error) => {
  const status = error.response?.status
  if (status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    if (!['/login', '/register'].includes(window.location.pathname)) {
      window.location.assign('/login')
    }
  } else if (status === 429) {
    toast.error(error.response?.data?.detail || 'Too many requests. Please wait a moment.')
  }
}

export const usePipeline = () => {
  const context = useContext(PipelineContext)
  if (!context) throw new Error('usePipeline must be used within PipelineProvider')
  return context
}

export const PipelineProvider = ({ children }) => {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const pollTimer = useRef(null)

  const saveToHistory = (data) => {
    const summary = { ...data, jobs: undefined, timestamp: Date.now(), jobCount: data.approved_count }
    const history = JSON.parse(localStorage.getItem('applyai_history') || '[]')
    localStorage.setItem('applyai_history', JSON.stringify([summary, ...history].slice(0, 20)))
  }

  const pollJob = (jobId, stepTimers) => {
    pollTimer.current = setInterval(async () => {
      try {
        const { data: job } = await axios.get(`${apiBase()}/status/${jobId}`, {
          headers: authHeaders(),
        })
        if (job.status === 'running') return

        clearInterval(pollTimer.current)
        stepTimers?.forEach(clearTimeout)
        localStorage.removeItem(JOB_ID_KEY)
        setLoading(false)

        if (job.status === 'done') {
          setCurrentStep(5)
          setResults(job.result)
          saveToHistory(job.result)
          toast.success(`${job.result.approved_count} job${job.result.approved_count !== 1 ? 's' : ''} matched!`)
        } else {
          toast.error(job.error || 'Pipeline failed. Please try again.')
        }
      } catch (error) {
        clearInterval(pollTimer.current)
        localStorage.removeItem(JOB_ID_KEY)
        setLoading(false)
        handleAuthError(error)
        if (error.response?.status !== 429 && error.response?.status !== 401) {
          toast.error('Lost connection to the pipeline run.')
        }
      }
    }, POLL_INTERVAL)
  }

  useEffect(() => {
    const savedJobId = localStorage.getItem(JOB_ID_KEY)
    if (savedJobId) {
      setLoading(true)
      pollJob(savedJobId)
    }
    return () => clearInterval(pollTimer.current)
  }, [])

  const runPipeline = async (formData) => {
    setLoading(true)
    setCurrentStep(0)
    setResults(null)

    const stepTimers = [
      setTimeout(() => setCurrentStep(1), 5000),
      setTimeout(() => setCurrentStep(2), 15000),
      setTimeout(() => setCurrentStep(3), 35000),
    ]

    try {
      const { data } = await axios.post(`${apiBase()}/run-pipeline`, formData, {
        headers: {
          ...authHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      })
      localStorage.setItem(JOB_ID_KEY, data.job_id)
      pollJob(data.job_id, stepTimers)
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      setLoading(false)
      handleAuthError(err)
      if (err.response?.status !== 429 && err.response?.status !== 401) {
        toast.error(err?.response?.data?.detail || 'Pipeline failed. Please try again.')
      }
      throw err
    }
  }

  /** Authenticated file download (Bearer via header — not exposed in the URL). */
  const downloadFile = async (filename) => {
    try {
      const response = await axios.get(`${apiBase()}/download/${filename}`, {
        headers: authHeaders(),
        responseType: 'blob',
      })
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      handleAuthError(error)
      if (error.response?.status !== 429 && error.response?.status !== 401) {
        toast.error('Download failed.')
      }
    }
  }

  return (
    <PipelineContext.Provider
      value={{ results, loading, currentStep, runPipeline, setResults, downloadFile }}
    >
      {children}
    </PipelineContext.Provider>
  )
}
