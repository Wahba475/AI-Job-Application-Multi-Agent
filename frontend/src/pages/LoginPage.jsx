import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/app'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) {
      toast.error('Please fill in all fields')
      return
    }

    setSubmitting(true)
    const loadingToast = toast.loading('Signing in…')

    try {
      const { data } = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/auth/login`,
        { email: email.trim(), password },
      )
      login(data.token, data.user)
      toast.success('Welcome back', { id: loadingToast })
      navigate(from, { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (err.response?.status === 429) {
        toast.error(detail || 'Too many requests. Please wait a moment.', { id: loadingToast })
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Invalid email or password', {
          id: loadingToast,
        })
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="hero-gradient min-h-[calc(100vh-44px)] flex items-center">
      <div className="max-w-md w-full mx-auto px-6 py-16">
        <div data-aos="fade-up">
          <p className="font-body text-xs tracking-caps uppercase text-ink-muted mb-4">
            Account
          </p>
          <h1 className="font-display font-light text-4xl md:text-5xl text-ink tracking-tighter mb-3">
            Sign in
          </h1>
          <p className="font-body text-sm font-light text-ink-muted mb-10 leading-relaxed">
            Continue to your ApplyAI workspace.
          </p>

          <form onSubmit={onSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block font-body text-xs tracking-caps uppercase text-ink-muted mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-btn px-4 bg-canvas border border-hairline font-body text-sm text-ink outline-none focus:border-mint-teal transition-colors"
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-body text-xs tracking-caps uppercase text-ink-muted mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-btn px-4 bg-canvas border border-hairline font-body text-sm text-ink outline-none focus:border-mint-teal transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full inline-flex items-center justify-center h-btn px-6 bg-ink text-canvas font-body font-medium text-sm rounded-pill hover:bg-on-surface transition-colors disabled:opacity-60"
            >
              {submitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-8 font-body text-sm text-ink-muted">
            No account?{' '}
            <Link to="/register" className="text-ink underline underline-offset-4 hover:text-secondary transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </section>
  )
}
