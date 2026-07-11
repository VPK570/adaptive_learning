"use client";

import React, { useState, useEffect } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import CourseCard from '@/app/components/CourseCard';
import { coursesApi } from '@/lib/api/courses';
import type { Course } from '@/lib/api/types';
import styles from './Faculty.module.css';

export default function FacultyDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    coursesApi.list()
      .then(data => { if (!controller.signal.aborted) setCourses(data); })
      .catch(() => {})
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  const tabs = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'courses', label: 'Courses' }
  ];

  const courseCards = courses.map(c => ({
    id: c.course_code,
    code: c.course_code,
    title: c.course_name,
    term: '—',
    students: '—',
    status: 'Active',
  }));

  return (
    <AppShell
      navRole="faculty"
      activeNavKey="dashboard"
      topBarVariant="tabs"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.welcomeBlock}>
            <h1 className={styles.greeting}>Faculty Dashboard</h1>
            <p className={styles.subtitle}>Overview of your courses and materials.</p>
          </div>
        </header>

        <section className={styles.statsRow}>
          <StatTile iconName="Users" value="—" label="Total Students" accent="primary" />
          <StatTile iconName="BookOpen" value={String(courses.length || '—')} label="Active Courses" accent="secondary" />
          <StatTile iconName="Activity" value="—" label="Avg Engagement" accent="tertiary" />
        </section>

        <section className={styles.coursesSection}>
          <h2 className={styles.sectionTitle}>Active Courses</h2>
          {loading ? (
            <p>Loading courses...</p>
          ) : (
            <div className={styles.courseGrid}>
              {courseCards.map(course => (
                <CourseCard key={course.id} course={course} variant="faculty" />
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
