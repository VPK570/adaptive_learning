"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Send, BookOpen, Sparkles, Copy, ThumbsUp, ChevronDown, Zap } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import Badge from '@/app/components/Badge';
import ProgressBar from '@/app/components/ProgressBar';
import { mockStudentUser, courseDetail, chatMessages } from '@/lib/mockData';
import styles from './CourseDetail.module.css';

export default function CourseDetailPage({ params }) {
  const router = useRouter();
  const code = params?.code || courseDetail.code;
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState(chatMessages);
  const [activeMaterialId, setActiveMaterialId] = useState(2);
  const chatEndRef = useRef(null);

  const breadcrumbs = [
    { label: 'Dashboard', href: '/student/dashboard' },
    { label: courseDetail.title }
  ];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      text: inputValue
    }]);
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AppShell
      navRole="student"
      activeNavKey="courses"
      topBarVariant="breadcrumbBack"
      breadcrumbs={breadcrumbs}
      onBack={() => router.back()}
      user={mockStudentUser}
    >
      <div className={styles.layout}>
        {/* Left: Materials Panel */}
        <aside className={styles.materialsPanel}>
          <div className={styles.courseHeader}>
            <h2 className={styles.courseTitle}>{courseDetail.title}</h2>
            <p className={styles.courseMeta}>{courseDetail.professor} • {courseDetail.term}</p>
          </div>

          <div className={styles.masteryBlock}>
            <div className={styles.masteryRow}>
              <span className={styles.masteryLabel}>Course Mastery</span>
              <span className={styles.masteryValue}>{courseDetail.mastery}%</span>
            </div>
            <ProgressBar percent={courseDetail.mastery} showGradient />
            <p className={styles.nextItem}>
              <Zap size={14} className={styles.zapIcon} />
              Next: {courseDetail.nextItem}
            </p>
          </div>

          <div className={styles.materialsList}>
            <h3 className={styles.materialsTitle}>
              <BookOpen size={16} />
              <span>Course Materials</span>
            </h3>
            {courseDetail.materials.map(mat => (
              <button
                key={mat.id}
                className={`${styles.materialItem} ${activeMaterialId === mat.id ? styles.activeMaterial : ''}`}
                onClick={() => setActiveMaterialId(mat.id)}
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

        {/* Right: Chat Panel */}
        <section className={styles.chatPanel}>
          <div className={styles.chatHeader}>
            <Sparkles size={20} className={styles.sparkleIcon} />
            <h2 className={styles.chatTitle}>AI Study Assistant</h2>
            <span className={styles.contextTag}>Context: Ch4 Monetary Policy</span>
          </div>

          <div className={styles.chatBody}>
            {messages.map(msg => (
              <div key={msg.id} className={`${styles.messageBubble} ${styles[msg.role]}`}>
                {msg.role === 'user' ? (
                  <p className={styles.msgText}>{msg.text}</p>
                ) : (
                  <div className={styles.assistantContent}>
                    {msg.paragraphs?.map((p, i) => (
                      <p key={i} className={styles.msgText}>{p}</p>
                    ))}
                    {msg.bullets && (
                      <ul className={styles.bulletList}>
                        {msg.bullets.map((b, i) => (
                          <li key={i}>
                            <strong>{b.label}</strong> {b.text}
                          </li>
                        ))}
                      </ul>
                    )}
                    {msg.sources && (
                      <div className={styles.sourcesBlock}>
                        <span className={styles.sourcesLabel}>Sources:</span>
                        {msg.sources.map((s, i) => (
                          <span key={i} className={styles.sourceChip}>
                            <FileText size={12} /> {s.file}, p.{s.page}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className={styles.msgActions}>
                      <button className={styles.msgActionBtn}><Copy size={14} /> Copy</button>
                      <button className={styles.msgActionBtn}><ThumbsUp size={14} /> Helpful</button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className={styles.chatInputArea}>
            <div className={styles.inputWrapper}>
              <textarea
                className={styles.chatInput}
                placeholder="Ask about your course materials..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
              />
              <button 
                className={`${styles.sendBtn} ${inputValue.trim() ? styles.sendActive : ''}`}
                onClick={handleSend}
                disabled={!inputValue.trim()}
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
