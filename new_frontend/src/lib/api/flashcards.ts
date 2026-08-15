import { api } from './client';
import type { Flashcard, FlashcardRequest, RecordFlashcardRequest, RecordFlashcardResponse, SaveFlashcardRequest, SavedFlashcardSet } from './types';

export const flashcardsApi = {
  generate: (data: FlashcardRequest) => api.post<Flashcard[]>('/flashcards', data).then(r => r.data),
  save: (data: SaveFlashcardRequest) => api.post<{ id: string; status: string }>('/flashcards/save', data).then(r => r.data),
  listSaved: (course: string) => api.get<SavedFlashcardSet[]>('/flashcards/saved', { params: { course } }).then(r => r.data),
  deleteSaved: (id: string) => api.delete<{ status: string }>(`/flashcards/saved/${id}`).then(r => r.data),
  record: (id: string, data: RecordFlashcardRequest) => api.post<RecordFlashcardResponse>(`/flashcards/saved/${id}/record`, data).then(r => r.data),
};
