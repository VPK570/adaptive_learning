"use client";

import React, { useEffect, useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '@/app/components/AppShell';
import { quizApi } from '@/lib/api/quiz';
import { coursesApi } from '@/lib/api/courses';
import { analyticsApi } from '@/lib/api/analytics';
import { Library, CheckCircle, SlidersHorizontal, BarChart3, Timer, Check, Lightbulb, ArrowRight, Trophy, X } from 'lucide-react';
import type { QuizQuestion, SavedQuiz, Course, StructuredTopic } from '@/lib/api/types';
import { useToast } from '@/app/components/ToastContext';
import styles from './Quiz.module.css';

const BLOOM_LEVELS = [
  { level: 1, label: 'Remember' },
  { level: 2, label: 'Understand' },
  { level: 3, label: 'Apply' },
  { level: 4, label: 'Analyze' },
  { level: 5, label: 'Evaluate' },
  { level: 6, label: 'Create' },
];

const BLOOM_MAP: Record<string, number> = {
  Remember: 1, Understand: 2, Apply: 3, Analyze: 4, Evaluate: 5, Create: 6,
};

export default function QuizPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [courseCode, setCourseCode] = useState('');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(10);
  const [bloomLevels, setBloomLevels] = useState<number[]>([1, 3]);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [answered, setAnswered] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timer, setTimer] = useState(0);
  const [saving, setSaving] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (courses.length > 0 && !courseCode) {
      setCourseCode(courses[0].course_code);
      setTopic(courses[0].course_name);
    }
  }, [courses]);

  const { data: analyticsData } = useQuery({
    queryKey: ['analytics', courseCode],
    queryFn: ({ signal }) => analyticsApi.getMy(courseCode, signal),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  useEffect(() => {
    if (analyticsData?.bloom_mastery && Object.keys(analyticsData.bloom_mastery).length > 0) {
      const weak = BLOOM_LEVELS
        .filter(bl => (analyticsData.bloom_mastery![bl.level] ?? 0) < 0.7)
        .map(bl => bl.level);
      if (weak.length > 0) setBloomLevels(weak);
    }
  }, [analyticsData]);

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
    }
  }, [topics]);

  const { data: savedQuizzes = [] } = useQuery({
    queryKey: ['quiz-saved', courseCode],
    queryFn: () => quizApi.listSaved(courseCode),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const handleTopicChange = (value: string) => {
    setTopic(value);
    const match = topics.find(t => t.topic_name === value);
    if (match) {
      const bl = BLOOM_MAP[match.bloom_level];
      if (bl) setBloomLevels([bl]);
    }
  };

  useEffect(() => {
    if (questions.length > 0 && !showResults) {
      timerRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [questions.length, showResults]);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await quizApi.generate({ course_code: courseCode, topic, count, bloom_levels: bloomLevels.length ? bloomLevels : undefined });
      setQuestions(data);
      setCurrentIndex(0);
      setSelectedOption(null);
      setAnswered(false);
      setShowResults(false);
      setTimer(0);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (index: number) => {
    if (answered) return;
    setSelectedOption(index);
    setAnswered(true);
    const updated = [...questions];
    updated[currentIndex] = { ...updated[currentIndex], user_answer_index: index, is_correct: index === updated[currentIndex].correct_index };
    setQuestions(updated);
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
      setSelectedOption(null);
      setAnswered(false);
    } else {
      setShowResults(true);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const correctCount = questions.filter((q) => q.is_correct).length;
      await quizApi.save({ course_code: courseCode, topic, questions, score: correctCount, total: questions.length, bloom_levels: bloomLevels });
      queryClient.invalidateQueries({ queryKey: ['quiz-saved', courseCode] });
      showToast('Results saved!', 'success');
    } catch {
      showToast('Failed to save results', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handlePracticeAgain = () => {
    setQuestions([]);
    setShowResults(false);
    setCurrentIndex(0);
    setSelectedOption(null);
    setAnswered(false);
    setTimer(0);
  };

  const toggleBloom = (level: number) => {
    setBloomLevels((prev) => prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const correctCount = questions.filter((q) => q.is_correct).length;
  const scorePct = questions.length ? Math.round((correctCount / questions.length) * 100) : 0;

  const q = questions[currentIndex];

  return (
    <AppShell navRole="student" activeNavKey="quiz" topBarVariant="search">
      <div className={styles.container}>
        {questions.length === 0 && !showResults && (
          <>
            <section className={styles.headerSection}>
              <h1>AI Assessment Lab</h1>
              <p>Select a course to generate a specialized quiz tailored to your learning progress.</p>
            </section>

            <section className={styles.configGrid}>
              <div className={styles.glassCard}>
                <h3>
                  <Library size={20} style={{ color: 'var(--color-primary)' }} />
                  Select Knowledge Source
                </h3>
                <div className={styles.courseGrid}>
                  {courses.map((c) => (
                    <label key={c.course_code} className={`${styles.courseOption} ${courseCode === c.course_code ? styles.courseOptionActive : ''}`}>
                      <input type="radio" name="course" checked={courseCode === c.course_code} onChange={() => setCourseCode(c.course_code)} />
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-2)' }}>
                          <span className={styles.courseCode}>{c.course_code}</span>
                          <CheckCircle size={20} className={styles.checkIcon} style={{ opacity: courseCode === c.course_code ? 1 : 0 }} />
                        </div>
                        <p style={{ fontWeight: 600, fontSize: 14 }}>{c.course_name}</p>
                      </div>
                    </label>
                  ))}
                </div>
                <div style={{ marginTop: 'var(--space-6)' }}>
                  <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-3)' }}>Topic Focus</p>
                  <select
                    value={topic}
                    onChange={(e) => handleTopicChange(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'var(--color-surface-container-low)',
                      border: '1px solid var(--color-outline-variant)',
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-3)',
                      fontSize: 14,
                      color: 'var(--color-on-surface)',
                      outline: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    {topics.length === 0 && <option value="">No topics available</option>}
                    {topics.map(t => (
                      <option key={t.topic_name} value={t.topic_name}>
                        {t.topic_name} ({t.bloom_level})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className={styles.glassCard} style={{ display: 'flex', flexDirection: 'column' }}>
                <h3>
                  <SlidersHorizontal size={20} style={{ color: 'var(--color-secondary)' }} />
                  Quiz Parameters
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', flex: 1 }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
                      <label style={{ fontSize: 12, fontWeight: 600 }}>Question Count</label>
                      <span style={{ font: 'var(--text-mono-md)', color: 'var(--color-primary)' }}>{count}</span>
                    </div>
                    <input
                      type="range" min={5} max={20} value={count}
                      onChange={(e) => setCount(Number(e.target.value))}
                      style={{ width: '100%', accentColor: 'var(--color-primary)', height: 4, background: 'var(--color-surface-container-high)', borderRadius: 'var(--radius-md)', appearance: 'none', cursor: 'pointer' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 'var(--space-3)' }}>Bloom&apos;s Taxonomy Levels</label>
                    <div className={styles.bloomFilters}>
                      {BLOOM_LEVELS.map((bl) => (
                        <button
                          key={bl.level}
                          className={`${styles.bloomPill} ${bloomLevels.includes(bl.level) ? styles.bloomPillActive : ''}`}
                          onClick={() => toggleBloom(bl.level)}
                        >
                          {bl.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  style={{
                    width: '100%',
                    marginTop: 'var(--space-8)',
                    padding: 'var(--space-3)',
                    background: 'var(--color-primary)',
                    color: 'var(--color-on-primary)',
                    borderRadius: 'var(--radius-md)',
                    fontWeight: 600,
                    border: 'none',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    fontFamily: 'inherit',
                    fontSize: 14,
                  }}
                >
                  {loading ? 'Generating...' : 'Generate Session'}
                </button>
                {error && <p style={{ color: 'var(--color-error)', fontSize: 13, marginTop: 'var(--space-2)' }}>{error}</p>}
              </div>
            </section>

            {savedQuizzes.length > 0 && (
              <section>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 'var(--space-6)' }}>
                  <div>
                    <h3 style={{ font: 'var(--text-headline-sm)' }}>Performance History</h3>
                    <p style={{ color: 'var(--color-on-surface-variant)', fontSize: 12, marginTop: 4 }}>Review your previously generated sessions and analyze weak points.</p>
                  </div>
                </div>
                <div className={styles.historyGrid}>
                  {savedQuizzes.map((sq) => (
                    <div key={sq.id} className={styles.historyCard}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
                        <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container-high)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <BarChart3 size={20} style={{ color: 'var(--color-primary)' }} />
                        </div>
                        <span className={sq.score >= 70 ? styles.badgeScore : styles.badgeError}>
                          SCORE: {sq.score}%
                        </span>
                      </div>
                      <h4 style={{ fontWeight: 600, fontSize: 14 }}>{sq.topic}</h4>
                      <p style={{ fontSize: 11, color: 'var(--color-on-surface-variant)', marginTop: 4 }}>{sq.course_code} • {new Date(sq.created_at).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {questions.length > 0 && !showResults && (
          <section className={styles.quizInterface}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                <div>
                  <h3 style={{ font: 'var(--text-headline-sm)' }}>Question {currentIndex + 1} of {questions.length}</h3>
                  <div className={styles.progressBar}>
                    <div style={{ width: `${((currentIndex + (answered ? 1 : 0)) / questions.length) * 100}%` }} />
                  </div>
                </div>
              </div>
              <div className={styles.timer}>
                <Timer size={14} style={{ color: 'var(--color-secondary)' }} />
                <span>{formatTime(timer)}</span>
              </div>
            </div>

            {q && (
              <div className={styles.questionCard}>
                <div className={styles.questionTags}>
                  <span style={{ background: 'rgba(192, 193, 255, 0.1)', color: 'var(--color-primary)' }}>
                    BLOOM: ANALYZE
                  </span>
                  <span style={{ background: 'rgba(78, 222, 163, 0.1)', color: 'var(--color-secondary)' }}>
                    DIFFICULTY: MEDIUM
                  </span>
                </div>
                <h4 style={{ font: 'var(--text-headline-md)', marginBottom: 'var(--space-8)', lineHeight: 1.6 }}>{q.question}</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  {q.options.map((opt, idx) => {
                    const isSelected = selectedOption === idx;
                    const isCorrectOpt = answered && idx === q.correct_index;
                    return (
                      <button key={idx} className={`${styles.optionBtn} ${isSelected ? styles.optionSelected : ''} ${isCorrectOpt ? styles.optionCorrect : ''}`} onClick={() => handleSelectOption(idx)}>
                        <span>{opt}</span>
                        <div style={{
                          width: 20, height: 20, borderRadius: 'var(--radius-full)',
                          border: isCorrectOpt ? 'none' : '2px solid var(--color-outline-variant)',
                          background: isCorrectOpt ? 'var(--color-secondary)' : isSelected && !answered ? 'var(--color-primary)' : 'transparent',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        }}>
                          {isCorrectOpt && (
                            <Check size={12} style={{ color: 'var(--color-on-secondary)' }} />
                          )}
                          {isSelected && !answered && (
                            <div style={{ width: 8, height: 8, borderRadius: 'var(--radius-full)', background: 'var(--color-on-primary)' }} />
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {answered && (
                  <div className={styles.feedbackArea}>
                    <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start' }}>
                      <div style={{ padding: 'var(--space-2)', borderRadius: 'var(--radius-md)', background: 'rgba(78, 222, 163, 0.2)', color: 'var(--color-secondary)' }}>
                        <Lightbulb size={20} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontWeight: 600, fontSize: 14, color: q.is_correct ? 'var(--color-secondary)' : 'var(--color-error)' }}>
                          {q.is_correct ? 'Correct Insight' : 'Incorrect'}
                        </p>
                        <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', marginTop: 4, lineHeight: 1.6 }}>{q.explanation}</p>
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-4)' }}>
                      <button className={styles.nextBtn} onClick={handleNext}>
                        {currentIndex < questions.length - 1 ? 'Next Question' : 'See Results'}
                        <ArrowRight size={18} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {showResults && (
          <section className={styles.resultsScreen}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-6)' }}>
                <div className={styles.scoreCircle}>
                  {scorePct}%
                  <div style={{ position: 'absolute', top: -8, right: -8, background: 'var(--color-secondary)', color: 'var(--color-on-secondary)', padding: 6, borderRadius: 'var(--radius-full)' }}>
                    <Trophy size={16} />
                  </div>
                </div>
              </div>
              <h2 style={{ font: 'var(--text-headline-lg)' }}>{scorePct >= 80 ? 'Excellent Mastery!' : scorePct >= 60 ? 'Good Effort!' : 'Keep Practicing!'}</h2>
              <p style={{ color: 'var(--color-on-surface-variant)', marginTop: 'var(--space-2)' }}>
                You answered {correctCount} of {questions.length} questions correctly.
              </p>
            </div>

            <div className={styles.resultStats} style={{ marginTop: 'var(--space-8)' }}>
              <div className={styles.glassCard} style={{ textAlign: 'center', borderBottom: '2px solid var(--color-primary)' }}>
                <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', fontWeight: 600 }}>Total Time</p>
                <p style={{ fontSize: 24, fontWeight: 700, marginTop: 'var(--space-2)' }}>{formatTime(timer)}</p>
              </div>
              <div className={styles.glassCard} style={{ textAlign: 'center', borderBottom: '2px solid var(--color-secondary)' }}>
                <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', fontWeight: 600 }}>Correct</p>
                <p style={{ fontSize: 24, fontWeight: 700, marginTop: 'var(--space-2)' }}>{correctCount}/{questions.length}</p>
              </div>
              <div className={styles.glassCard} style={{ textAlign: 'center', borderBottom: '2px solid var(--color-tertiary)' }}>
                <p style={{ fontSize: 12, color: 'var(--color-on-surface-variant)', textTransform: 'uppercase', fontWeight: 600 }}>Avg. Response</p>
                <p style={{ fontSize: 24, fontWeight: 700, marginTop: 'var(--space-2)' }}>{questions.length ? Math.round(timer / questions.length) : 0}s</p>
              </div>
            </div>

            <div className={styles.glassCard} style={{ marginTop: 'var(--space-8)', padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: 'var(--space-4) var(--space-6)', background: 'var(--color-surface-container-low)', borderBottom: '1px solid var(--color-outline-variant)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ fontWeight: 600 }}>Review Questions</h4>
              </div>
              <div className={styles.reviewList}>
                {questions.map((item, idx) => (
                  <div key={idx} style={{ padding: 'var(--space-6)', display: 'flex', gap: 'var(--space-4)' }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: 'var(--radius-full)',
                      background: item.is_correct ? 'rgba(78, 222, 163, 0.2)' : 'rgba(255, 180, 171, 0.2)',
                      color: item.is_correct ? 'var(--color-secondary)' : 'var(--color-error)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      {item.is_correct ? <Check size={14} /> : <X size={14} />}
                    </div>
                    <div>
                      <p style={{ fontSize: 14, fontWeight: 500 }}>{item.question}</p>
                      <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                        <span className={styles.pillTag}>{item.is_correct ? 'Correct' : 'Incorrect'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-4)', padding: 'var(--space-8) 0' }}>
              <button
                onClick={handlePracticeAgain}
                style={{
                  padding: 'var(--space-3) var(--space-8)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-outline-variant)',
                  background: 'transparent',
                  color: 'var(--color-on-surface)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  fontSize: 14,
                }}
              >
                Practice Again
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  padding: 'var(--space-3) var(--space-8)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-primary)',
                  color: 'var(--color-on-primary)',
                  fontWeight: 600,
                  border: 'none',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.7 : 1,
                  fontFamily: 'inherit',
                  fontSize: 14,
                }}
              >
                {saving ? 'Saving...' : 'Save Results'}
              </button>
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
