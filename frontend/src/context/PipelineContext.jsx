import { createContext, useContext, useState } from 'react'
import toast from 'react-hot-toast'
import { runPipeline as apiRunPipeline } from '../services/api'

const PipelineContext = createContext()

export const usePipeline = () => {
  const context = useContext(PipelineContext)
  if (!context) throw new Error('usePipeline must be used within PipelineProvider')
  return context
}

export const PipelineProvider = ({ children }) => {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  const runPipeline = async (formData) => {
    setLoading(true)
    setCurrentStep(0)

    const stepTimers = [
      setTimeout(() => setCurrentStep(1), 5000),
      setTimeout(() => setCurrentStep(2), 15000),
      setTimeout(() => setCurrentStep(3), 35000),
      setTimeout(() => setCurrentStep(4), 55000),
    ]

    try {
      const data = await apiRunPipeline(formData)
      stepTimers.forEach(clearTimeout)
      setCurrentStep(5)
      setResults(data)

      const summary = { ...data, jobs: undefined, timestamp: Date.now(), jobCount: data.approved_count }
      const history = JSON.parse(localStorage.getItem('applyai_history') || '[]')
      localStorage.setItem('applyai_history', JSON.stringify([summary, ...history].slice(0, 20)))

      toast.success(`${data.approved_count} job${data.approved_count !== 1 ? 's' : ''} matched!`)
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      toast.error(err?.response?.data?.detail || 'Pipeline failed. Please try again.')
      throw err
    } finally {
      setLoading(false)
    }
  }

  return (
    <PipelineContext.Provider value={{ results, loading, currentStep, runPipeline, setResults }}>
      {children}
    </PipelineContext.Provider>
  )
}
