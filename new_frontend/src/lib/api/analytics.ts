import { api } from './client';
import type { Analytics, StudentStats } from './types';

export const analyticsApi = {
  getMyStats: (signal?: AbortSignal) => api.get<StudentStats>('/students/me/stats', { signal }).then(r => r.data),
  getMy: (courseCode: string, signal?: AbortSignal) => api.get<Analytics>('/analytics/me', { params: { course_code: courseCode }, signal }).then(r => r.data),
  get: (courseCode: string) => api.get<Analytics>('/analytics', { params: { course_code: courseCode } }).then(r => r.data),
  getUnanswered: (courseCode: string) => api.get('/analytics/unanswered', { params: { course_code: courseCode } }).then(r => r.data),
  getCoverage: (courseCode: string) => api.get('/analytics/coverage', { params: { course_code: courseCode } }).then(r => r.data),
  getQuestions: (courseCode: string) => api.get('/questions', { params: { course_code: courseCode } }).then(r => r.data),
};
