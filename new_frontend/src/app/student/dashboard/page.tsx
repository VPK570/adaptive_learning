import React from 'react';
import AppShell from '@/app/components/AppShell';
import RadialProgress from '@/app/components/RadialProgress';
import StatTile from '@/app/components/StatTile';
import CourseCard from '@/app/components/CourseCard';
import { mockStudentUser, mockStudentStats, mockStudentCourses } from '@/lib/mockData';
import styles from './Dashboard.module.css';

export default function StudentDashboard() {
  return (
    <AppShell 
      navRole="student" 
      activeNavKey="dashboard" 
      topBarVariant="search"
      user={mockStudentUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.welcomeBlock}>
            <h1 className={styles.greeting}>Welcome back, {mockStudentUser.name.split(' ')[0]}</h1>
            <p className={styles.subtitle}>Here's where you left off. Keep up the momentum.</p>
          </div>
        </header>

        <section className={styles.statsSection}>
          <div className={styles.radialWrapper}>
            <RadialProgress percent={mockStudentStats.mastery} label="OVERALL" />
          </div>
          
          <div className={styles.statGrid}>
            <StatTile 
              iconName="Flame" 
              value={`${mockStudentStats.streak} days`} 
              label="Current Streak" 
              accent="tertiary"
            />
            <StatTile 
              iconName="CheckCircle" 
              value={mockStudentStats.topicsCompleted} 
              label="Topics Completed" 
              accent="primary"
            />
            <StatTile 
              iconName="Award" 
              value={mockStudentStats.quizzesTaken} 
              label="Quizzes Taken" 
              accent="secondary"
            />
          </div>
        </section>

        <section className={styles.coursesSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Continue Learning</h2>
          </div>
          
          <div className={styles.courseGrid}>
            {mockStudentCourses.map(course => (
              <CourseCard key={course.id} course={course} variant="student" />
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
