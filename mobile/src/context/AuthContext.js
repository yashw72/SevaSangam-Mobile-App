import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  getToken,
  setToken,
  clearToken,
  getSession,
  setSession,
  clearSession,
} from '../services/native/secureStorage';

// Shorter session expiry for Admin (15 mins), standard for others (7 days)
const ADMIN_TOKEN_EXPIRY_MS = 15 * 60 * 1000; // 15 minutes
const STANDARD_TOKEN_EXPIRY_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export const AuthContext = createContext({
  user: null,
  role: null, // 'customer' | 'worker' | 'admin' | null
  token: null,
  status: null, // 'verified' | 'pending' | 'rejected' | 'suspended' | null
  isLoading: true,
  login: async () => {},
  logout: async () => {},
  restoreSession: async () => {},
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [token, setTokenState] = useState(null);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Restores user session from secure storage
   */
  const restoreSession = useCallback(async () => {
    try {
      setIsLoading(true);
      const storedToken = await getToken();
      const storedSession = await getSession();

      if (storedToken && storedSession) {
        // Validate token expiration
        const now = Date.now();
        if (storedSession.expiresAt && now > storedSession.expiresAt) {
          console.warn('[AuthContext] Session expired, clearing credentials');
          await clearToken();
          await clearSession();
          setUser(null);
          setRole(null);
          setTokenState(null);
          setStatus(null);
        } else {
          setUser(storedSession.user || null);
          setRole(storedSession.role || null);
          setStatus(storedSession.status || null);
          setTokenState(storedToken);
        }
      } else {
        setUser(null);
        setRole(null);
        setTokenState(null);
        setStatus(null);
      }
    } catch (error) {
      console.warn('[AuthContext] Error restoring session:', error);
      setUser(null);
      setRole(null);
      setTokenState(null);
      setStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restore session when component mounts
  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  /**
   * Logs in a user, assigns mock token & sets role-based expiry in secure storage
   * @param {object} authPayload - { user, role, status, token }
   */
  const login = useCallback(async (authPayload) => {
    try {
      const targetRole = authPayload?.role || 'customer';
      const targetStatus = authPayload?.status || (targetRole === 'worker' ? 'verified' : 'active');
      const generatedToken = authPayload?.token || `sevasangam_mock_jwt_${targetRole}_${Date.now()}`;
      
      const expiryDuration = targetRole === 'admin' ? ADMIN_TOKEN_EXPIRY_MS : STANDARD_TOKEN_EXPIRY_MS;
      const expiresAt = Date.now() + expiryDuration;

      const userData = authPayload?.user || {
        id: `usr_${targetRole}_${Date.now().toString().slice(-4)}`,
        name: authPayload?.name || (targetRole === 'admin' ? 'Cooperative Admin' : targetRole === 'worker' ? 'Ramesh Kumar' : 'Pooja Sharma'),
        phone: authPayload?.phone || '+91 9876543210',
        role: targetRole,
      };

      const sessionData = {
        user: userData,
        role: targetRole,
        status: targetStatus,
        expiresAt,
      };

      // Persist in secure storage
      await setToken(generatedToken);
      await setSession(sessionData);

      // Update context state
      setUser(userData);
      setRole(targetRole);
      setStatus(targetStatus);
      setTokenState(generatedToken);

      return true;
    } catch (error) {
      console.error('[AuthContext] Login error:', error);
      return false;
    }
  }, []);

  /**
   * Logs out user and clears all secure storage and in-memory state
   */
  const logout = useCallback(async () => {
    try {
      await clearToken();
      await clearSession();
    } catch (error) {
      console.warn('[AuthContext] Error during logout cleanup:', error);
    } finally {
      setUser(null);
      setRole(null);
      setTokenState(null);
      setStatus(null);
    }
  }, []);

  const value = {
    user,
    role,
    token,
    status,
    isLoading,
    login,
    logout,
    restoreSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
