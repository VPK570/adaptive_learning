"use client";

import React, { useState, useRef, useEffect, useCallback, use } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Send, BookOpen, Sparkles, Copy, ThumbsUp, Zap, ChevronDown, ImageIcon, X, Square, RefreshCw, ExternalLink } from 'lucide-react';
import dynamic from 'next/dynamic';
const ReactMarkdown = dynamic(() => import('react-markdown'), { ssr: false });
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

const BLOOM_LABELS = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'] as const;
import AppShell from '@/app/components/AppShell';
import ProgressBar from '@/app/components/ProgressBar';
import { coursesApi } from '@/lib/api/courses';
import { chatApi } from '@/lib/api/chat';
import type { Course, ChatMessage, StudentCourseMap } from '@/lib/api/types';
import { useQuery } from '@tanstack/react-query';
import { useToast } from '@/app/components/ToastContext';
import styles from './CourseDetail.module.css';

function cite(text: string) {
  const withCites = text.replace(
    /\[(Source|Curriculum):([^\]]*)\]/g,
    (_, type, rest) => `<cite class="citation-inline">${type}:${rest}</cite>`
  );
  return withCites.replace(/<(\/?)(?!cite\b)[a-zA-Z][^>]*>/g, '');
}

const CHIP_SUGGESTIONS = ['Explain further', 'Give a concrete example', 'Quiz me on this'];

