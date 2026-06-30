import React from 'react';
import AppShell from '../components/AppShell';
import StatTile from '../components/StatTile';
import ProgressBar from '../components/ProgressBar';
import ActivityHeatmap from '../components/ActivityHeatmap';
import Badge from '../components/Badge';
import { mockStudentUser, progressStats, topicsBreakdown, recommendedRevision } from '../../lib/mockData';
import styles from './Progress.module.css';

export default function LearningProgress() {
  return (
    <AppShell
      navRole="student"
      activeNavKey="progress"
      topBarVariant="search"
      user={mockStudentUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.pageTitle}>Learning Progress</h1>
          <p className={styles.pageSubtitle}>Track your growth, identify weak spots, and focus your study time.</p>
        </header>

        <section className={styles.statsRow}>
          {progressStats.map((stat, i) => (
            <StatTile
              key={i}
              iconName={stat.icon}
              value={stat.value}
              label={stat.label}
              trend={stat.trend}
              caption={stat.caption}
              accent={i === 0 ? 'primary' : i === 1 ? 'secondary' : 'tertiary'}
            />
          ))}
        </section>

        <section className={styles.middleRow}>
          <div className={styles.topicsColumn}>
            <h2 className={styles.sectionTitle}>Topics Breakdown</h2>
            <div className={styles.topicsList}>
              {topicsBreakdown.map((topic, i) => (
                <div key={i} className={styles.topicItem}>
                  <div className={styles.topicHeader}>
                    <span className={styles.topicName}>{topic.topic}</span>
                    <span className={styles.topicPercent}>{topic.percent}%</span>
                  </div>
                  <ProgressBar percent={topic.percent} intensity={topic.intensity} />
                </div>
              ))}
            </div>
          </div>

          <div className={styles.heatmapColumn}>
            <h2 className={styles.sectionTitle}>Study Activity</h2>
            <div className={styles.heatmapCard}>
              <ActivityHeatmap rows={5} cols={7} />
              <div className={styles.heatmapStats}>
                <div className={styles.heatmapStat}>
                  <span className={styles.heatmapValue}>23</span>
                  <span className={styles.heatmapLabel}>Active Days</span>
                </div>
                <div className={styles.heatmapStat}>
                  <span className={styles.heatmapValue}>14</span>
                  <span className={styles.heatmapLabel}>Day Streak</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.revisionSection}>
          <h2 className={styles.sectionTitle}>Recommended for Revision</h2>
          <div className={styles.revisionGrid}>
            {recommendedRevision.map((item, i) => (
              <div key={i} className={styles.revisionCard}>
                <div className={styles.revisionContent}>
                  <h3 className={styles.revisionTitle}>{item.title}</h3>
                  <p className={styles.revisionNote}>{item.note}</p>
                </div>
                <Badge variant="outline-pill">Review</Badge>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
