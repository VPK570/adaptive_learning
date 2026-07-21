"use client";

import React, { useEffect, useState } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';

import Badge from '@/app/components/Badge';
import { coursesApi } from '@/lib/api/courses';
import { analyticsApi } from '@/lib/api/analytics';
import type { Course, Analytics } from '@/lib/api/types';
import styles from './Progress.module.css';

export default function LearningProgress() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [weakTopics, setWeakTopics] = useState<string[]>([]);
  const [revisionItems, setRevisionItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    coursesApi.list()
      .then(async (list) => {
        if (controller.signal.aborted) return;
        setCourses(list);
        const topics: string[] = [];
        const revisions: string[] = [];
        await Promise.all(list.map(c =>
          analyticsApi.getMy(c.course_code)
            .then((data: Analytics) => {
              if (controller.signal.aborted) return;
              if (data?.weak_topics) topics.push(...data.weak_topics);
              if (data?.suggested_revision) revisions.push(...data.suggested_revision);
            })
            .catch(() => {})
        ));
        if (!controller.signal.aborted) {
          setWeakTopics([...new Set(topics)]);
          setRevisionItems([...new Set(revisions)]);
        }
      })
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  const statTiles = [
    { icon: 'Award', value: '—', label: 'Overall Mastery', accent: 'primary' as const },
    { icon: 'Clock', value: '—', label: 'Study Time', accent: 'secondary' as const },
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
              <p>Loading...</p>
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
            <p>Loading...</p>
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