const ChatMessage = React.memo(function ChatMessage({ msg, feedbackLoading, onFeedback, isStreaming, onRegenerate, onChip }: {
  msg: ChatMessage;
  feedbackLoading: Record<number, boolean>;
  onFeedback: (msgId: number, helpful: boolean) => void;
  isStreaming?: boolean;
  onRegenerate?: () => void;
  onChip?: (text: string) => void;
}) {
  return (
    <div className={`${styles.messageBubble} ${styles[msg.role]} ${isStreaming ? styles.streaming : ''}`}>
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
        {isStreaming && !msg.text ? (
          <div className={styles.typingIndicator}>
            <span /><span /><span />
          </div>
        ) : (
          <ReactMarkdown className={styles.msgText} remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
            {cite(msg.text)}
          </ReactMarkdown>
        )}
        {msg.sources && msg.sources.length > 0 && (
          <div className={styles.sourcesBlock}>
            <span className={styles.sourcesLabel}>Sources:</span>
            {msg.sources.map((s, i) => (
              s.file_url ? (
                <a key={i} href={`${s.file_url}#page=${s.page}`} target="_blank" rel="noopener noreferrer" className={styles.sourceChip} style={{ textDecoration: 'none', cursor: 'pointer' }}>
                  <FileText size={12} /> {s.file || s.source_title}, p.{s.page}
                </a>
              ) : (
                <span key={i} className={styles.sourceChip}>
                  <FileText size={12} /> {s.file || s.source_title}, p.{s.page}
                </span>
              )
            ))}
          </div>
        )}
        {msg.verified === false && (
          <div className={styles.unverifiedBanner}>
            ⚠️ This answer may not be based on your course materials. {msg.verificationReason}
          </div>
        )}
        {msg.role === 'assistant' && msg.text && !isStreaming && (
          <div className={styles.msgActions}>
            {onRegenerate && (
              <button className={styles.msgActionBtn} onClick={onRegenerate}>
                <RefreshCw size={14} /> Regenerate
              </button>
            )}
            <button className={styles.msgActionBtn}><Copy size={14} /> Copy</button>
            <button className={styles.msgActionBtn} onClick={() => onFeedback(msg.id, true)} disabled={feedbackLoading[msg.id]}>
              <ThumbsUp size={14} /> {feedbackLoading[msg.id] ? '...' : 'Helpful'}
            </button>
          </div>
        )}
        {msg.role === 'assistant' && msg.text && !isStreaming && onChip && (
          <div className={styles.chipRow}>
            {CHIP_SUGGESTIONS.map(c => (
              <button key={c} className={styles.chipBtn} onClick={() => onChip(c)}>{c}</button>
            ))}
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
  const [studentMap, setStudentMap] = useState<StudentCourseMap | null>(null);
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
  const wsRef = useRef<{ close: () => void; cancel: () => void; regenerate: () => void } | null>(null);
  const sessionId = `course_${code}`;
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  useEffect(() => {
    if (!code) return;
    const controller = new AbortController();
    Promise.all([
      coursesApi.get(code),
      chatApi.getHistory(code, sessionId).catch(() => [] as ChatMessage[]),
      coursesApi.getStudentMap(code).catch(() => null),
    ])
      .then(([courseData, history, map]) => {
        if (controller.signal.aborted) return;
        setCourse(courseData);
        setStudentMap(map);
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

  const { data: structuredTopics = [] } = useQuery({
    queryKey: ['topics', code],
    queryFn: () => coursesApi.getStructuredTopics(code),
    staleTime: 30_000,
  });

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

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  const handleSend = useCallback((overrideText?: string) => {
    const userText = overrideText ?? inputValue;
    if ((!userText.trim() && imageIds.length === 0) || streaming || !course) return;
    if (selectedDocs.length === 0 && selectedTopics.length === 0) return;
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', text: userText, images: [...imageIds] };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setImageIds([]);
    setImagePreviews([]);
    setStreaming(true);

    const assistantId = crypto.randomUUID();
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', text: '', thinkingText: '' }]);

    wsRef.current?.close();
    wsRef.current = chatApi.queryWebSocket(
      {
        question: userText, course_code: code, session_id: sessionId,
        bloom_level: bloomLevel, image_ids: imageIds.length > 0 ? imageIds : undefined,
        source_titles: selectedDocs.length > 0 ? selectedDocs : undefined,
        topics: selectedTopics.length > 0 ? selectedTopics : undefined,
      },
      {
        onThinking: (content) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, thinkingText: (m.thinkingText || '') + content } : m
          ));
        },
        onContent: (content) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, text: (m.text || '') + content } : m
          ));
        },
        onMetadata: (meta) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? {
                  ...m,
                  sources: ((meta.cited_sources || meta.sources || []) as Array<Record<string, unknown>>).map(s => ({ file: (s.source_title || s.file) as string, page: s.page as number, file_url: s.file_url as string })),
                  verified: meta.verified as boolean,
                  verificationReason: meta.verification_reason as string,
                }
              : m
          ));
        },
        onDone: () => {
          setMessages(prev => prev.filter(m => m.id !== assistantId || m.text));
          setStreaming(false);
        },
        onCancel: () => {
          setMessages(prev => prev.filter(m => m.id !== assistantId || m.text));
          setStreaming(false);
        },
        onError: () => {
          setStreaming(false);
        },
      },
    );
  }, [inputValue, streaming, course, code, sessionId, imageIds, bloomLevel, selectedDocs, selectedTopics]);

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

  const handleRegenerate = useCallback(() => {
    if (streaming || !wsRef.current) return;
    const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant');
    if (!lastAssistant) return;
    setMessages(prev => prev.map(m =>
      m.id === lastAssistant.id ? { ...m, text: '', thinkingText: '', sources: undefined } : m
    ));
    setStreaming(true);
    wsRef.current.regenerate();
  }, [streaming, messages]);

  const handleChip = useCallback((text: string) => {
    handleSend(text);
  }, [handleSend]);

  const handleStop = useCallback(() => {
    wsRef.current?.cancel();
  }, []);

  const breadcrumbs = [
    { label: 'Dashboard', href: '/student/dashboard' },
    { label: course?.course_name || code }
  ];

  const materials = course ? (course.documents || []).map((d, i) => ({
    id: i,
    name: d.name,
    file_url: d.file_url,
    meta: d.doc_type === 'curriculum' ? 'Curriculum' : d.file_size ? `${(d.file_size / 1024).toFixed(0)} KB` : 'Material',
  })) : [];

  const masteryPct = studentMap ? Math.round(studentMap.overall_mastery * 100) : 0;
  const nextTopic = studentMap?.next?.[0];
  const nextTopicName = nextTopic
    ? studentMap?.topics?.find(t => t.topic_id === nextTopic.topic_id)?.topic_name
    : undefined;

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
              <span className={styles.masteryValue}>{studentMap ? `${masteryPct}%` : '—'}</span>
            </div>
            <ProgressBar percent={masteryPct} showGradient />
            <p className={styles.nextItem}>
              <Zap size={14} className={styles.zapIcon} />
              {nextTopicName ? `Next: ${nextTopicName}` : 'Next: Ask the AI assistant a question'}
            </p>
          </div>

          <div className={styles.materialsList}>
            <h3 className={styles.materialsTitle}>
              <BookOpen size={16} />
              <span>Documents</span>
            </h3>
            {materials.length === 0 ? (
              <p className={styles.matEmpty}>No materials uploaded yet.</p>
            ) : (
              <>
                <label className={styles.sourceItem}>
                  <input
                    type="checkbox"
                    className={styles.sourceCheckbox}
                    checked={selectedDocs.length === materials.length && materials.length > 0}
                    onChange={() => {
                      if (selectedDocs.length === materials.length) {
                        setSelectedDocs([]);
                      } else {
                        setSelectedDocs(materials.map(m => m.name));
                      }
                    }}
                  />
                  <span className={styles.selectAllLabel}>Select all</span>
                </label>
                {materials.map(mat => (
                  <label key={mat.id} className={styles.sourceItem}>
                    <input
                      type="checkbox"
                      className={styles.sourceCheckbox}
                      checked={selectedDocs.includes(mat.name)}
                      onChange={() => {
                        setSelectedDocs(prev =>
                          prev.includes(mat.name)
                            ? prev.filter(n => n !== mat.name)
                            : [...prev, mat.name]
                        );
                      }}
                    />
                    <span className={styles.sourceName}>{mat.name}</span>
                    {mat.file_url && (
                      <a
                        href={`${mat.file_url}#page=1`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.sourceLink}
                        onClick={e => e.stopPropagation()}
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </label>
                ))}
              </>
            )}
          </div>

          {structuredTopics.length > 0 && (
            <div className={styles.materialsList}>
              <h3 className={styles.materialsTitle}>
                <BookOpen size={16} />
                <span>Topics</span>
              </h3>
              <label className={styles.sourceItem}>
                <input
                  type="checkbox"
                  className={styles.sourceCheckbox}
                  checked={selectedTopics.length === structuredTopics.length}
                  onChange={() => {
                    if (selectedTopics.length === structuredTopics.length) {
                      setSelectedTopics([]);
                    } else {
                      setSelectedTopics(structuredTopics.map(t => t.topic_name));
                    }
                  }}
                />
                <span className={styles.selectAllLabel}>Select all</span>
              </label>
              {structuredTopics.map(topic => (
                <label key={topic.topic_name} className={styles.sourceItem}>
                  <input
                    type="checkbox"
                    className={styles.sourceCheckbox}
                    checked={selectedTopics.includes(topic.topic_name)}
                    onChange={() => {
                      setSelectedTopics(prev =>
                        prev.includes(topic.topic_name)
                          ? prev.filter(n => n !== topic.topic_name)
                          : [...prev, topic.topic_name]
                      );
                    }}
                  />
                  <span className={styles.sourceName}>{topic.topic_name}</span>
                </label>
              ))}
            </div>
          )}
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
              messages.map((msg, idx) => (
                <ChatMessage key={msg.id} msg={msg} feedbackLoading={feedbackLoading} onFeedback={handleFeedback}
                  isStreaming={streaming && idx === messages.length - 1 && msg.role === 'assistant'}
                  onRegenerate={idx === messages.length - 1 && msg.role === 'assistant' && !streaming ? handleRegenerate : undefined}
                  onChip={idx === messages.length - 1 && msg.role === 'assistant' && !streaming ? handleChip : undefined} />
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
            {selectedDocs.length === 0 && selectedTopics.length === 0 && (
              <p className={styles.noSourcesHint}>Select at least one document or topic from the sidebar to start chatting.</p>
            )}
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
                placeholder={selectedDocs.length === 0 && selectedTopics.length === 0 ? "Select sources above to start..." : "Ask about your course materials..."}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                rows={1}
                disabled={selectedDocs.length === 0 && selectedTopics.length === 0}
              />
              <input ref={fileInputRef} type="file" accept="image/jpeg,image/png" hidden onChange={handleImageSelect} />
              <button className={styles.imageBtn} onClick={() => fileInputRef.current?.click()} disabled={streaming || uploading || imageIds.length >= 5 || (selectedDocs.length === 0 && selectedTopics.length === 0)}>
                <ImageIcon size={18} />
              </button>
              <button
                className={`${styles.sendBtn} ${streaming ? styles.stopActive : (inputValue.trim() || imageIds.length > 0) ? styles.sendActive : ''}`}
                onClick={streaming ? handleStop : handleSend}
                disabled={streaming ? false : (!inputValue.trim() && imageIds.length === 0) || (selectedDocs.length === 0 && selectedTopics.length === 0)}
                aria-label={streaming ? 'Stop generating' : 'Send message'}
              >
                {streaming ? <Square size={18} /> : <Send size={18} />}
              </button>
            </div>
            <p className={styles.disclaimer}>AI responses are generated from your uploaded course materials.</p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
