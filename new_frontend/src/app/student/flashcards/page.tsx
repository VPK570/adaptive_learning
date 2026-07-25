"use client";

import React, { useEffect, useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '@/app/components/AppShell';
import { flashcardsApi } from '@/lib/api/flashcards';
import { coursesApi } from '@/lib/api/courses';
import { Sparkles } from 'lucide-react';
import type { Flashcard, SavedFlashcardSet, Course, StructuredTopic } from '@/lib/api/types';
import { useToast } from '@/app/components/ToastContext';

const BLOOM_MAP: Record<string, string> = {
  Remember: '1', Understand: '2', Apply: '3', Analyze: '4', Evaluate: '5', Create: '6',
};
import styles from './Flashcards.module.css';

export default function FlashcardsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<'config' | 'studying' | 'results'>('config');
  const [courseCode, setCourseCode] = useState('');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(15);
  const [bloomLevel, setBloomLevel] = useState('1');
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [knownCount, setKnownCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const startTime = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef = useRef(phase);
  const isFlippedRef = useRef(isFlipped);
  const handleKnownRef = useRef<(known: boolean) => void>(() => {});

  phaseRef.current = phase;
  isFlippedRef.current = isFlipped;

  const { data: savedSets = [] } = useQuery({
    queryKey: ['flashcards-saved'],
    queryFn: () => flashcardsApi.listSaved(''),
    staleTime: 30_000,
  });

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (courses.length > 0 && !courseCode) setCourseCode(courses[0].course_code);
  }, [courses]);

  const { data: topics = [] } = useQuery({
    queryKey: ['topics', courseCode],
    queryFn: () => coursesApi.getStructuredTopics(courseCode),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  useEffect(() => {
    const list = Array.isArray(topics) ? topics : [];
    if (list.length > 0) {
      setTopic(list[0].topic_name);
      const bl = BLOOM_MAP[list[0].bloom_level];
      if (bl) setBloomLevel(bl);
    }
  }, [topics]);

  const handleTopicChange = (value: string) => {
    setTopic(value);
    const match = topics.find(t => t.topic_name === value);
    if (match) {
      const bl = BLOOM_MAP[match.bloom_level];
      if (bl) setBloomLevel(bl);
    }
  };

  useEffect(() => {
    if (phase === 'studying') {
      startTime.current = Date.now();
      timerRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTime.current) / 1000));
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [phase]);

  const handleKnown = (known: boolean) => {
    if (known) setKnownCount(c => c + 1);
    if (currentIdx < cards.length - 1) {
      setCurrentIdx(i => i + 1);
      setIsFlipped(false);
    } else {
      setPhase('results');
    }
  };

  handleKnownRef.current = handleKnown;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (phaseRef.current !== 'studying') return;
      if (e.code === 'Space') {
        e.preventDefault();
        setIsFlipped(v => !v);
      }
      if (isFlippedRef.current) {
        if (e.code === 'ArrowRight' || e.code === 'KeyD') handleKnownRef.current(true);
        if (e.code === 'ArrowLeft' || e.code === 'KeyA') handleKnownRef.current(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await flashcardsApi.generate({
        course_code: courseCode,
        topic: topic || 'general',
        count,
        bloom_levels: [parseInt(bloomLevel)],
      });
      if (!result.length) {
        setError('No cards generated. Try a different topic.');
        setLoading(false);
        return;
      }
      setCards(result);
      setCurrentIdx(0);
      setIsFlipped(false);
      setKnownCount(0);
      setElapsed(0);
      setPhase('studying');
    } catch {
      setError('Failed to generate cards. Please try again.');
    }
    setLoading(false);
  };

  const handleSave = async () => {
    try {
      await flashcardsApi.save({
        course_code: courseCode,
        topic: topic || 'general',
        cards,
      });
      queryClient.invalidateQueries({ queryKey: ['flashcards-saved'] });
      showToast('Saved to collections!', 'success');
    } catch {
      showToast('Failed to save set', 'error');
      setError('Failed to save set');
    }
  };

  const reset = () => {
    setPhase('config');
    setCards([]);
    setCurrentIdx(0);
    setIsFlipped(false);
    setKnownCount(0);
    setElapsed(0);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}m ${sec.toString().padStart(2, '0')}s`;
  };

  const progress = cards.length ? ((currentIdx + 1) / cards.length) * 100 : 0;

  return (
    <AppShell navRole="student" activeNavKey="flashcards" topBarVariant="search">
      <div className={styles.container}>
        {phase === 'config' && (
          <>
            <div className={styles.header}>
              <h1>Flashcard Generator</h1>
              <p>Leverage AI to synthesize complex course materials into active-recall study sets. Select your parameters below to begin.</p>
            </div>
            <div className={styles.configGrid}>
              <div className={styles.configPanel}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
                  <div className={styles.formRow}>
                    <label>Select Course</label>
                    <select className={styles.selectField} value={courseCode} onChange={e => setCourseCode(e.target.value)}>
                      {courses.map(c => (
                        <option key={c.course_code} value={c.course_code}>{c.course_code}: {c.course_name}</option>
                      ))}
                    </select>
                  </div>
                  <div className={styles.formRow}>
                    <label>Topic Focus</label>
                    <select className={styles.selectField} value={topic} onChange={e => handleTopicChange(e.target.value)}>
                      {topics.length === 0 && <option value="">No topics available</option>}
                      {topics.map(t => (
                        <option key={t.topic_name} value={t.topic_name}>
                          {t.topic_name} ({t.bloom_level})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className={styles.formRow}>
                    <label>Card Count</label>
                    <div className={styles.counter}>
                      <button className={styles.counterBtn} onClick={() => setCount(c => Math.max(5, c - 1))}>-</button>
                      <span className={styles.counterValue}>{count}</span>
                      <button className={styles.counterBtn} onClick={() => setCount(c => Math.min(25, c + 1))}>+</button>
                    </div>
                  </div>
                  <div className={styles.formRow}>
                    <label>Cognitive Level</label>
                    <select className={styles.selectField} value={bloomLevel} onChange={e => setBloomLevel(e.target.value)}>
                      <option value="1">Bloom's: Remember</option>
                      <option value="2">Bloom's: Understand</option>
                      <option value="3">Bloom's: Apply</option>
                      <option value="4">Bloom's: Analyze</option>
                      <option value="5">Bloom's: Evaluate</option>
                      <option value="6">Bloom's: Create</option>
                    </select>
                  </div>
                </div>
                <button className={styles.genBtn} onClick={handleGenerate} disabled={loading}>
                  {loading ? 'Generating...' : 'Generate Smart Deck'}
                </button>
                {error && <p style={{ color: 'var(--color-error)', fontSize: 13, margin: 0 }}>{error}</p>}
              </div>
              <div className={styles.historyPanel}>
                <h3>Recent Study Sets</h3>
                <div className={styles.customScrollbar}>
                  {savedSets.map(set => (
                    <div key={set.id} className={styles.historyCard}>
                      <span className={styles.historyCardCode}>{set.course_code}</span>
                      <p style={{ font: 'var(--text-headline-sm)', fontSize: 14, margin: '4px 0' }}>{set.topic}</p>
                      <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', margin: 0 }}>{new Date(set.created_at).toLocaleDateString()}</p>
                    </div>
                  ))}
                  {!savedSets.length && <p style={{ fontSize: 13, color: 'var(--color-on-surface-variant)' }}>No saved sets yet.</p>}
                </div>
              </div>
            </div>
          </>
        )}

        {phase === 'studying' && cards.length > 0 && (
          <div className={styles.studyingSection}>
            <div className={styles.studyHeader}>
              <button onClick={reset} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-on-surface-variant)', font: 'var(--text-label-md)', background: 'none', border: 'none', cursor: 'pointer' }}>
                Exit Session
              </button>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <span style={{ font: 'var(--text-mono-md)', fontSize: 13, color: 'var(--color-on-surface-variant)' }}>Card {currentIdx + 1} of {cards.length}</span>
                <div className={styles.progressBar}>
                  <div className={styles.progressFill} style={{ width: `${progress}%` }} />
                </div>
              </div>
            </div>

            <div className={styles.flashcard3d} onClick={() => setIsFlipped(v => !v)}>
              <div className={`${styles.flashcardInner} ${isFlipped ? styles.flipped : ''}`}>
                <div className={styles.cardFront}>
                  <span className={styles.cardLabel}>Question</span>
                  <div className={styles.cardContent}>{cards[currentIdx].question}</div>
                  <p style={{ marginTop: 32, color: 'var(--color-on-surface-variant)', opacity: 0.4, fontSize: 13, fontStyle: 'italic' }}>Click to reveal answer</p>
                </div>
                <div className={styles.cardBack}>
                  <span className={styles.cardLabel} style={{ color: 'var(--color-secondary)' }}>Answer</span>
                  <div className={styles.cardContent}>{cards[currentIdx].answer}</div>
                </div>
              </div>
            </div>

            <div className={`${styles.actionButtons} ${!isFlipped ? styles.actionButtonsHidden : ''}`}>
              <button className={`${styles.actionBtn} ${styles.actionBtnLearning}`} onClick={() => handleKnown(false)}>
                Still Learning
              </button>
              <button className={`${styles.actionBtn} ${styles.actionBtnGotIt}`} onClick={() => handleKnown(true)}>
                Got It
              </button>
            </div>
          </div>
        )}

        {phase === 'results' && (
          <div className={styles.resultsSection}>
            <div>
              <div className={styles.resultsIcon}>
                <Sparkles size={48} style={{ color: 'var(--color-primary)' }} />
              </div>
              <h2>Session Complete</h2>
              <p>Great work! You mastered {cards.length ? Math.round((knownCount / cards.length) * 100) : 0}% of the concepts in this deck.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className={styles.resultStat}>
                <p className={styles.resultStatLabel}>Time Spent</p>
                <p className={styles.resultStatValue} style={{ color: 'var(--color-primary)' }}>{formatTime(elapsed)}</p>
              </div>
              <div className={styles.resultStat}>
                <p className={styles.resultStatLabel}>Recall Rate</p>
                <p className={styles.resultStatValue} style={{ color: 'var(--color-secondary)' }}>{knownCount} / {cards.length}</p>
              </div>
            </div>
            <button className={styles.genBtn} onClick={handleSave}>Save to My Collections</button>
            <button onClick={reset} style={{ width: '100%', padding: 'var(--space-4)', border: '1px solid var(--color-outline-variant)', borderRadius: 'var(--radius-DEFAULT)', color: 'var(--color-on-surface-variant)', fontWeight: 700, font: 'var(--text-body-md)', background: 'none', cursor: 'pointer' }}>Practice Again</button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
