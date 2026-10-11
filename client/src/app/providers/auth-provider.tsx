import React, { useEffect, useState } from 'react';
import { UserProfile, MerchantInfo } from '@/types/api';
import { authService } from '@/services/auth';
import { AuthContext } from './auth-context';

const TOKEN_KEY = 'reconpilot_auth_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState<UserProfile | null>(null);
  const [merchant, setMerchant] = useState<MerchantInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await authService.getCurrentUser();
        setUser(data.user);
        setMerchant(data.merchant);
      } catch {
        // If session validation fails (token expired, user deleted), clean up
        try {
          sessionStorage.removeItem(TOKEN_KEY);
        } catch {
          // ignore
        }
        setToken(null);
        setUser(null);
        setMerchant(null);
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await authService.login({ email, password });
      try {
        sessionStorage.setItem(TOKEN_KEY, resp.access_token);
      } catch {
        // ignore
      }
      setToken(resp.access_token);
      setUser(resp.user);
      setMerchant(resp.merchant);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      if (token) {
        await authService.logout().catch(() => {});
      }
    } finally {
      try {
        sessionStorage.removeItem(TOKEN_KEY);
      } catch {
        // ignore
      }
      setToken(null);
      setUser(null);
      setMerchant(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token && !!user,
        isLoading,
        user,
        merchant,
        token,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
