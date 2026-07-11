import { api } from './client';
import type { QuizRequest, SaveQuizRequest, SavedQuiz } from './types';

export const quizApi = {
  generate: (data: QuizRequest) => api.post('/quiz', data).then(r => r.data),
  save: (data: SaveQuizRequest) => api.post('/quiz/save', data).then(r => r.data),
  listSaved: (course: string) => api.get<SavedQuiz[]>('/quiz/saved', { params: { course } }).then(r => r.data),
  remove: (id: string) => api.delete(`/quiz/saved/${id}`).then(r => r.data),
};
