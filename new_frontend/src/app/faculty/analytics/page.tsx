"use client";

import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AppShell from '@/app/components/AppShell';
import { api } from '@/lib/api/client';
import { coursesApi } from '@/lib/api/courses';
import { BarChart3, AlertTriangle, Lightbulb, Sparkles, CheckCircle, Clock, Zap, BookOpen, Check, X } from 'lucide-react';
import type { Analytics } from '@/lib/api/types';
import styles from './Analytics.module.css';



type QuestionRow = {
  id: string;
  course_code: string;
  question: string;
  timestamp: string | null;
  out_of_scope: boolean;
};

function getDayLabel(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { weekday: 'long' });
  } catch {
    return dateStr;
  }
}

export default function FacultyAnalyticsPage() {
  const [courseCode, setCourseCode] = useState('');
  const [period, setPeriod] = useState<'7D' | '30D'>('7D');

  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  useEffect(() => {
    if (courses.length > 0 && !courseCode) setCourseCode(courses[0].course_code);
  }, [courses]);

  const { data: analytics, isLoading: analyticsLoading, isError: analyticsError } = useQuery({
    queryKey: ['analytics', courseCode],
    queryFn: () => api.get('/analytics', { params: { course_code: courseCode } }).then(r => r.data),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const { data: questions = [], isLoading: questionsLoading, isError: questionsError } = useQuery({
    queryKey: ['questions', courseCode],
    queryFn: () => api.get('/questions', { params: { course_code: courseCode } }).then(r => r.data || []),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const { data: coverage = {}, isLoading: coverageLoading, isError: coverageError } = useQuery({
    queryKey: ['coverage', courseCode],
    queryFn: () => api.get('/analytics/coverage', { params: { course_code: courseCode } }).then(r => r.data || {}),
    enabled: !!courseCode,
    staleTime: 30_000,
  });

  const loading = analyticsLoading || questionsLoading || coverageLoading;
  const hasError = analyticsError || questionsError || coverageError;

  if (loading) {
    return (
      <AppShell navRole="faculty" activeNavKey="analytics" topBarVariant="search">
        <div className={styles.loadingContainer}>
          <div className={styles.spinner} />
        </div>
      </AppShell>
    );
  }

  if (hasError) {
    return (
      <AppShell navRole="faculty" activeNavKey="analytics" topBarVariant="search">
        <div className={styles.loadingContainer}>
          <p style={{ font: 'var(--text-body-md)', color: 'var(--color-error)', textAlign: 'center' }}>
            Failed to load analytics data. Please try again.
          </p>
        </div>
      </AppShell>
    );
  }

  const qpd = analytics?.questions_per_day || {};
  const qpdEntries = Object.entries(qpd).sort(([a], [b]) => a.localeCompare(b));
  const periodDays = period === '7D' ? 7 : 30;
  const recentQpd = qpdEntries.slice(-periodDays);
  const maxCount = Math.max(...recentQpd.map(([, c]) => c), 1);

  const totalQuestions = Object.values(qpd).reduce((a, b) => a + b, 0);
  const weakTopics = analytics?.weak_topics || [];
  const suggestedRevision = analytics?.suggested_revision || [];
  const topQuestions = analytics?.top_questions || [];
  const recentQuestions = analytics?.recent_questions || [];
  const topicCoverage = analytics?.topic_coverage || [];

  const coveredTopics = topicCoverage.filter(t => t.status === 'covered');
  const missingTopics = topicCoverage.filter(t => t.status === 'missing');

  const tableData = questions.slice(0, 10);

  return (
    <AppShell navRole="faculty" activeNavKey="analytics" topBarVariant="search">
      <div className={styles.container}>
        <div className={styles.pageHeader}>
          <div>
            <h1 style={{ font: 'var(--text-headline-lg)', color: 'var(--color-on-surface)', marginBottom: 'var(--space-2)' }}>
              Faculty Analytics
            </h1>
            <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)' }}>
              Deep insights into student engagement and conceptual gaps.
            </p>
          </div>
          <div className={styles.courseSelect}>
            <select
              value={courseCode}
              onChange={(e) => setCourseCode(e.target.value)}
            >
              {courses.map((c) => (
                <option key={c.course_code} value={c.course_code}>
                  {c.course_code} - {c.course_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className={styles.statGrid}>
          <div className={styles.statTile}>
            <div className={styles.statIcon} style={{ background: 'rgba(192, 193, 255, 0.1)', color: 'var(--color-primary)' }}>
              <BarChart3 size={20} />
            </div>
            <span style={{ font: 'var(--text-label-md)', letterSpacing: '0.01em', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase' }}>
              Total Questions
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
              <span className={styles.statValue}>{totalQuestions.toLocaleString()}</span>
              {totalQuestions > 0 && (
                <span className={styles.statChange}>+{Math.round((qpdEntries.length > 0 ? recentQpd.reduce((a, [, c]) => a + c, 0) / recentQpd.length : 0) / Math.max(totalQuestions, 1) * 100)}% vs LW</span>
              )}
            </div>
          </div>
          {(weakTopics.length > 0 || suggestedRevision.length > 0) && (
            <div className={styles.statTile}>
              <div className={styles.statIcon} style={{ background: 'rgba(255, 180, 171, 0.2)', color: 'var(--color-error)' }}>
                <AlertTriangle size={20} />
              </div>
              <span style={{ font: 'var(--text-label-md)', letterSpacing: '0.01em', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase' }}>
                Weak Topics
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                <span className={styles.statValue}>{String(weakTopics.length).padStart(2, '0')}</span>
                <span className={styles.statChange}>High priority</span>
              </div>
            </div>
          )}
          {(suggestedRevision.length > 0 || weakTopics.length > 0) && (
            <div className={styles.statTile}>
              <div className={styles.statIcon} style={{ background: 'rgba(78, 222, 163, 0.1)', color: 'var(--color-secondary)' }}>
                <Lightbulb size={20} />
              </div>
              <span style={{ font: 'var(--text-label-md)', letterSpacing: '0.01em', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase' }}>
                Suggested Revisions
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                <span className={styles.statValue}>{String(suggestedRevision.length).padStart(2, '0')}</span>
                <span className={styles.statChange}>Based on trends</span>
              </div>
            </div>
          )}
        </div>

        <div className={styles.bentoGrid}>
          <div className={styles.chartCard}>
            <div className={styles.chartHeader}>
              <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>Questions Volume</h3>
              <div className={styles.periodToggle}>
                <button
                  className={`${styles.periodBtn} ${period === '7D' ? styles.periodBtnActive : ''}`}
                  onClick={() => setPeriod('7D')}
                >
                  7D
                </button>
                <button
                  className={`${styles.periodBtn} ${period === '30D' ? styles.periodBtnActive : ''}`}
                  onClick={() => setPeriod('30D')}
                >
                  30D
                </button>
              </div>
            </div>
            <div>
              {recentQpd.map(([date, count]) => {
                const pct = (count / maxCount) * 100;
                const opacity = 0.4 + (count / maxCount) * 0.6;
                return (
                  <div key={date} className={styles.barRow}>
                    <div className={styles.barLabel}>
                      <span>{getDayLabel(date)}</span>
                      <span className={styles.barCount}>{count} queries</span>
                    </div>
                    <div className={styles.barTrack}>
                      <div
                        className={styles.barFill}
                        style={{ '--bar-width': `${pct}%` } as React.CSSProperties}
                      />
                    </div>
                  </div>
                );
              })}
              {recentQpd.length === 0 && (
                <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)', textAlign: 'center', padding: 'var(--space-10) 0' }}>
                  No query data for this period.
                </p>
              )}
            </div>
          </div>

          <div className={styles.trendingCard}>
            <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)', marginBottom: 'var(--space-6)' }}>
              Trending Questions
            </h3>
            <div className={`${styles.trendingList} ${styles.customScrollbar}`}>
              {topQuestions.map((q, i) => (
                <div key={i} className={i === 0 ? styles.trendingItemActive : styles.trendingItem}>
                  <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface)', marginBottom: 'var(--space-1)' }}>
                    &ldquo;{q.question}&rdquo;
                  </p>
                  <div className={styles.questionCount} style={{ color: i === 0 ? 'rgba(192, 193, 255, 0.8)' : 'var(--color-on-surface-variant)' }}>
                    <span style={{ color: i === 0 ? 'rgba(192, 193, 255, 0.8)' : 'var(--color-on-surface-variant)', display: 'flex', alignItems: 'center', gap: 4 }}>
                      {i === 0 ? <Zap size={14} /> : <Clock size={14} />}
                    </span>
                    <span>Asked {q.count} times</span>
                  </div>
                </div>
              ))}
              {topQuestions.length === 0 && (
                <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)', textAlign: 'center', padding: 'var(--space-10) 0' }}>
                  No trending questions yet.
                </p>
              )}
            </div>
            <button className={styles.downloadBtn} onClick={() => window.open(`/api/analytics/report/${courseCode}`, '_blank')}>
              Download Report
            </button>
          </div>
        </div>

        <div className={styles.doubleGrid}>
          <div className={styles.sectionCard}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
              <BarChart3 size={20} style={{ color: 'var(--color-error)' }} />
              <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>Conceptual Gaps</h3>
            </div>
            <div className={styles.chipGroup}>
              {weakTopics.map((t) => (
                <span key={t} className={`${styles.tagChip} ${styles.tagChipError}`}>{t}</span>
              ))}
              {weakTopics.length === 0 && (
                <span style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)' }}>No weak topics identified.</span>
              )}
            </div>
            {weakTopics.length > 0 && (
              <div className={styles.insightBox} style={{ background: 'rgba(255, 180, 171, 0.05)', borderColor: 'rgba(255, 180, 171, 0.1)' }}>
                <p className={styles.insightText}>
                  <strong style={{ color: 'var(--color-error)' }}>Insight:</strong> Students are consistently struggling with {weakTopics.slice(0, 2).join(' and ')}. Consider reviewing these topics in the next session.
                </p>
              </div>
            )}
          </div>

          <div className={styles.sectionCard}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
              <Sparkles size={20} style={{ color: 'var(--color-secondary)' }} />
              <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>AI Suggested Actions</h3>
            </div>
            <div className={styles.chipGroup}>
              {suggestedRevision.map((t) => (
                <span key={t} className={`${styles.tagChip} ${styles.tagChipSecondary}`}>{t}</span>
              ))}
              {suggestedRevision.length === 0 && (
                <span style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)' }}>Upload materials and tag them with topics to get AI suggestions.</span>
              )}
            </div>
            {suggestedRevision.length > 0 && (
              <div className={styles.insightBox} style={{ background: 'rgba(78, 222, 163, 0.05)', borderColor: 'rgba(78, 222, 163, 0.1)' }}>
                <p className={styles.insightText}>
                  <strong style={{ color: 'var(--color-secondary)' }}>Recommendation:</strong> Focus on {suggestedRevision.slice(0, 2).join(' and ')} to address coverage gaps before assessments.
                </p>
              </div>
            )}
          </div>
        </div>

        {topicCoverage.length > 0 ? (
          <div className={styles.sectionCard}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
              <BookOpen size={20} style={{ color: 'var(--color-primary)' }} />
              <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>Topic Coverage</h3>
              <span style={{ marginLeft: 'auto', font: 'var(--text-label-md)', color: 'var(--color-on-surface-variant)' }}>
                {coveredTopics.length} of {topicCoverage.length} topics covered
              </span>
            </div>
            <div className={styles.coverageBar}>
              <div className={styles.coverageFill} style={{ width: `${topicCoverage.length ? (coveredTopics.length / topicCoverage.length) * 100 : 0}%` }} />
            </div>
            <div className={styles.coverageList}>
              {topicCoverage.map(t => (
                <div key={t.topic_name} className={styles.coverageItem}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
                    {t.status === 'covered'
                      ? <Check size={16} style={{ color: 'var(--color-secondary)', flexShrink: 0 }} />
                      : <X size={16} style={{ color: 'var(--color-error)', flexShrink: 0 }} />
                    }
                    <span className={styles.coverageTopic}>{t.topic_name}</span>
                    <span className={styles.coverageBloom} style={{ flexShrink: 0 }}>{t.bloom_level}</span>
                  </div>
                  <span style={{ font: 'var(--text-label-md)', color: 'var(--color-on-surface-variant)', flexShrink: 0 }}>
                    {t.chunk_count} chunks
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.sectionCard}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
              <BookOpen size={20} style={{ color: 'var(--color-primary)' }} />
              <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>Topic Coverage</h3>
            </div>
            <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)', textAlign: 'center', padding: 'var(--space-10) 0' }}>
              Upload a curriculum PDF to extract topics and track coverage.
            </p>
          </div>
        )}

        <div className={styles.tableCard}>
          <div className={styles.tableHeader}>
            <h3 style={{ font: 'var(--text-headline-sm)', color: 'var(--color-on-surface)' }}>Live Queries Stream</h3>
            <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', font: 'var(--text-label-md)', letterSpacing: '0.01em', color: 'var(--color-secondary)' }}>
              <span className={styles.liveDot} />
              Live Now
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Query</th>
                  <th>Topic</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tableData.map((row, i) => {
                  const resolved = !row.out_of_scope;
                  return (
                    <tr key={row.id || i} className={styles.tableRow}>
                      <td style={{ color: 'var(--color-on-surface)' }}>Student #{row.id?.slice(0, 4) || i + 1}</td>
                      <td style={{ color: 'var(--color-on-surface-variant)' }}>&ldquo;{row.question.slice(0, 60)}{row.question.length > 60 ? '...' : ''}&rdquo;</td>
                      <td>
                        <span className={styles.topicBadge}>
                          {row.out_of_scope ? 'Out of Scope' : 'Course Topic'}
                        </span>
                      </td>
                      <td>
                        <span className={resolved ? styles.statusResolved : styles.statusPending}>
                          {resolved ? <CheckCircle size={16} /> : <Clock size={16} />}
                          {resolved ? 'Resolved by AI' : 'Needs Faculty'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
                {tableData.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--color-on-surface-variant)', font: 'var(--text-body-md)' }}>
                      No queries yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
