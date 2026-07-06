import { useState, useEffect } from 'react'
import { Clock, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function HistoryPage() {
  const [history, setHistory] = useState([])

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('applyai_history') || '[]')
    setHistory(stored)
  }, [])

  const clearHistory = () => {
    localStorage.removeItem('applyai_history')
    setHistory([])
  }

  const formatDate = (ts) =>
    new Date(ts).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })

  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <div data-aos="fade-up" className="flex items-start justify-between gap-4 mb-10">
        <div>
          <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-2">Activity</p>
          <h1 className="font-display font-medium text-4xl text-ink tracking-tighter">Run history</h1>
        </div>
        {history.length > 0 && (
          <button
            onClick={clearHistory}
            className="inline-flex items-center gap-2 h-btn px-4 border border-hairline text-ink-muted font-body text-sm rounded-pill hover:text-error hover:border-error transition-colors"
          >
            <Trash2 size={14} /> Clear all
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div
          className="border border-outline-variant bg-canvas p-16 text-center"
          data-aos="fade-up"
        >
          <Clock size={32} className="text-surface-dim mx-auto mb-4" />
          <p className="font-body text-sm font-medium text-ink mb-2">No runs yet</p>
          <p className="font-body text-sm text-ink-muted mb-6">
            Your pipeline runs will appear here.
          </p>
          <Link
            to="/app"
            className="inline-flex items-center h-9 px-5 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
          >
            Start a run
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-px bg-outline-variant border border-outline-variant" data-aos="fade-up">
          {history.map((run, i) => (
            <div key={i} className="bg-canvas p-6 flex items-center justify-between gap-4">
              <div>
                <p className="font-body text-sm font-medium text-ink">
                  {run.jobCount ?? run.approved_count} job{(run.jobCount ?? run.approved_count) !== 1 ? 's' : ''} matched
                </p>
                <p className="font-body text-xs text-ink-muted mt-0.5">
                  {run.total_jobs} found · {formatDate(run.timestamp)}
                </p>
              </div>
              <span className="inline-flex items-center px-3 py-1 rounded-pill text-xs font-body font-medium bg-secondary-container text-secondary">
                Complete
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
