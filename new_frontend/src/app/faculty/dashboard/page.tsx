"use client";

import React, { useState } from 'react';
import AppShell from '@/app/components/AppShell';
import StatTile from '@/app/components/StatTile';
import CourseCard from '@/app/components/CourseCard';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { coursesApi } from '@/lib/api/courses';
import type { Course } from '@/lib/api/types';
import AddCourseModal from './AddCourseModal';
import { Plus } from 'lucide-react';
import styles from './Faculty.module.css';

export default function FacultyDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showAddModal, setShowAddModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses', 'faculty'],
    queryFn: ({ signal }) => coursesApi.list(signal),
    staleTime: 30_000,
  });

  const tabs = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'courses', label: 'Courses' }
  ];

  const courseCards = courses.map(c => ({
    id: c.course_code,
    code: c.course_code,
    title: c.course_name,
    term: '—',
    students: String(c.student_count ?? 0),
    status: 'Active',
  }));

  const totalStudents = courses.reduce((s, c) => s + (c.student_count || 0), 0);
  const totalQueries = courses.reduce((s, c) => s + (c.total_queries || 0), 0);
  const avgEngagement = courses.length ? Math.round(totalQueries / courses.length) : 0;

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
          <div className={styles.headerActions}>
            <button className={styles.addBtn} onClick={() => setShowAddModal(true)}>
              <Plus size={18} />
              Add Course
            </button>
          </div>
        </header>

        <section className={styles.statsRow}>
          <StatTile iconName="Users" value={String(totalStudents)} label="Total Students" accent="primary" />
          <StatTile iconName="BookOpen" value={String(courses.length || '—')} label="Active Courses" accent="secondary" />
          <StatTile iconName="Activity" value={String(avgEngagement)} label="Avg Engagement" accent="tertiary" />
        </section>

        <section className={styles.coursesSection}>
          <h2 className={styles.sectionTitle}>Active Courses</h2>
          {isLoading ? (
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

      <AddCourseModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['courses', 'faculty'] })}
      />
    </AppShell>
  );
}
