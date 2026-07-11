"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Send, BookOpen, Sparkles, Copy, ThumbsUp, Zap } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import Badge from '@/app/components/Badge';
import ProgressBar from '@/app/components/ProgressBar';
import { coursesApi } from '@/lib/api/courses';
import { chatApi } from '@/lib/api/chat';
import type { Course, ChatMessage } from '@/lib/api/types';
import styles from './CourseDetail.module.css';

export default function CourseDetailPage({ params }: { params: { code: string } }) {
  const router = useRouter();
  const code = params?.code || '';
  const [course, setCourse] = useState<Course | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);
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
          text: h.content || h.text || '',
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

  const handleSend = useCallback(() => {
    if (!inputValue.trim() || streaming || !course) return;
    const userText = inputValue;
    const userMsg: ChatMessage = { id: Date.now(), role: 'user', text: userText };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setStreaming(true);

    const assistantId = Date.now() + 1;
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', text: '' }]);

    let fullText = '';

    chatApi.queryStream(
      { question: userText, course_code: code, session_id: sessionId },
      (content) => {
        fullText += content;
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, text: (m.text || '') + content } : m
        ));
      },
      (meta) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantId
            ? { ...m, sources: (meta.cited_sources || meta.sources || []).map(s => ({ file: s.source_title || s.file, page: s.page })) }
            : m
        ));
        setStreaming(false);
        chatApi.saveMessage(code, sessionId, 'assistant', fullText).catch(() => {});
      },
      () => { setStreaming(false); }
    );

    chatApi.saveMessage(code, sessionId, 'user', userText).catch(() => {});
  }, [inputValue, streaming, course, code, sessionId]);

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
              <p className={styles.msgText}>Loading chat...</p>
            ) : messages.length === 0 ? (
              <p className={styles.msgText}>Ask a question about your course materials.</p>
            ) : (
              messages.map(msg => (
                <div key={msg.id} className={`${styles.messageBubble} ${styles[msg.role]}`}>
                  <div className={styles.assistantContent}>
                    <p className={styles.msgText}>{msg.text}</p>
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
                    {msg.role === 'assistant' && msg.text && (
                      <div className={styles.msgActions}>
                        <button className={styles.msgActionBtn}><Copy size={14} /> Copy</button>
                        <button className={styles.msgActionBtn}><ThumbsUp size={14} /> Helpful</button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          <div className={styles.chatInputArea}>
            <div className={styles.inputWrapper}>
              <textarea
                className={styles.chatInput}
                placeholder="Ask about your course materials..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                rows={1}
              />
              <button
                className={`${styles.sendBtn} ${inputValue.trim() && !streaming ? styles.sendActive : ''}`}
                onClick={handleSend}
                disabled={!inputValue.trim() || streaming}
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
