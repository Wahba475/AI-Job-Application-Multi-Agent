import { Check } from 'lucide-react'

const STEPS = [
  { label: 'Searching jobs', sub: 'Scanning job boards for matching roles' },
  { label: 'Filtering results', sub: 'Ranking by relevance and requirements' },
  { label: 'Tailoring CVs', sub: 'Optimising each CV for the job posting' },
  { label: 'Validating ATS scores', sub: 'Checking scores ≥ 70% and no fabrication' },
  { label: 'Building deliverables', sub: 'Generating DOCX files and spreadsheet' },
]

export default function LoadingSteps({ currentStep }) {
  return (
    <div className="flex flex-col gap-4 w-full max-w-md">
      {STEPS.map((step, i) => {
        const done = i < currentStep
        const active = i === currentStep

        return (
          <div key={i} className="flex items-start gap-4">
            <div className={`mt-0.5 w-6 h-6 rounded-pill flex items-center justify-center flex-shrink-0 transition-colors
              ${done ? 'bg-mint-teal' : active ? 'bg-ink' : 'bg-surface-dim'}`}
            >
              {done
                ? <Check size={14} className="text-canvas" strokeWidth={2.5} />
                : <span className={`w-2 h-2 rounded-pill ${active ? 'bg-canvas animate-pulse' : 'bg-ink-muted'}`} />
              }
            </div>
            <div>
              <p className={`font-body text-sm font-medium transition-colors ${done || active ? 'text-ink' : 'text-ink-muted'}`}>
                {step.label}
              </p>
              {active && (
                <p className="font-body text-xs text-ink-muted mt-0.5">{step.sub}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
