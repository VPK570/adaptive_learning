import { api } from './client';
import type { Course, CourseCreate, CourseUpdate, CourseStats, StudentCourseMap } from './types';

export const coursesApi = {
  list: (signal?: AbortSignal) => api.get<Course[]>('/courses', { signal }).then(r => r.data),
  get: (code: string) => api.get<Course>(`/courses/${code}`).then(r => r.data),
  create: (data: CourseCreate) => api.post<Course>('/courses', data).then(r => r.data),
  update: (code: string, data: CourseUpdate) => api.put<Course>(`/courses/${code}`, data).then(r => r.data),
  remove: (code: string) => api.delete(`/courses/${code}`).then(r => r.data),
  getStats: (courseCode: string) => api.get<CourseStats>('/stats', { params: { course_code: courseCode } }).then(r => r.data),
  getTopics: (course: string) => api.get('/curriculum/topics', { params: { course } }).then(r => r.data),
  getStructuredTopics: (code: string) => api.get<any[]>(`/courses/${code}/topics`).then(r => r.data),
  getStudentMap: (code: string) => api.get<StudentCourseMap>(`/courses/${code}/student-map`).then(r => r.data),
};
