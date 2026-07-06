import { MapPin, Briefcase, ExternalLink, Eye, Download } from 'lucide-react'
import { getDownloadUrl } from '../services/api'

export default function JobCard({ job, onPreview }) {
  const score = typeof job.ats_score === 'number' ? job.ats_score : parseInt(job.ats_score) || 0

  const scoreBadge =
    score >= 70
      ? 'bg-secondary-container text-secondary'
      : score >= 55
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-red-100 text-error'

  return (
    <div
      className="bg-canvas border border-hairline hover:shadow-lg transition-shadow"
      style={{ padding: '40px 32px 40px' }}
>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-display font-semibold text-lg text-ink leading-tight">{job.title}</h3>
          <p className="font-body text-sm font-medium text-ink-muted mt-0.5">{job.company}</p>
        </div>
        <span className={`flex-shrink-0 inline-flex items-center px-3 py-1 rounded-pill text-xs font-body font-medium ${scoreBadge}`}>
          ATS {score}%
        </span>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {job.location && (
          <span className="inline-flex items-center gap-1.5 font-body text-xs text-ink-muted">
            <MapPin size={12} /> {job.location}
          </span>
        )}
        {job.type && (
          <span className="inline-flex items-center gap-1.5 font-body text-xs text-ink-muted">
            <Briefcase size={12} /> {job.type}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {job.apply_link && (
          <a
            href={job.apply_link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 h-9 px-4 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
          >
            <ExternalLink size={13} /> Apply Now
          </a>
        )}

        <button
          type="button"
          onClick={() => onPreview(job)}
          className="inline-flex items-center gap-1.5 h-9 px-4 border border-hairline text-ink font-body text-sm font-medium rounded-pill hover:bg-surface-dim transition-colors"
        >
          <Eye size={13} /> Preview CV
        </button>

        <a
          href={getDownloadUrl(job.cv_filename)}
          download={job.cv_filename}
          className="inline-flex items-center gap-1.5 h-9 px-4 border border-hairline text-ink font-body text-sm font-medium rounded-pill hover:bg-surface-dim transition-colors"
        >
          <Download size={13} /> Download CV
        </a>
      </div>
    </div>
  )
}
