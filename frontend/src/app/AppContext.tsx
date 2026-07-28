import React, { createContext, useContext, useEffect, useState } from 'react';
import type { Page, Prescription, SessionResponse, User } from './types';
import { apiFetch, postJson } from './api';

interface AppContextType {
  currentUser: User | null;
  currentPage: Page;
  setCurrentPage: (page: Page) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  selectedPrescription: Prescription | null;
  setSelectedPrescription: (p: Prescription | null) => void;
  unreadCount: number;
  setUnreadCount: (n: number) => void;
  refreshSession: () => Promise<void>;
  loadingSession: boolean;
  pendingVerificationEmail: string;
  setPendingVerificationEmail: (email: string) => void;
}

const AppContext = createContext<AppContextType | null>(null);

function defaultPageForRole(role: User['role']): Page {
  if (role === 'patient') return 'patient-dashboard';
  if (role === 'doctor') return 'doctor-dashboard';
  if (role === 'nurse') return 'nurse-dashboard';
  return 'admin-dashboard';
}

function readPendingVerificationEmail() {
  try {
    return window.localStorage.getItem('mediqueue.pendingVerificationEmail') || '';
  } catch {
    return '';
  }
}

function storePendingVerificationEmail(email: string) {
  try {
    if (email) {
      window.localStorage.setItem('mediqueue.pendingVerificationEmail', email);
    } else {
      window.localStorage.removeItem('mediqueue.pendingVerificationEmail');
    }
  } catch {
    // Local storage is optional; keep the in-memory state working.
  }
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [selectedPrescription, setSelectedPrescription] = useState<Prescription | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingSession, setLoadingSession] = useState(true);
  const [pendingVerificationEmailState, setPendingVerificationEmailState] = useState(readPendingVerificationEmail);

  const setPendingVerificationEmail = (email: string) => {
    const normalised = email.trim().toLowerCase();
    setPendingVerificationEmailState(normalised);
    storePendingVerificationEmail(normalised);
  };

  const refreshSession = async () => {
    const data = await apiFetch<SessionResponse>('/api/session');
    setCurrentUser(data.user);
    setUnreadCount(data.unreadCount || 0);
    if (data.user) setCurrentPage(defaultPageForRole(data.user.role));
  };

  useEffect(() => {
    refreshSession().catch(() => undefined).finally(() => setLoadingSession(false));
  }, []);

  const login = async (email: string, password: string) => {
    const data = await postJson<{ ok: boolean; user: User; unreadCount: number }>('/api/login', { email, password });
    setCurrentUser(data.user);
    setUnreadCount(data.unreadCount || 0);
    setPendingVerificationEmail('');
    setCurrentPage(defaultPageForRole(data.user.role));
  };

  const logout = async () => {
    await postJson('/api/logout', {});
    setCurrentUser(null);
    setSelectedPrescription(null);
    setUnreadCount(0);
    setCurrentPage('landing');
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        currentPage,
        setCurrentPage,
        login,
        logout,
        selectedPrescription,
        setSelectedPrescription,
        unreadCount,
        setUnreadCount,
        refreshSession,
        loadingSession,
        pendingVerificationEmail: pendingVerificationEmailState,
        setPendingVerificationEmail,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
