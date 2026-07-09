import { createContext, useContext, useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { startPipeline, getPipelineStatus } from '../services/api'

const PipelineContext = createContext()
const JOB_ID_KEY = 'applyai_job_id'
const POLL_INTERVAL = 3000

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
        const job = await getPipelineStatus(jobId)
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
      } catch {
        clearInterval(pollTimer.current)
        localStorage.removeItem(JOB_ID_KEY)
        setLoading(false)
        toast.error('Lost connection to the pipeline run.')
      }
    }, POLL_INTERVAL)
  }

  // Resume an in-flight job after a page refresh instead of losing track of it
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

    // Capped at step 3 ("Validating ATS scores") — that step can loop through
    // several retry rounds and take minutes, so it's the honest place to sit
    // rather than falsely advancing to "Building deliverables" (near-instant)
    // while the backend is still mid-retry.
    const stepTimers = [
      setTimeout(() => setCurrentStep(1), 5000),
      setTimeout(() => setCurrentStep(2), 15000),
      setTimeout(() => setCurrentStep(3), 35000),
    ]

    try {
      const { job_id } = await startPipeline(formData)
      localStorage.setItem(JOB_ID_KEY, job_id)
      pollJob(job_id, stepTimers)
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      setLoading(false)
      toast.error(err?.response?.data?.detail || 'Pipeline failed. Please try again.')
      throw err
    }
  }

  return (
    <PipelineContext.Provider value={{ results, loading, currentStep, runPipeline, setResults }}>
      {children}
    </PipelineContext.Provider>
  )
}
