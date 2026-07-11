import { api } from './client';
import type { LoginResponse, RegisterResponse } from './types';

export const authApi = {
  login: (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    return api.post<LoginResponse>('/auth/login', body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(r => r.data);
  },
  register: (email: string, password: string, role: string = 'student') =>
    api.post<RegisterResponse>('/auth/register', { email, password, role }).then(r => r.data),
};
