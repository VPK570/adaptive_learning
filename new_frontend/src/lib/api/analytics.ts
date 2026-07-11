import { api } from './client';
import type { Analytics } from './types';

export const analyticsApi = {
  get: (courseCode: string) => api.get<Analytics>('/analytics', { params: { course_code: courseCode } }).then(r => r.data),
  getUnanswered: (courseCode: string) => api.get('/analytics/unanswered', { params: { course_code: courseCode } }).then(r => r.data),
  getCoverage: (courseCode: string) => api.get('/analytics/coverage', { params: { course_code: courseCode } }).then(r => r.data),
  getQuestions: (courseCode: string) => api.get('/questions', { params: { course_code: courseCode } }).then(r => r.data),
};
