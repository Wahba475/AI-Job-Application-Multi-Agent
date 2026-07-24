import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'))
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || 'null')
    } catch {
      return null
    }
  })

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('token'))
  }, [])

  const login = (token, userData) => {
    localStorage.setItem('token', token)
    if (userData) localStorage.setItem('user', JSON.stringify(userData))
    setIsLoggedIn(true)
    setUser(userData || null)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setIsLoggedIn(false)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        isAuthenticated: isLoggedIn,
        user,
        login,
        logout,
        setIsLoggedIn,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
