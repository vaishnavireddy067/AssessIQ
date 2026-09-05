import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiRequest } from '../api/client';

export interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  phone?: string;
  avatar_url?: string;
  is_active: boolean;
  company_id?: string;
  roles: string[];
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  registerCompany: (data: any) => Promise<void>;
  registerCandidate: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  reloadUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    try {
      const profile = await apiRequest<UserProfile>('/users/me');
      setUser(profile);
    } catch (err) {
      setUser(null);
      localStorage.removeItem('assessiq_access_token');
      localStorage.removeItem('assessiq_refresh_token');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('assessiq_access_token');
    if (token) {
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', pass);

      const tokens = await apiRequest<{ access_token: string; refresh_token: string }>('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      localStorage.setItem('assessiq_access_token', tokens.access_token);
      localStorage.setItem('assessiq_refresh_token', tokens.refresh_token);

      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const registerCompany = async (data: any) => {
    setIsLoading(true);
    try {
      const tokens = await apiRequest<{ access_token: string; refresh_token: string }>(
        '/auth/register-company',
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      );

      localStorage.setItem('assessiq_access_token', tokens.access_token);
      localStorage.setItem('assessiq_refresh_token', tokens.refresh_token);

      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const registerCandidate = async (data: any) => {
    setIsLoading(true);
    try {
      const tokens = await apiRequest<{ access_token: string; refresh_token: string }>(
        '/auth/register-candidate',
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      );

      localStorage.setItem('assessiq_access_token', tokens.access_token);
      localStorage.setItem('assessiq_refresh_token', tokens.refresh_token);

      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('assessiq_refresh_token');
      await apiRequest('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (_) {
    } finally {
      localStorage.removeItem('assessiq_access_token');
      localStorage.removeItem('assessiq_refresh_token');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        registerCompany,
        registerCandidate,
        logout,
        reloadUser: fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
