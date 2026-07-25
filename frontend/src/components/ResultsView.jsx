import { useState } from 'react'
import { Download, RotateCcw } from 'lucide-react'
import { usePipeline } from '../context/PipelineContext'
import JobCard from './JobCard'
import CVPreviewModal from './CVPreviewModal'

/**
 * Shared results view — used for both a live run (AppPage) and a past run
 * (HistoryPage). `results` shape:
 *   { history_id, approved_count, total_jobs, retry_rounds, jobs: [...] }
 * `onReset` is optional (shown as "New Search" on the live page).
 */
export default function ResultsView({ results, onReset }) {
  const [previewJob, setPreviewJob] = useState(null)
  const { downloadSpreadsheet } = usePipeline()
  const historyId = results.history_id
  const jobs = results.jobs || []

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div
        className="border border-mint-teal bg-secondary-container/20 p-6 mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
        data-aos="fade-up"
      >
        <div>
          <p className="font-body text-xs tracking-caps uppercase text-secondary mb-1">
            {onReset ? 'Pipeline complete' : 'Saved run'}
          </p>
          <p className="font-display font-semibold text-2xl text-ink">
            {results.approved_count} job{results.approved_count !== 1 ? 's' : ''} matched
          </p>
          <p className="font-body text-sm text-ink-muted mt-1">
            {results.total_jobs} found
            {typeof results.retry_rounds === 'number'
              ? ` · ${results.retry_rounds} validation round${results.retry_rounds !== 1 ? 's' : ''}`
              : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {historyId && (
            <button
              type="button"
              onClick={() => downloadSpreadsheet(historyId)}
              className="inline-flex items-center gap-2 h-btn px-5 border border-hairline text-ink font-body text-sm font-medium rounded-pill hover:bg-surface-dim transition-colors"
            >
              <Download size={14} /> Download Spreadsheet
            </button>
          )}
          {onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-2 h-btn px-5 bg-ink text-canvas font-body text-sm font-medium rounded-pill hover:bg-on-surface transition-colors"
            >
              <RotateCcw size={14} /> New Search
            </button>
          )}
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-16">
          <p className="font-body text-sm text-ink-muted">No jobs passed validation. Try a broader search.</p>
        </div>
      ) : (
        <div
          data-aos="fade-up"
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-px bg-outline-variant border border-outline-variant"
        >
          {jobs.map((job, i) => (
            <JobCard key={i} job={job} historyId={historyId} onPreview={setPreviewJob} />
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
