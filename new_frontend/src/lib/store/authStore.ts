import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '@/lib/api/auth';

interface User {
  email: string;
  role: string;
  name: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const res = await authApi.login(email, password);
        const token = res.access_token;
        const role = res.role;
        set({
          token,
          user: { email, role, name: email.split('@')[0] },
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          localStorage.removeItem('role');
          window.location.href = '/';
        }
      },

      hydrate: () => {
        const { token } = get();
        if (token && !get().isAuthenticated) {
          set({ isAuthenticated: true });
        }
      },
    }),
    {
      name: 'uniauth',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);
