import { api } from './client';
import type { FlashcardRequest, SaveFlashcardRequest, SavedFlashcardSet } from './types';

export const flashcardsApi = {
  generate: (data: FlashcardRequest) => api.post('/flashcards', data).then(r => r.data),
  save: (data: SaveFlashcardRequest) => api.post('/flashcards/save', data).then(r => r.data),
  listSaved: (course: string) => api.get<SavedFlashcardSet[]>('/flashcards/saved', { params: { course } }).then(r => r.data),
  remove: (id: string) => api.delete(`/flashcards/saved/${id}`).then(r => r.data),
};
