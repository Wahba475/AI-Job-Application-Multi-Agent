import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <header className="sticky top-0 z-50 bg-canvas border-b border-hairline">
      <nav className="max-w-6xl mx-auto px-6 h-nav flex items-center justify-between">
        <Link to="/" className="font-display font-semibold text-base tracking-tight text-ink">
          ApplyAI
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <a href="/#how-it-works" className="font-body text-sm text-ink-muted hover:text-ink transition-colors">
            How it works
          </a>
          <a href="/#features" className="font-body text-sm text-ink-muted hover:text-ink transition-colors">
            Features
          </a>
          <Link
            to="/history"
            className={`font-body text-sm transition-colors ${pathname === '/history' ? 'text-ink' : 'text-ink-muted hover:text-ink'}`}
          >
            History
          </Link>
        </div>

        <Link
          to="/app"
          className="inline-flex items-center h-9 px-4 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors flex-shrink-0 whitespace-nowrap"
        >
          Try Now
        </Link>
      </nav>
    </header>
  )
}
