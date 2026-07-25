"use client";

import React, { useState, useRef, useEffect, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Send, BookOpen, Sparkles, Copy, ThumbsUp, Zap, ChevronDown, ImageIcon, X } from 'lucide-react';
import dynamic from 'next/dynamic';
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

const BLOOM_LABELS = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'] as const;
import AppShell from '@/app/components/AppShell';
import Badge from '@/app/components/Badge';
import ProgressBar from '@/app/components/ProgressBar';
import { coursesApi } from '@/lib/api/courses';
import { chatApi } from '@/lib/api/chat';
import type { Course, ChatMessage } from '@/lib/api/types';
import { useToast } from '@/app/components/ToastContext';
import styles from './CourseDetail.module.css';

function cite(text: string) {
  return text.replace(
    /\[(Source|Curriculum):([^\]]*)\]/g,
    (_, type, rest) => `<cite class="citation-inline">${type}:${rest}</cite>`
  );
}

const ChatMessage = React.memo(({ msg, feedbackLoading, onFeedback }: {
  msg: ChatMessage;
  feedbackLoading: Record<number, boolean>;
  onFeedback: (msgId: number, helpful: boolean) => void;
}) => {
  return (
    <div className={`${styles.messageBubble} ${styles[msg.role]}`}>
      <div className={styles.assistantContent}>
        {msg.images && msg.images.length > 0 && (
          <div className={styles.msgImages}>
            {msg.images.map(imgId => (
              <img key={imgId} src={`/chat-images/${imgId}`} alt="Uploaded" className={styles.msgImage} />
            ))}
          </div>
        )}
        {msg.role === 'assistant' && msg.thinkingText && (
          <details className={styles.thinkingBlock}>
            <summary className={styles.thinkingSummary}>
              <ChevronDown size={14} className={styles.thinkingChevron} />
              Show reasoning
            </summary>
            <div className={styles.thinkingContent}>{msg.thinkingText}</div>
          </details>
        )}
        <ReactMarkdown className={styles.msgText} remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
          {cite(msg.text)}
        </ReactMarkdown>
        {msg.sources && msg.sources.length > 0 && (
          <div className={styles.sourcesBlock}>
            <span className={styles.sourcesLabel}>Sources:</span>
            {msg.sources.map((s, i) => (
              <span key={i} className={styles.sourceChip}>
                <FileText size={12} /> {s.file || s.source_title}, p.{s.page}
              </span>
            ))}
          </div>
        )}
        {msg.verified === false && (
          <div className={styles.unverifiedBanner}>
            ⚠️ This answer may not be based on your course materials. {msg.verificationReason}
          </div>
        )}
        {msg.role === 'assistant' && msg.text && (
          <div className={styles.msgActions}>
            <button className={styles.msgActionBtn}><Copy size={14} /> Copy</button>
            <button className={styles.msgActionBtn} onClick={() => onFeedback(msg.id, true)} disabled={feedbackLoading[msg.id]}>
              <ThumbsUp size={14} /> {feedbackLoading[msg.id] ? '...' : 'Helpful'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
});

export default function CourseDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { showToast } = useToast();
  const router = useRouter();
  const { code } = use(params);
  const [course, setCourse] = useState<Course | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [bloomLevel, setBloomLevel] = useState<number | null>(null);
  const [bloomOpen, setBloomOpen] = useState(false);
  const [imageIds, setImageIds] = useState<string[]>([]);
  const [imagePreviews, setImagePreviews] = useState<{ id: string; url: string; name: string }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState<Record<number, boolean>>({});
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sessionId = `course_${code}`;

  useEffect(() => {
    if (!code) return;
    const controller = new AbortController();
    Promise.all([
      coursesApi.get(code),
      chatApi.getHistory(code, sessionId).catch(() => [] as ChatMessage[]),
    ])
      .then(([courseData, history]) => {
        if (controller.signal.aborted) return;
        setCourse(courseData);
        const msgs = (Array.isArray(history) ? history : []).map((h, i) => ({
          id: i + 1,
          role: h.role,
          text: h.role === 'user' ? (() => { try { const p = JSON.parse(h.content || ''); return p.text || ''; } catch {} return h.content || ''; })() : (h.content || h.text || ''),
          images: h.role === 'user' ? (() => { try { const p = JSON.parse(h.content || ''); return p.images || []; } catch {} return []; })() : undefined,
        }));
        setMessages(msgs);
      })
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [code]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleImageSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const imageId = await chatApi.uploadImage(file, sessionId);
      setImageIds(prev => [...prev, imageId]);
      setImagePreviews(prev => [...prev, { id: imageId, url: URL.createObjectURL(file), name: file.name }]);
    } catch (err) {
      console.error('Upload failed', err);
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [sessionId]);

  const removeImage = useCallback((id: string) => {
    setImageIds(prev => prev.filter(i => i !== id));
    setImagePreviews(prev => { const p = prev.filter(x => x.id !== id); return p; });
  }, []);

  const handleSend = useCallback(() => {
    if ((!inputValue.trim() && imageIds.length === 0) || streaming || !course) return;
    const userText = inputValue;
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', text: userText, images: [...imageIds] };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setImageIds([]);
    setImagePreviews([]);
    setStreaming(true);

    const assistantId = crypto.randomUUID();
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', text: '', thinkingText: '' }]);

    let fullText = '';

    chatApi.queryStream(
      { question: userText, course_code: code, session_id: sessionId, bloom_level: bloomLevel, image_ids: imageIds.length > 0 ? imageIds : undefined },
      (content) => {
        console.log('[PAGE] onContent chunk len=' + content.length + ' total=' + (fullText.length + content.length));
        fullText += content;
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, text: (m.text || '') + content } : m
        ));
      },
      (content) => {
        console.log('[PAGE] onThinking chunk len=' + content.length);
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, thinkingText: (m.thinkingText || '') + content } : m
        ));
      },
      (meta) => {
        console.log('[PAGE] onMetadata', JSON.stringify(meta));
        setMessages(prev => prev.map(m =>
          m.id === assistantId
            ? {
                ...m,
                sources: (meta.cited_sources || meta.sources || []).map(s => ({ file: s.source_title || s.file, page: s.page })),
                verified: meta.verified,
                verificationReason: meta.verification_reason,
              }
            : m
        ));
        setStreaming(false);
        chatApi.saveMessage(code, sessionId, 'assistant', fullText).catch(() => {});
      },
      () => { console.log('[PAGE] onError/onDone'); setStreaming(false); }
    );

    chatApi.saveMessage(code, sessionId, 'user', userText).catch(() => {});
  }, [inputValue, streaming, course, code, sessionId, imageIds, bloomLevel]);

  const handleFeedback = useCallback(async (msgId: number, helpful: boolean) => {
    const lastUser = [...messages].reverse().find(m => m.role === 'user');
    if (!lastUser || !course || feedbackLoading[msgId]) return;
    setFeedbackLoading(prev => ({ ...prev, [msgId]: true }));
    try {
      await chatApi.feedback({ question: lastUser.text || '', course_code: code, helpful });
      showToast('Feedback recorded', 'success');
    } catch { /* silently fail */ }
    setFeedbackLoading(prev => ({ ...prev, [msgId]: false }));
  }, [messages, course, code, feedbackLoading]);

  const breadcrumbs = [
    { label: 'Dashboard', href: '/student/dashboard' },
    { label: course?.course_name || code }
  ];

  const materials = course ? [
    { id: 1, name: course.course_name, meta: `${course.doc_count || 0} documents`, active: true },
  ] : [];

  return (
    <AppShell
      navRole="student"
      activeNavKey="courses"
      topBarVariant="breadcrumbBack"
      breadcrumbs={breadcrumbs}
      onBack={() => router.back()}
    >
      <div className={styles.layout}>
        <aside className={styles.materialsPanel}>
          <div className={styles.courseHeader}>
            <h2 className={styles.courseTitle}>{course?.course_name || code}</h2>
            <p className={styles.courseMeta}>{course?.description || ''}</p>
          </div>

          <div className={styles.masteryBlock}>
            <div className={styles.masteryRow}>
              <span className={styles.masteryLabel}>Course Mastery</span>
              <span className={styles.masteryValue}>—</span>
            </div>
            <ProgressBar percent={0} showGradient />
            <p className={styles.nextItem}>
              <Zap size={14} className={styles.zapIcon} />
              Next: Ask the AI assistant a question
            </p>
          </div>

          <div className={styles.materialsList}>
            <h3 className={styles.materialsTitle}>
              <BookOpen size={16} />
              <span>Course Materials</span>
            </h3>
            {materials.map(mat => (
              <button
                key={mat.id}
                className={`${styles.materialItem}`}
              >
                <FileText size={18} className={styles.matIcon} />
                <div className={styles.matContent}>
                  <span className={styles.matName}>{mat.name}</span>
                  <span className={styles.matMeta}>{mat.meta}</span>
                </div>
                {mat.active && <Badge variant="solid" color="primary">Active</Badge>}
              </button>
            ))}
          </div>
        </aside>

        <section className={styles.chatPanel}>
          <div className={styles.chatHeader}>
            <Sparkles size={20} className={styles.sparkleIcon} />
            <h2 className={styles.chatTitle}>AI Study Assistant</h2>
          </div>

          <div className={styles.chatBody}>
            {loading ? (
              <div style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ height: 48, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite', width: '60%' }} />
                <div style={{ height: 48, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite', width: '40%' }} />
                <div style={{ height: 48, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite', width: '50%' }} />
              </div>
            ) : messages.length === 0 ? (
              <p className={styles.msgText}>Ask a question about your course materials.</p>
            ) : (
              messages.map(msg => (
                <ChatMessage key={msg.id} msg={msg} feedbackLoading={feedbackLoading} onFeedback={handleFeedback} />
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <div className={styles.chatInputArea}>
            <div className={styles.bloomSelector}>
              <button className={styles.bloomToggle} onClick={() => setBloomOpen(!bloomOpen)}>
                {bloomLevel ? `L${bloomLevel}: ${BLOOM_LABELS[bloomLevel - 1]}` : 'Auto'}
                <ChevronDown size={14} />
              </button>
              {bloomOpen && (
                <div className={styles.bloomDropdown}>
                  <button className={styles.bloomOption} onClick={() => { setBloomLevel(null); setBloomOpen(false); }}>Auto (detect)</button>
                  {[1,2,3,4,5,6].map(l => (
                    <button key={l} className={styles.bloomOption} onClick={() => { setBloomLevel(l); setBloomOpen(false); }}>
                      L{l}: {BLOOM_LABELS[l - 1]}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {imagePreviews.length > 0 && (
              <div className={styles.previewRow}>
                {imagePreviews.map(p => (
                  <div key={p.id} className={styles.previewChip}>
                    <img src={p.url} alt={p.name} className={styles.previewThumb} />
                    <button className={styles.previewRemove} onClick={() => removeImage(p.id)}><X size={14} /></button>
                  </div>
                ))}
              </div>
            )}
            <div className={styles.inputWrapper}>
              <textarea
                className={styles.chatInput}
                placeholder="Ask about your course materials..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                rows={1}
              />
              <input ref={fileInputRef} type="file" accept="image/jpeg,image/png" hidden onChange={handleImageSelect} />
              <button className={styles.imageBtn} onClick={() => fileInputRef.current?.click()} disabled={streaming || uploading || imageIds.length >= 5}>
                <ImageIcon size={18} />
              </button>
              <button
                className={`${styles.sendBtn} ${(inputValue.trim() || imageIds.length > 0) && !streaming ? styles.sendActive : ''}`}
                onClick={handleSend}
                disabled={(!inputValue.trim() && imageIds.length === 0) || streaming}
              >
                <Send size={18} />
              </button>
            </div>
            <p className={styles.disclaimer}>AI responses are generated from your uploaded course materials.</p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
