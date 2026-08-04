import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { pathname } = useLocation()
  const { isLoggedIn, user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const closeMenu = () => setOpen(false)

  const onLogout = () => {
    closeMenu()
    logout()
    navigate('/')
  }

  const desktopLink = (active) =>
    `font-body text-sm transition-colors ${active ? 'text-ink' : 'text-ink-muted hover:text-ink'}`
  const mobileLink =
    'py-3 font-body text-sm text-ink-muted hover:text-ink transition-colors border-b border-hairline'

  return (
    <header className="sticky top-0 z-50 bg-canvas border-b border-hairline">
      <nav className="max-w-6xl mx-auto px-6 h-nav flex items-center justify-between">
        <Link
          to="/"
          onClick={closeMenu}
          className="font-display font-semibold text-base tracking-tight text-ink"
        >
          ApplyAI
        </Link>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-8">
          <a href="/#how-it-works" className={desktopLink(false)}>How it works</a>
          <a href="/#features" className={desktopLink(false)}>Features</a>
          {isLoggedIn && (
            <Link to="/history" className={desktopLink(pathname === '/history')}>History</Link>
          )}
        </div>

        {/* Desktop auth actions */}
        <div className="hidden md:flex items-center gap-3 flex-shrink-0">
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
              <Link to="/login" className="font-body text-sm text-ink-muted hover:text-ink transition-colors">
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

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          className="md:hidden inline-flex items-center justify-center w-9 h-9 -mr-2 text-ink"
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {/* Mobile menu panel */}
      {open && (
        <div className="md:hidden bg-canvas border-t border-hairline px-6 pb-4 flex flex-col">
          <a href="/#how-it-works" onClick={closeMenu} className={mobileLink}>How it works</a>
          <a href="/#features" onClick={closeMenu} className={mobileLink}>Features</a>

          {isLoggedIn ? (
            <>
              <Link to="/history" onClick={closeMenu} className={mobileLink}>History</Link>
              {user?.email && (
                <span className="pt-3 pb-1 font-body text-xs text-ink-muted truncate">{user.email}</span>
              )}
              <Link
                to="/app"
                onClick={closeMenu}
                className="mt-2 inline-flex items-center justify-center h-11 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors"
              >
                Workspace
              </Link>
              <button
                type="button"
                onClick={onLogout}
                className="mt-2 inline-flex items-center justify-center h-11 border border-hairline font-body text-sm text-ink-muted hover:text-ink rounded-pill transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={closeMenu} className={mobileLink}>Sign in</Link>
              <Link
                to="/register"
                onClick={closeMenu}
                className="mt-3 inline-flex items-center justify-center h-11 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}
