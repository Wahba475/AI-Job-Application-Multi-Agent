import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Download, RotateCcw } from 'lucide-react'

import { usePipeline } from '../context/PipelineContext'
import FileUpload from '../components/FileUpload'
import LoadingSteps from '../components/LoadingSteps'
import JobCard from '../components/JobCard'
import CVPreviewModal from '../components/CVPreviewModal'
import { getDownloadUrl } from '../services/api'

const EXPERIENCE_OPTIONS = [
  'Entry Level (0–2 years)',
  'Mid Level (3–5 years)',
  'Senior (5–8 years)',
  'Lead / Principal (8+ years)',
]

// ── Form ────────────────────────────────────────────────────────────────────
function FormState({ onSubmit }) {
  const [jobTitle, setJobTitle] = useState('')
  const [location, setLocation] = useState('')
  const [experience, setExperience] = useState('')
  const [file, setFile] = useState(null)

  const inputClass =
    'w-full h-12 px-4 border border-hairline rounded-md font-body text-sm text-ink bg-canvas placeholder:text-ink-muted focus:outline-none focus:ring-1 focus:ring-ink transition'

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!jobTitle || !location || !experience || !file) {
      toast.error('Fill in all fields and upload your CV.')
      return
    }
    onSubmit({ jobTitle, location, experience, file })
  }

  return (
    <div className="max-w-xl mx-auto px-6 py-20">
      <div data-aos="fade-up">
        <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-3">New run</p>
        <h1 className="font-display font-medium text-4xl text-ink tracking-tighter mb-2">
          Find your next role.
        </h1>
        <p className="font-body text-sm text-ink-muted mb-10">
          Fill in the details and upload your CV. The pipeline handles the rest.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="font-body text-xs font-medium text-ink-muted uppercase tracking-caps block mb-1.5">
              Job Title
            </label>
            <input
              type="text"
              placeholder="e.g. Software Engineer"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="font-body text-xs font-medium text-ink-muted uppercase tracking-caps block mb-1.5">
              Location
            </label>
            <input
              type="text"
              placeholder="e.g. London, UK or Remote"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="font-body text-xs font-medium text-ink-muted uppercase tracking-caps block mb-1.5">
              Experience Level
            </label>
            <select
              value={experience}
              onChange={(e) => setExperience(e.target.value)}
              className={inputClass}
            >
              <option value="">Select experience level</option>
              {EXPERIENCE_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-body text-xs font-medium text-ink-muted uppercase tracking-caps block mb-1.5">
              Your CV
            </label>
            <FileUpload file={file} setFile={setFile} />
          </div>

          <button
            type="submit"
            className="mt-2 w-full h-btn bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors"
          >
            Run Pipeline
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Loading ──────────────────────────────────────────────────────────────────
function LoadingState({ currentStep }) {
  return (
    <div className="max-w-lg mx-auto px-6 py-24 flex flex-col items-center text-center">
      <div className="w-12 h-12 border-2 border-ink border-t-transparent rounded-pill animate-spin mb-8" />
      <h2 className="font-display font-medium text-2xl text-ink tracking-tight mb-2">
        Processing your application
      </h2>
      <p className="font-body text-sm text-ink-muted mb-10">
        This takes a few minutes. Don't close this tab.
      </p>
      <LoadingSteps currentStep={currentStep} />
    </div>
  )
}

// ── Results ──────────────────────────────────────────────────────────────────
function ResultsState({ results, onReset }) {
  const [previewJob, setPreviewJob] = useState(null)

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      {/* Summary banner */}
      <div
        className="border border-mint-teal bg-secondary-container/20 p-6 mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
        data-aos="fade-up"
      >
        <div>
          <p className="font-body text-xs tracking-caps uppercase text-secondary mb-1">Pipeline complete</p>
          <p className="font-display font-semibold text-2xl text-ink">
            {results.approved_count} job{results.approved_count !== 1 ? 's' : ''} matched
          </p>
          <p className="font-body text-sm text-ink-muted mt-1">
            {results.total_jobs} found · {results.retry_rounds} validation round{results.retry_rounds !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            href={getDownloadUrl(results.spreadsheet_download)}
            download
            className="inline-flex items-center gap-2 h-btn px-5 border border-hairline text-ink font-body text-sm font-medium rounded-pill hover:bg-surface-dim transition-colors"
          >
            <Download size={14} /> Download Spreadsheet
          </a>
          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 h-btn px-5 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
          >
            <RotateCcw size={14} /> New Search
          </button>
        </div>
      </div>

      {/* Job grid */}
      {results.jobs.length === 0 ? (
        <div className="text-center py-16">
          <p className="font-body text-sm text-ink-muted">No jobs passed validation. Try a broader search.</p>
        </div>
      ) : (
        <div
          data-aos="fade-up"
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-px bg-outline-variant border border-outline-variant"
        >
          {results.jobs.map((job, i) => (
            <JobCard key={i} job={job} onPreview={setPreviewJob} />
          ))}
        </div>
      )}

      <CVPreviewModal
        isOpen={!!previewJob}
        onClose={() => setPreviewJob(null)}
        jobData={previewJob}
      />
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function AppPage() {
  const { results, loading, currentStep, runPipeline, setResults } = usePipeline()
  const [pageState, setPageState] = useState('form')

  const handleSubmit = async ({ jobTitle, location, experience, file }) => {
    const formData = new FormData()
    formData.append('job_title', jobTitle)
    formData.append('location', location)
    formData.append('experience', experience)
    formData.append('cv_file', file)

    setPageState('loading')
    try {
      await runPipeline(formData)
      setPageState('results')
    } catch {
      setPageState('form')
    }
  }

  const handleReset = () => {
    setResults(null)
    setPageState('form')
  }

  if (pageState === 'loading' || loading) return <LoadingState currentStep={currentStep} />
  if (pageState === 'results' && results) return <ResultsState results={results} onReset={handleReset} />
  return <FormState onSubmit={handleSubmit} />
}
