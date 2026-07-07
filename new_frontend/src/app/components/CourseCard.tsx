import React from 'react';
import Link from 'next/link';
import { FileText, ArrowRight, UploadCloud, BarChart2 } from 'lucide-react';
import Badge from './Badge';
import styles from './CourseCard.module.css';

export default function CourseCard({ course, variant = 'student' }) {
  if (variant === 'faculty') {
    return (
      <div className={`${styles.card} ${styles.facultyCard}`}>
        <div className={styles.header}>
          <div>
            <h3 className={styles.title}>{course.title}</h3>
            <p className={styles.meta}>{course.term} • {course.students} Students</p>
          </div>
          <Badge variant="solid" color="secondary">{course.status}</Badge>
        </div>
        <div className={styles.actions}>
          <Link href={`/faculty/course/${course.code}`} className={styles.ghostBtn}>
            <UploadCloud size={16} />
            <span>Upload Materials</span>
          </Link>
          <Link href={`/faculty/analytics`} className={styles.ghostBtn}>
            <BarChart2 size={16} />
            <span>View Analytics</span>
          </Link>
        </div>
      </div>
    );
  }

  // student variant
  return (
    <div className={styles.card}>
      <div className={styles.studentHeader}>
        <div className={`${styles.dot} ${styles[course.color]}`} />
        <h3 className={styles.title}>{course.title}</h3>
      </div>
      <p className={styles.description}>{course.description}</p>
      
      <div className={styles.footer}>
        <div className={styles.docCount}>
          <FileText size={16} className={styles.docIcon} />
          <span className={styles.docText}>{course.docCount} docs</span>
        </div>
        <Link href={`/student/courses/${course.id}`} className={styles.ghostBtn}>
          <span>Open</span>
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
