import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as authApi from '../api/authApi'
import { refreshOnce, setAccessToken, setOnAuthExpired } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const clearAuth = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setOnAuthExpired(clearAuth)
  }, [clearAuth])

  useEffect(() => {
    let mounted = true
    refreshOnce()
      .then(({ data }) => {
        if (!mounted) return
        setAccessToken(data.access_token)
        setUser(data.user)
      })
      .catch(() => {
        if (!mounted) return
        clearAuth()
      })
      .finally(() => {
        if (mounted) setIsLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [clearAuth])

  const loginWithCredentials = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password })
    setAccessToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      clearAuth()
    }
  }, [clearAuth])

  return (
    <AuthContext.Provider value={{ user, isLoading, loginWithCredentials, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải được dùng bên trong AuthProvider')
  return ctx
}
