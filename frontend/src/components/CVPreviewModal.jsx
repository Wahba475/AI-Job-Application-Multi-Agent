import { useEffect } from 'react'
import { X, Download } from 'lucide-react'
import { usePipeline } from '../context/PipelineContext'

export default function CVPreviewModal({ isOpen, onClose, jobData }) {
  const { downloadFile } = usePipeline()

  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  if (!isOpen || !jobData) return null

  const score = typeof jobData.ats_score === 'number' ? jobData.ats_score : parseInt(jobData.ats_score) || 0
  const scoreBadge =
    score >= 70 ? 'bg-secondary-container text-secondary'
    : score >= 55 ? 'bg-yellow-100 text-yellow-800'
    : 'bg-red-100 text-error'

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-canvas w-full max-w-3xl max-h-[90vh] flex flex-col border border-hairline">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 p-6 border-b border-hairline flex-shrink-0">
          <div>
            <h2 className="font-display font-semibold text-lg text-ink">{jobData.title}</h2>
            <p className="font-body text-sm text-ink-muted mt-0.5">{jobData.company}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-pill text-xs font-body font-medium ${scoreBadge}`}>
              ATS {score}%
            </span>
            <button
              onClick={onClose}
              className="text-ink-muted hover:text-ink transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 no-scrollbar">
          {jobData.cv_text ? (
            <pre className="font-body text-sm text-on-surface whitespace-pre-wrap leading-relaxed">
              {jobData.cv_text}
            </pre>
          ) : (
            <p className="font-body text-sm text-ink-muted">No preview available. Download to view.</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-hairline flex-shrink-0">
          <button
            onClick={onClose}
            className="h-btn px-5 border border-hairline font-body text-sm font-medium text-ink rounded-pill hover:bg-surface-dim transition-colors"
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => downloadFile(jobData.cv_filename)}
            className="inline-flex items-center gap-2 h-btn px-5 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
          >
            <Download size={14} /> Download CV
          </button>
        </div>
      </div>
    </div>
  )
}
