"use client";

import React, { useState } from 'react';
import AppShell from '../components/AppShell';
import StatTile from '../components/StatTile';
import CourseCard from '../components/CourseCard';
import DataTable from '../components/DataTable';
import ActivityHeatmap from '../components/ActivityHeatmap';
import Badge from '../components/Badge';
import { mockFacultyUser, mockFacultyStats, mockFacultyActivity, mockFacultyCourses } from '../../lib/mockData';
import styles from './Faculty.module.css';

export default function FacultyDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'courses', label: 'Courses' }
  ];

  const activityColumns = [
    { 
      key: 'student', 
      label: 'Student',
      render: (val, row) => (
        <div className={styles.studentCell}>
          <span className={styles.studentName}>{val}</span>
          <span className={styles.courseMeta}>{row.course}</span>
        </div>
      )
    },
    { 
      key: 'action', 
      label: 'Action',
      render: (val) => <Badge variant="mono-chip">{val}</Badge>
    },
    { key: 'time', label: 'Time' }
  ];

  return (
    <AppShell 
      navRole="faculty" 
      activeNavKey="dashboard" 
      topBarVariant="tabs"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      user={mockFacultyUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.welcomeBlock}>
            <h1 className={styles.greeting}>Faculty Dashboard</h1>
            <p className={styles.subtitle}>Overview of your courses and student engagement.</p>
          </div>
        </header>

        <section className={styles.statsRow}>
          <StatTile 
            iconName="Users" 
            value={mockFacultyStats.totalStudents} 
            label="Total Students" 
            accent="primary"
          />
          <StatTile 
            iconName="BookOpen" 
            value={mockFacultyStats.activeCourses} 
            label="Active Courses" 
            accent="secondary"
          />
          <StatTile 
            iconName="Activity" 
            value={`${mockFacultyStats.avgEngagement}%`} 
            label="Avg Engagement" 
            trend="+5.2%"
            accent="tertiary"
          />
        </section>

        <section className={styles.middleRow}>
          <div className={styles.activityColumn}>
            <h2 className={styles.sectionTitle}>Recent Activity</h2>
            <DataTable 
              columns={activityColumns} 
              data={mockFacultyActivity} 
              onViewAll={() => console.log('View all activity')}
            />
          </div>
          <div className={styles.heatmapColumn}>
            <h2 className={styles.sectionTitle}>Engagement Heatmap</h2>
            <div className={styles.heatmapWrapper}>
              <ActivityHeatmap rows={4} cols={7} />
            </div>
          </div>
        </section>

        <section className={styles.coursesSection}>
          <h2 className={styles.sectionTitle}>Active Courses</h2>
          <div className={styles.courseGrid}>
            {mockFacultyCourses.map(course => (
              <CourseCard key={course.id} course={course} variant="faculty" />
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
