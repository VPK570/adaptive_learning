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
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [count, setCount] = useState(15);
  const [selectedBloomLevel, setSelectedBloomLevel] = useState('');
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [knownCount, setKnownCount] = useState(0);
  const [activeSetId, setActiveSetId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const startTime = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef = useRef(phase);
  const isFlippedRef = useRef(isFlipped);
  const handleKnownRef = useRef<(known: boolean) => void>(() => {});

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  const courseCode = selectedCourse || courses[0]?.course_code || '';

  const { data: savedSets = [] } = useQuery({
    queryKey: ['flashcards-saved', courseCode],
    queryFn: () => flashcardsApi.listSaved(courseCode),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const { data: topics = [] } = useQuery({
    queryKey: ['topics', courseCode],
    queryFn: () => coursesApi.getStructuredTopics(courseCode),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const topic = selectedTopic || (Array.isArray(topics) && topics.length > 0 ? topics[0].topic_name : '');
  const bloomLevel = selectedBloomLevel || (Array.isArray(topics) && topics.length > 0 ? BLOOM_MAP[topics[0].bloom_level] || '1' : '1');

  const handleTopicChange = (value: string) => {
    setSelectedTopic(value);
    const match = topics.find(t => t.topic_name === value);
    if (match) {
      const bl = BLOOM_MAP[match.bloom_level];
      if (bl) setSelectedBloomLevel(bl);
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

  useEffect(() => {
    phaseRef.current = phase;
    isFlippedRef.current = isFlipped;
    handleKnownRef.current = handleKnown;
  });

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
      setActiveSetId(null);
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
    setActiveSetId(null);
  };

  const restart = () => {
    setCurrentIdx(0);
    setIsFlipped(false);
    setKnownCount(0);
    setElapsed(0);
    setPhase('studying');
  };

  const handleStudySaved = (set: SavedFlashcardSet) => {
    if (!set.cards?.length) return;
    setCards(set.cards);
    setCurrentIdx(0);
    setIsFlipped(false);
    setKnownCount(0);
    setElapsed(0);
    setActiveSetId(set.id);
    setPhase('studying');
  };

  const handleRecordProgress = async () => {
    if (!activeSetId || !cards.length) return;
    setRecording(true);
    try {
      await flashcardsApi.record(activeSetId, { known_count: knownCount, total: cards.length });
      queryClient.invalidateQueries({ queryKey: ['flashcards-saved'] });
      showToast('Progress recorded!', 'success');
    } catch {
      showToast('Failed to record progress', 'error');
    }
    setRecording(false);
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
                    <select className={styles.selectField} value={selectedCourse} onChange={e => setSelectedCourse(e.target.value)}>
                      {courses.map(c => (
                        <option key={c.course_code} value={c.course_code}>{c.course_code}: {c.course_name}</option>
                      ))}
                    </select>
                  </div>
                  <div className={styles.formRow}>
                    <label>Topic Focus</label>
                    <input list="fc-topics" className={styles.selectField}
                      value={topic}
                      onChange={e => handleTopicChange(e.target.value)}
                      placeholder="Type a topic or select from suggestions..."
                    />
                    <datalist id="fc-topics">
                      {topics.map(t => (
                        <option key={t.topic_name} value={t.topic_name} />
                      ))}
                    </datalist>
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
                    <select className={styles.selectField} value={selectedBloomLevel} onChange={e => setSelectedBloomLevel(e.target.value)}>
                      <option value="1">Bloom&apos;s: Remember</option>
                      <option value="2">Bloom&apos;s: Understand</option>
                      <option value="3">Bloom&apos;s: Apply</option>
                      <option value="4">Bloom&apos;s: Analyze</option>
                      <option value="5">Bloom&apos;s: Evaluate</option>
                      <option value="6">Bloom&apos;s: Create</option>
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
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: 'var(--color-on-surface-variant)' }}>
                          {set.times_studied ? `Studied ×${set.times_studied}` : 'Not studied yet'}
                          {set.best_recall != null ? ` · Best ${set.best_recall}%` : ''}
                        </span>
                        <button className={styles.studyBtn} onClick={() => handleStudySaved(set)} disabled={!set.cards?.length}>
                          Study
                        </button>
                      </div>
                      <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', margin: '8px 0 0' }}>{new Date(set.created_at).toLocaleDateString()}</p>
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
            {activeSetId ? (
              <button className={styles.genBtn} onClick={handleRecordProgress} disabled={recording}>
                {recording ? 'Recording...' : 'Record Progress'}
              </button>
            ) : (
              <button className={styles.genBtn} onClick={handleSave}>Save to My Collections</button>
            )}
            <button onClick={restart} style={{ width: '100%', padding: 'var(--space-4)', border: '1px solid var(--color-outline-variant)', borderRadius: 'var(--radius-DEFAULT)', color: 'var(--color-on-surface-variant)', fontWeight: 700, font: 'var(--text-body-md)', background: 'none', cursor: 'pointer' }}>Practice Again</button>
            <button onClick={reset} style={{ background: 'none', border: 'none', color: 'var(--color-on-surface-variant)', font: 'var(--text-body-md)', cursor: 'pointer' }}>Exit to Study Sets</button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
