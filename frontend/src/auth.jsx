import React, { createContext, useContext, useEffect, useState } from 'react'
import Keycloak from 'keycloak-js'

const AuthContext = createContext(null)

const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'lsap',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'lsap-frontend',
}

const keycloak = new Keycloak(keycloakConfig)

export function AuthProvider({ children }) {
  const [authenticated, setAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(null)

  useEffect(() => {
    keycloak
      .init({
        onLoad: 'check-sso',
        pkceMethod: 'S256',
        checkLoginIframe: false,
      })
      .then((auth) => {
        setAuthenticated(auth)
        if (auth) {
          setUser({
            username: keycloak.tokenParsed?.preferred_username,
            email: keycloak.tokenParsed?.email,
            roles: keycloak.tokenParsed?.realm_access?.roles || [],
          })
          setToken(keycloak.token)
        }
        setLoading(false)
      })
      .catch((err) => {
        console.warn('Keycloak init failed – falling back to anonymous mode', err)
        setAuthenticated(false)
        setUser({ username: 'dev-user', roles: ['analyst'] })
        setLoading(false)
      })

    // Token refresh
    keycloak.onTokenExpired = () => {
      keycloak.updateToken(30).then((refreshed) => {
        if (refreshed) setToken(keycloak.token)
      })
    }
  }, [])

  const login = () => keycloak.login()
  const logout = () => keycloak.logout({ redirectUri: window.location.origin })

  const getToken = () => keycloak.token || token

  return (
    <AuthContext.Provider value={{ authenticated, user, loading, login, logout, getToken, keycloak }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
