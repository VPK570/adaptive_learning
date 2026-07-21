import { api } from './client';
import { useAuthStore } from '@/lib/store/authStore';
import type { ChatMessage, QueryRequest } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

function parseUserMessage(msg: ChatMessage): { text: string; images: string[] } {
  if (msg.role !== 'user' || !msg.content) return { text: msg.text || msg.content || '', images: [] };
  try {
    const parsed = JSON.parse(msg.content);
    if (parsed && typeof parsed.text === 'string') return parsed;
  } catch {}
  return { text: msg.content, images: [] };
}

export const chatApi = {
  uploadImage: (file: File, sessionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    return api.post<{ image_id: string }>('/chat-images', formData).then(r => r.data.image_id);
  },

  getHistory: (courseCode: string, sessionId: string) =>
    api.get<ChatMessage[]>('/chat-history', { params: { course_code: courseCode, session_id: sessionId } }).then(r => r.data),
  saveMessage: (courseCode: string, sessionId: string, role: string, content: string) =>
    api.post('/chat-history', null, { params: { course_code: courseCode, session_id: sessionId, role, content } }).then(r => r.data),
  clearHistory: (courseCode: string, sessionId: string) =>
    api.delete('/chat-history', { params: { course_code: courseCode, session_id: sessionId } }).then(r => r.data),

  queryStream: (
    body: QueryRequest,
    onContent: (text: string) => void,
    onThinking: (text: string) => void,
    onMetadata: (meta: Record<string, unknown>) => void,
    onError: (err: Error) => void,
  ): Promise<void> => {
    const token = useAuthStore.getState().token;
    return fetch(`${API_BASE}/query-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    }).then(async (response) => {
      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(`Server error ${response.status}: ${text}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          const trimmed = line.replace(/\r$/, '');
          if (trimmed.startsWith('data: ')) {
            try {
              const data = JSON.parse(trimmed.slice(6));
              if (data.type === 'thinking') {
                onThinking(data.content);
              } else if (data.type === 'content') {
                onContent(data.content);
              } else if (data.type === 'metadata') {
                onMetadata(data);
              }
            } catch { /* skip malformed chunks */ }
          }
        }
      }
    }).catch(onError);
  },
};
