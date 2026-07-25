"use client";

import React from 'react';
import AppShell from '@/app/components/AppShell';
import RadialProgress from '@/app/components/RadialProgress';
import StatTile from '@/app/components/StatTile';
import CourseCard from '@/app/components/CourseCard';
import { useQuery } from '@tanstack/react-query';
import { coursesApi } from '@/lib/api/courses';
import { useAuthStore } from '@/lib/store/authStore';
import type { Course } from '@/lib/api/types';
import styles from './Dashboard.module.css';

export default function StudentDashboard() {
  const user = useAuthStore(s => s.user);
  const { data: courses = [], isLoading, error } = useQuery({
    queryKey: ['courses'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  const userName = user?.name?.split(' ')[0] || 'Student';
  const courseCards = courses.map(c => ({
    id: c.course_code,
    title: c.course_name,
    description: c.description,
    color: 'blue',
    docCount: c.doc_count || 0,
  }));

  return (
    <AppShell navRole="student" activeNavKey="dashboard" topBarVariant="search">
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.welcomeBlock}>
            <h1 className={styles.greeting}>Welcome back, {userName}</h1>
            <p className={styles.subtitle}>Here's where you left off. Keep up the momentum.</p>
          </div>
        </header>

        <section className={styles.statsSection}>
          <div className={styles.radialWrapper}>
            <RadialProgress percent={0} label="OVERALL" />
          </div>

          <div className={styles.statGrid}>
            <StatTile iconName="Flame" value="—" label="Current Streak" accent="tertiary" />
            <StatTile iconName="CheckCircle" value="—" label="Topics Completed" accent="primary" />
            <StatTile iconName="Award" value="—" label="Quizzes Taken" accent="secondary" />
          </div>
        </section>

        <section className={styles.coursesSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Continue Learning</h2>
          </div>

          {isLoading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-4)' }}>
              {[1,2,3].map(i => (
                <div key={i} style={{ height: 160, borderRadius: 'var(--radius-md)', background: 'var(--color-surface-container)', opacity: 0.5 }} />
              ))}
            </div>
          ) : error ? (
            <p className={styles.error}>{error.message}</p>
          ) : (
            <div className={styles.courseGrid}>
              {courseCards.map(course => (
                <CourseCard key={course.id} course={course} variant="student" />
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
