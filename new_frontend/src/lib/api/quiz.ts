import { api } from './client';
import type { QuizQuestion, QuizRequest, SaveQuizRequest, SavedQuiz } from './types';

export const quizApi = {
  generate: (data: QuizRequest) => api.post<QuizQuestion[]>('/quiz', data).then(r => r.data),
  save: (data: SaveQuizRequest) => api.post<{ id: string; status: string }>('/quiz/save', data).then(r => r.data),
  listSaved: (course: string) => api.get<SavedQuiz[]>('/quiz/saved', { params: { course } }).then(r => r.data),
  deleteSaved: (id: string) => api.delete<{ status: string }>(`/quiz/saved/${id}`).then(r => r.data),
};
