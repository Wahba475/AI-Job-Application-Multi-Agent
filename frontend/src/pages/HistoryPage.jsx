import { useState, useEffect } from 'react'
import { Clock, Trash2, ChevronRight, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'
import ResultsView from '../components/ResultsView'

const apiBase = () => `${import.meta.env.VITE_API_URL}/api`
const authHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Map a DB history row into the shape ResultsView expects.
const toResults = (row) => ({
  history_id: row.id,
  approved_count: (row.jobs || []).length,
  total_jobs: (row.jobs || []).length,
  jobs: (row.jobs || []).map((j, i) => ({
    index: i,
    title: j.title,
    company: j.company,
    location: j.location,
    type: j.type,
    apply_link: j.apply_link,
    ats_score: j.ats_score,
    gaps: j.gaps,
    tailored: j.tailored,
    cv_filename: j.cv_filename,
    cv_text: j.cv_text || '',
  })),
})

export default function HistoryPage() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await axios.get(`${apiBase()}/history/`, { headers: authHeaders() })
      setRuns(data)
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.assign('/login')
      } else {
        toast.error('Could not load history.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const deleteRun = async (id, e) => {
    e.stopPropagation()
    try {
      await axios.delete(`${apiBase()}/history/${id}`, { headers: authHeaders() })
      setRuns((r) => r.filter((x) => x.id !== id))
      toast.success('Run deleted')
    } catch {
      toast.error('Could not delete run.')
    }
  }

  const formatDate = (ts) =>
    new Date(ts).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })

  // Detail view — reuse the exact live results component.
  if (selected) {
    return (
      <div className="max-w-6xl mx-auto px-6 pt-10">
        <button
          onClick={() => setSelected(null)}
          className="inline-flex items-center gap-1.5 font-body text-sm text-ink-muted hover:text-ink transition-colors"
        >
          <ArrowLeft size={15} /> Back to history
        </button>
        <ResultsView results={toResults(selected)} />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <div data-aos="fade-up" className="flex items-start justify-between gap-4 mb-10">
        <div>
          <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-2">Activity</p>
          <h1 className="font-display font-medium text-4xl text-ink tracking-tighter">Run history</h1>
        </div>
      </div>

      {loading ? (
        <p className="font-body text-sm text-ink-muted">Loading…</p>
      ) : runs.length === 0 ? (
        <div className="border border-outline-variant bg-canvas p-16 text-center" data-aos="fade-up">
          <Clock size={32} className="text-surface-dim mx-auto mb-4" />
          <p className="font-body text-sm font-medium text-ink mb-2">No runs yet</p>
          <p className="font-body text-sm text-ink-muted mb-6">Your pipeline runs will appear here.</p>
          <Link
            to="/app"
            className="inline-flex items-center h-9 px-5 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
          >
            Start a run
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-px bg-outline-variant border border-outline-variant" data-aos="fade-up">
          {runs.map((run) => {
            const count = (run.jobs || []).length
            return (
              <div
                key={run.id}
                onClick={() => setSelected(run)}
                className="bg-canvas p-6 flex items-center justify-between gap-4 cursor-pointer hover:bg-surface-dim/40 transition-colors"
              >
                <div>
                  <p className="font-body text-sm font-medium text-ink">
                    {run.job_title} · {count} job{count !== 1 ? 's' : ''}
                  </p>
                  <p className="font-body text-xs text-ink-muted mt-0.5">
                    {run.location || '—'} · {formatDate(run.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => deleteRun(run.id, e)}
                    className="text-ink-muted hover:text-error transition-colors"
                    title="Delete run"
                  >
                    <Trash2 size={15} />
                  </button>
                  <ChevronRight size={16} className="text-ink-muted" />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
