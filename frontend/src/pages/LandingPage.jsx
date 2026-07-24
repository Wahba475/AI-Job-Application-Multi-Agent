import { Link } from 'react-router-dom'
import { Search, Filter, FileText, ShieldCheck, Zap, Target, Clock, Download } from 'lucide-react'

const STEPS = [
  { icon: Search, title: 'Search', desc: 'Scans job boards for roles matching your title, location, and experience level.' },
  { icon: Filter, title: 'Filter', desc: 'Ranks and filters results by relevance, discarding low-quality listings.' },
  { icon: FileText, title: 'Tailor', desc: 'Rewrites your CV sections to maximise ATS match score for each job.' },
  { icon: ShieldCheck, title: 'Validate', desc: 'Scores every CV ≥ 70% and checks for fabrication before delivery.' },
]

const FEATURES = [
  { icon: Zap, title: 'Fully automated', desc: 'One upload, one click — the entire pipeline runs without you.' },
  { icon: Target, title: 'ATS-optimised', desc: 'Each CV is scored and rewritten until it passes the 70% threshold.' },
  { icon: ShieldCheck, title: 'No fabrication', desc: 'Hard guardrails prevent invented skills, metrics, or companies.' },
  { icon: Clock, title: 'Minutes not hours', desc: 'What takes days of manual work is done while you grab coffee.' },
  { icon: Download, title: 'Ready to send', desc: 'Receive polished DOCX files and a job-tracker spreadsheet.' },
  { icon: FileText, title: 'Full transparency', desc: 'Preview every tailored CV before downloading or applying.' },
]

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="hero-gradient min-h-[88vh] flex items-center">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <div data-aos="fade-up">
            <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-8">
              AI-powered job applications
            </p>
            <h1 className="font-display font-light text-5xl md:text-7xl lg:text-8xl text-ink leading-none tracking-tighter mb-8 max-w-4xl">
              Land your dream job.{' '}
              <span className="text-mint-teal">Automatically.</span>
            </h1>
            <p className="font-body text-lg font-light text-ink-muted max-w-xl leading-relaxed mb-12">
              Upload your CV. Set your target role. ApplyAI searches, filters,
              tailors, and validates — delivering job-ready applications while you focus on what matters.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                to="/register"
                className="inline-flex items-center h-btn px-6 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors"
              >
                Start for free
              </Link>
              <a
                href="#how-it-works"
                className="inline-flex items-center h-btn px-6 border border-hairline text-ink font-body font-medium text-sm rounded-pill hover:bg-surface-dim transition-colors"
              >
                See how it works
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-canvas border-t border-hairline py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div data-aos="fade-up">
            <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-4">Process</p>
            <h2 className="font-display font-medium text-4xl md:text-5xl text-ink tracking-tighter mb-16">
              Four steps. Zero manual work.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-hairline border border-hairline">
            {STEPS.map((step, i) => (
              <div
                key={i}
                className="bg-canvas p-8"
                data-aos="fade"
                data-aos-delay={i * 80}
              >
                <div className="w-10 h-10 bg-ink flex items-center justify-center mb-6">
                  <step.icon size={18} className="text-canvas" />
                </div>
                <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-2">
                  Step {i + 1}
                </p>
                <h3 className="font-display font-semibold text-xl text-ink mb-3">{step.title}</h3>
                <p className="font-body text-sm text-ink-muted leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-surface py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div data-aos="fade-up">
            <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-4">Features</p>
            <h2 className="font-display font-medium text-4xl md:text-5xl text-ink tracking-tighter mb-16">
              Built for results.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-outline-variant border border-outline-variant">
            {FEATURES.map((feat, i) => (
              <div
                key={i}
                className="bg-canvas p-8"
                data-aos="fade"
                data-aos-delay={i * 60}
              >
                <feat.icon size={20} className="text-mint-teal mb-4" />
                <h3 className="font-display font-semibold text-base text-ink mb-2">{feat.title}</h3>
                <p className="font-body text-sm text-ink-muted leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-ink py-24">
        <div className="max-w-6xl mx-auto px-6 text-center" data-aos="fade-up">
          <h2 className="font-display font-light text-4xl md:text-6xl text-canvas tracking-tighter mb-6">
            Ready to apply smarter?
          </h2>
          <p className="font-body text-base font-light text-canvas/60 mb-10">
            Upload your CV once and let ApplyAI do the rest.
          </p>
          <Link
            to="/app"
            className="inline-flex items-center h-btn px-8 bg-mint-teal text-ink font-body font-medium text-sm rounded-pill hover:opacity-90 transition-opacity"
          >
            Get started now
          </Link>
        </div>
      </section>
    </>
  )
}
