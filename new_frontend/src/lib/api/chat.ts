import { api } from './client';
import { useAuthStore } from '@/lib/store/authStore';
import type { ChatMessage, QueryRequest, ChatFeedbackRequest } from './types';

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

  feedback: (data: ChatFeedbackRequest) =>
    api.post<{ status: string; bloom_level?: number }>('/chat/feedback', data).then(r => r.data),

  queryWebSocket: (
    params: {
      question: string; course_code: string; session_id: string;
      language?: string; mastery?: number; bloom_level?: number;
      top_k?: number; image_ids?: string[];
    },
    callbacks: {
      onThinking: (text: string) => void;
      onContent: (text: string) => void;
      onMetadata: (meta: Record<string, unknown>) => void;
      onDone: () => void;
      onError: (err: Error) => void;
    },
  ): { close: () => void; cancel: () => void; regenerate: () => void } => {
    const token = useAuthStore.getState().token;
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${window.location.host}/query/ws?token=${token}`;
    let ws = new WebSocket(url);
    let closed = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const send = (msg: object) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
      }
    };

    const cleanup = () => {
      closed = true;
      if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
      if (ws) { ws.onopen = null; ws.onmessage = null; ws.onerror = null; ws.onclose = null; ws.close(); ws = null; }
    };

    ws.onopen = () => {
      send({ type: 'query', data: params });
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'thinking') { callbacks.onThinking(msg.content); }
        else if (msg.type === 'content') { callbacks.onContent(msg.content); }
        else if (msg.type === 'metadata') { callbacks.onMetadata(msg); }
        else if (msg.type === 'done') { cleanup(); callbacks.onDone(); }
        else if (msg.type === 'error') { cleanup(); callbacks.onError(new Error(msg.content)); }
      } catch {}
    };

    ws.onerror = () => {
      if (!closed) { cleanup(); callbacks.onError(new Error('WebSocket connection error')); }
    };

    ws.onclose = () => {
      if (!closed) { cleanup(); callbacks.onError(new Error('WebSocket connection closed')); }
    };

    return {
      close: cleanup,
      cancel: () => send({ type: 'cancel' }),
      regenerate: () => send({ type: 'regenerate' }),
    };
  },
};
