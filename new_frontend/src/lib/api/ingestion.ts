import { api } from './client';
import type { AxiosProgressEvent } from 'axios';

export const ingestionApi = {
  ingestPdf: (file: File, courseCode: string, topic: string = '', onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_code', courseCode);
    formData.append('topic', topic);
    return api.post('/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress ? (e: AxiosProgressEvent) => {
        if (e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      } : undefined,
    }).then(r => r.data);
  },
  uploadCurriculum: (file: File, courseCode: string, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('course_code', courseCode);
    return api.post('/curriculum', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress ? (e: AxiosProgressEvent) => {
        if (e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      } : undefined,
    }).then(r => r.data);
  },
};
