import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-canvas border-t border-hairline" style={{ padding: '52px 20px 48px' }}>
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <p className="font-display font-semibold text-base text-ink mb-1">ApplyAI</p>
          <p className="font-body text-sm text-ink-muted">AI-powered job application automation.</p>
        </div>

        <div className="flex gap-8 text-sm font-body text-ink-muted">
          <Link to="/" className="hover:text-ink transition-colors">Home</Link>
          <Link to="/app" className="hover:text-ink transition-colors">Try it</Link>
          <Link to="/history" className="hover:text-ink transition-colors">History</Link>
        </div>

        <p className="font-body text-sm text-ink-muted">
          © {new Date().getFullYear()} ApplyAI
        </p>
      </div>
    </footer>
  )
}
