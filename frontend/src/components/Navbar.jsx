import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { pathname } = useLocation()
  const { isLoggedIn, user, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/')
  }

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
          {isLoggedIn && (
            <Link
              to="/history"
              className={`font-body text-sm transition-colors ${pathname === '/history' ? 'text-ink' : 'text-ink-muted hover:text-ink'}`}
            >
              History
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {isLoggedIn ? (
            <>
              <span className="hidden sm:inline font-body text-xs text-ink-muted truncate max-w-[140px]">
                {user?.email}
              </span>
              <Link
                to="/app"
                className="inline-flex items-center h-9 px-4 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors whitespace-nowrap"
              >
                Workspace
              </Link>
              <button
                type="button"
                onClick={onLogout}
                className="inline-flex items-center h-9 px-3 border border-hairline font-body text-sm text-ink-muted hover:text-ink transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="font-body text-sm text-ink-muted hover:text-ink transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center h-9 px-4 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors whitespace-nowrap"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
