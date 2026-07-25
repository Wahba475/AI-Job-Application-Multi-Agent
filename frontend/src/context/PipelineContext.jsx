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

// Map a pipeline node name (from GET /status) to the loading-step index.
const STEP_INDEX = {
  search_jobs: 0,
  filter_relevance: 1,
  tailor_cv: 2,
  validate_ats: 3,
  build_deliverable: 4,
  uploading: 4,
  done: 5,
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

  const pollJob = (jobId) => {
    pollTimer.current = setInterval(async () => {
      try {
        const { data: job } = await axios.get(`${apiBase()}/status/${jobId}`, {
          headers: authHeaders(),
        })

        // Live step progress from the backend.
        if (job.step && job.step in STEP_INDEX) setCurrentStep(STEP_INDEX[job.step])

        if (job.status === 'running') return

        clearInterval(pollTimer.current)
        localStorage.removeItem(JOB_ID_KEY)
        setLoading(false)

        if (job.status === 'done') {
          setCurrentStep(5)
          setResults(job.result)
          const n = job.result.approved_count
          toast.success(`${n} job${n !== 1 ? 's' : ''} matched!`)
        } else {
          toast.error(job.error || 'Pipeline failed. Please try again.')
        }
      } catch (error) {
        clearInterval(pollTimer.current)
        localStorage.removeItem(JOB_ID_KEY)
        setLoading(false)
        handleAuthError(error)
        if (![429, 401].includes(error.response?.status)) {
          toast.error('Lost connection to the pipeline run.')
        }
      }
    }, POLL_INTERVAL)
  }

  // Resume an in-flight run after a page refresh.
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
    try {
      const { data } = await axios.post(`${apiBase()}/run-pipeline`, formData, {
        headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' },
      })
      localStorage.setItem(JOB_ID_KEY, data.job_id)
      pollJob(data.job_id)
    } catch (err) {
      setLoading(false)
      handleAuthError(err)
      if (![429, 401].includes(err.response?.status)) {
        toast.error(err?.response?.data?.detail || 'Pipeline failed. Please try again.')
      }
      throw err
    }
  }

  /** Download one job's tailored CV via the auth-protected history endpoint. */
  const downloadCv = async (historyId, jobIndex, filename) => {
    try {
      const res = await axios.get(`${apiBase()}/history/${historyId}/cv/${jobIndex}`, {
        headers: authHeaders(),
        responseType: 'blob',
      })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'CV.docx'
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      handleAuthError(error)
      if (![429, 401].includes(error.response?.status)) toast.error('CV download failed.')
    }
  }

  /** Open the run's spreadsheet via a fresh signed URL. */
  const downloadSpreadsheet = async (historyId) => {
    try {
      const { data } = await axios.get(`${apiBase()}/history/${historyId}/download`, {
        headers: authHeaders(),
      })
      if (data.download_url) window.open(data.download_url, '_blank')
      else toast.error('Spreadsheet unavailable.')
    } catch (error) {
      handleAuthError(error)
      if (![429, 401].includes(error.response?.status)) toast.error('Spreadsheet download failed.')
    }
  }

  return (
    <PipelineContext.Provider
      value={{ results, loading, currentStep, runPipeline, setResults,
               downloadCv, downloadSpreadsheet }}
    >
      {children}
    </PipelineContext.Provider>
  )
}
