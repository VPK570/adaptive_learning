"use client";

import React, { useMemo, useState } from 'react';
import { useQuery, useQueries } from '@tanstack/react-query';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import Badge from '@/app/components/Badge';
import { coursesApi } from '@/lib/api/courses';
import { analyticsApi } from '@/lib/api/analytics';
import type { Course, Analytics } from '@/lib/api/types';
import styles from './Progress.module.css';

export default function LearningProgress() {
  const { data: courses = [] } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  const analyticsResults = useQueries({
    queries: courses.map(c => ({
      queryKey: ['analytics', c.course_code],
      queryFn: ({ signal }) => analyticsApi.getMy(c.course_code, signal),
      staleTime: 30_000,
    })),
  });

  const { weakTopics, revisionItems, loading } = useMemo(() => {
    const topics: string[] = [];
    const revisions: string[] = [];
    analyticsResults.forEach(result => {
      if (result.data?.weak_topics) topics.push(...result.data.weak_topics);
      if (result.data?.suggested_revision) revisions.push(...result.data.suggested_revision);
    });
    return {
      weakTopics: [...new Set(topics)],
      revisionItems: [...new Set(revisions)],
      loading: analyticsResults.length > 0 && analyticsResults.some(r => r.isLoading),
    };
  }, [analyticsResults]);

  const { data: stats } = useQuery({
    queryKey: ['my-stats'],
    queryFn: ({ signal }) => analyticsApi.getMyStats(signal),
    staleTime: 30_000,
  });

  const overallPct = stats?.courses.length
    ? Math.round(stats.courses.reduce((s, c) => s + c.overall_mastery, 0) / stats.courses.length * 100)
    : 0;

  const statTiles = [
    { icon: 'Award', value: String(overallPct) + '%', label: 'Overall Mastery', accent: 'primary' as const },
    { icon: 'Clock', value: String(stats?.active_days ?? 0), label: 'Active Days', accent: 'secondary' as const },
    { icon: 'BookOpen', value: String(courses.length || '—'), label: 'Courses Enrolled', accent: 'tertiary' as const },
  ];

  return (
    <AppShell
      navRole="student"
      activeNavKey="progress"
      topBarVariant="search"
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.pageTitle}>Learning Progress</h1>
          <p className={styles.pageSubtitle}>Track your growth, identify weak spots, and focus your study time.</p>
        </header>

        <section className={styles.statsRow}>
          {statTiles.map((stat, i) => (
            <StatTile key={i} iconName={stat.icon} value={stat.value} label={stat.label} accent={stat.accent} />
          ))}
        </section>

        <section className={styles.middleRow}>
          <div className={styles.topicsColumn}>
            <h2 className={styles.sectionTitle}>Weak Topics</h2>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {[1,2,3].map(i => <div key={i} style={{ height: 48, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite' }} />)}
              </div>
            ) : (
              <div className={styles.topicsList}>
                {weakTopics.length === 0 ? (
                  <p>No weak topics identified yet. Ask questions in your courses.</p>
                ) : (
                  weakTopics.map((topic, i) => (
                    <div key={i} className={styles.topicItem}>
                      <span className={styles.topicName}>{topic}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          <div className={styles.heatmapColumn}>
            <h2 className={styles.sectionTitle}>Study Activity</h2>
            <div className={styles.heatmapCard}>
              <p>Study activity tracking coming soon.</p>
            </div>
          </div>
        </section>

        <section className={styles.revisionSection}>
          <h2 className={styles.sectionTitle}>Recommended for Revision</h2>
          {loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 'var(--space-3)' }}>
              {[1,2,3].map(i => <div key={i} style={{ height: 80, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', animation: 'pulse 1.5s infinite' }} />)}
            </div>
          ) : (
            <div className={styles.revisionGrid}>
              {revisionItems.length === 0 ? (
                <p>No revision suggestions yet.</p>
              ) : (
                revisionItems.map((item, i) => (
                  <div key={i} className={styles.revisionCard}>
                    <div className={styles.revisionContent}>
                      <p className={styles.revisionNote}>{item}</p>
                    </div>
                    <Badge variant="outline-pill">Review</Badge>
                  </div>
                ))
              )}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
