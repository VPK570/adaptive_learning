import { api } from './client';
import type { PaperRequest, GeneratedPaper } from './types';

export const paperApi = {
  generate: (data: PaperRequest) => api.post<GeneratedPaper>('/generate-paper', data).then(r => r.data),
};
