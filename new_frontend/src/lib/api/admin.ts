import { api } from './client';

export interface AdminUser {
  id: number;
  email: string;
  role: string;
  name: string;
  status: string;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  total_courses: number;
  total_documents: number;
  total_conversations: number;
}

export const adminApi = {
  listUsers: () => api.get<AdminUser[]>('/admin/users').then(r => r.data),
  getStats: () => api.get<AdminStats>('/admin/stats').then(r => r.data),
};
