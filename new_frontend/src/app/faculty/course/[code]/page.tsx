"use client";

import React, { useState, useCallback, use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Upload, FileText, Trash2 } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import Dropzone from '@/app/components/Dropzone';
import Badge from '@/app/components/Badge';
import { ingestionApi } from '@/lib/api/ingestion';
import { coursesApi } from '@/lib/api/courses';
import { BookOpen, Layers } from 'lucide-react';
import styles from './UploadMaterials.module.css';

interface UploadFile {
  id: number;
  name: string;
  status: 'uploading' | 'processing' | 'error';
  size: string;
  progress: number;
}

export default function UploadMaterials({ params }: { params: Promise<{ code: string }> }) {
  const router = useRouter();
  const { code: courseCode } = use(params);
  const [uploadingFiles, setUploadingFiles] = useState<UploadFile[]>([]);
  const [deletingFilename, setDeletingFilename] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'materials' | 'curriculum'>('materials');

  const { data: course, isLoading } = useQuery({
    queryKey: ['course', courseCode],
    queryFn: () => coursesApi.get(courseCode),
    staleTime: 30_000,
  });

  const { data: topics = [] } = useQuery({
    queryKey: ['topics', courseCode],
    queryFn: () => coursesApi.getStructuredTopics(courseCode),
    staleTime: 30_000,
  });

  const handleDeleteDoc = useCallback(async (name: string) => {
    if (!confirm(`Delete "${name}"? This will remove all related chunks and embeddings.`)) return;
    setDeletingFilename(name);
    try {
      if (activeTab === 'materials') {
        await ingestionApi.deleteMaterial(courseCode, name);
      } else {
        await ingestionApi.deleteCurriculum(courseCode, name);
      }
    } catch {
      alert('Failed to delete document');
    } finally {
      setDeletingFilename(null);
    }
  }, [courseCode, activeTab]);

  const handleDrop = useCallback((newFiles: File[]) => {
    newFiles.forEach(file => {
      const fileId = Date.now() + Math.random();
      const entry: UploadFile = {
        id: fileId,
        name: file.name,
        status: 'uploading',
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        progress: 0,
      };
      setUploadingFiles(prev => [...prev, entry]);

      ingestionApi.ingestPdf(
        file,
        courseCode,
        '',
        pct => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, progress: pct } : f
          ));
        },
      )
        .then(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'processing', progress: 100 } : f
          ));
        })
        .catch(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        });
    });
  }, [courseCode]);

  const handleCurriculumDrop = useCallback((newFiles: File[]) => {
    newFiles.forEach(file => {
      const fileId = Date.now() + Math.random();
      const entry: UploadFile = {
        id: fileId,
        name: file.name,
        status: 'uploading',
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        progress: 0,
      };
      setUploadingFiles(prev => [...prev, entry]);

      ingestionApi.uploadCurriculum(
        file,
        courseCode,
        '',
        pct => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, progress: pct } : f
          ));
        },
      )
        .then(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'processing', progress: 100 } : f
          ));
        })
        .catch(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        });
    });
  }, [courseCode]);

  const tabs = [
    { key: 'materials', label: 'Materials' },
    { key: 'curriculum', label: 'Curriculum' },
  ];

  const statusVariant: Record<string, 'solid' | 'pulse'> = {
    uploading: 'pulse', processing: 'pulse', error: 'solid',
  };
  const statusColor: Record<string, string> = {
    uploading: 'primary', processing: 'primary', error: 'danger',
  };
  const statusLabel: Record<string, string> = {
    uploading: 'Uploading', processing: 'Processing...', error: 'Failed',
  };

  return (
    <AppShell
      navRole="faculty"
      activeNavKey="courses"
      topBarVariant="tabs"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tab: string) => setActiveTab(tab as 'materials' | 'curriculum')}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.pageTitle}>
            {activeTab === 'materials' ? 'Upload Materials' : 'Upload Curriculum'}
          </h1>
          <p className={styles.pageSubtitle}>
            {activeTab === 'materials'
              ? `Upload PDF reading materials for ${courseCode}. Files are automatically processed and indexed for the AI knowledge base.`
              : `Upload the curriculum/syllabus PDF for ${courseCode}. Topics will be extracted and used for scope detection and analytics.`}
          </p>
        </header>

        <div className={styles.layout}>
          <div className={styles.leftPanel}>
            <Dropzone onDrop={activeTab === 'materials' ? handleDrop : handleCurriculumDrop} />

            {uploadingFiles.length > 0 && (
              <div className={styles.uploadQueue}>
                <h3 className={styles.sectionTitle}>Upload Queue ({uploadingFiles.length})</h3>
                {uploadingFiles.map(f => (
                  <div key={f.id} className={styles.queueItem}>
                    <FileText size={24} style={{ color: 'var(--color-on-surface-variant)' }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span className={styles.queueItemName}>{f.name}</span>
                        <span className={styles.queueItemSize}>{f.size}</span>
                      </div>
                      <div className={styles.queueProgress}>
                        <div className={styles.queueProgressFill} style={{ width: `${f.progress}%` }} />
                      </div>
                    </div>
                    <Badge variant={statusVariant[f.status]} color={statusColor[f.status]}>
                      {f.status === 'uploading' ? `${f.progress}%` : statusLabel[f.status]}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className={styles.rightPanel}>
            <h3 className={styles.sectionTitle}>
              {activeTab === 'materials' ? 'Course Materials' : 'Curriculum Files'}
            </h3>
            {isLoading ? (
              <div className={styles.loadingContainer}>
                <div className={styles.spinner} />
              </div>
            ) : null}

            {activeTab === 'curriculum' && (
              <div style={{ marginTop: 'var(--space-6)' }}>
                <h3 className={styles.sectionTitle}>
                  <BookOpen size={18} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                  Extracted Topics
                </h3>
                {topics.length === 0 ? (
                  <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)', textAlign: 'center', padding: 'var(--space-4)' }}>
                    No topics extracted yet. Topics are extracted during curriculum processing.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                    {topics.map((topic, i) => (
                      <div key={i} className={styles.topicCard}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <span className={styles.topicName}>{topic.topic_name}</span>
                          <Badge variant="solid" color="secondary">{topic.bloom_level}</Badge>
                        </div>
                        {topic.subtopics?.length > 0 && (
                          <div style={{ font: 'var(--text-body-sm)', color: 'var(--color-on-surface-variant)', marginBottom: 4 }}>
                            <Layers size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                            {topic.subtopics.join(', ')}
                          </div>
                        )}
                        {topic.learning_objectives?.length > 0 && (
                          <ul style={{ margin: '4px 0 0', paddingLeft: 16, font: 'var(--text-body-sm)', color: 'var(--color-on-surface-variant)' }}>
                            {topic.learning_objectives.slice(0, 3).map((obj: string, j: number) => (
                              <li key={j}>{obj}</li>
                            ))}
                            {topic.learning_objectives.length > 3 && (
                              <li style={{ listStyle: 'none', fontStyle: 'italic' }}>+{topic.learning_objectives.length - 3} more</li>
                            )}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
