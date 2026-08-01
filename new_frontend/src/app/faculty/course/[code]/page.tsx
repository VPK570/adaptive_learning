"use client";

import React, { useState, useCallback, use } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
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
  taskId?: string;
}

interface TopicAnalysis {
  topics: { topic_name: string; chunk_count: number; coverage_pct: number; page_min: number; page_max: number; depth: string }[];
  module_coverage: { module: string; topics_total: number; topics_covered: number; coverage_pct: number }[];
  extra_topics: { name: string; page_range: number[]; description: string }[];
  total_chunks: number;
  uncategorized_chunks: number;
}

export default function UploadMaterials({ params }: { params: Promise<{ code: string }> }) {
  const router = useRouter();
  const { code: courseCode } = use(params);
  const [uploadingFiles, setUploadingFiles] = useState<UploadFile[]>([]);
  const [deletingFilename, setDeletingFilename] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'materials' | 'curriculum'>('materials');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [topicAnalysis, setTopicAnalysis] = useState<TopicAnalysis | null>(null);
  const [analysisDocId, setAnalysisDocId] = useState<number | null>(null);

  const queryClient = useQueryClient();

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

  const { data: stats } = useQuery({
    queryKey: ['stats', courseCode],
    queryFn: () => coursesApi.getStats(courseCode),
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
      queryClient.invalidateQueries({ queryKey: ['stats', courseCode] });
      queryClient.invalidateQueries({ queryKey: ['topics', courseCode] });
    } catch {
      alert('Failed to delete document');
    } finally {
      setDeletingFilename(null);
    }
  }, [courseCode, activeTab, queryClient]);

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
        selectedTopic,
        pct => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, progress: pct } : f
          ));
        },
      )
        .then((data: { task_id: string; status: string }) => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'processing', progress: 100, taskId: data.task_id } : f
          ));
          queryClient.invalidateQueries({ queryKey: ['stats', courseCode] });
          // Poll for task completion
          const poll = setInterval(async () => {
            try {
              const result = await ingestionApi.pollTask(data.task_id);
              if (result.status === 'SUCCESS' && result.result?.topic_analysis) {
                clearInterval(poll);
                setTopicAnalysis(result.result.topic_analysis);
                setAnalysisDocId(fileId);
              } else if (result.status === 'FAILURE') {
                clearInterval(poll);
              }
            } catch {
              clearInterval(poll);
            }
          }, 2000);
        })
        .catch(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        });
    });
  }, [courseCode, queryClient, selectedTopic]);

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
        selectedTopic,
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
          queryClient.invalidateQueries({ queryKey: ['stats', courseCode] });
          queryClient.invalidateQueries({ queryKey: ['topics', courseCode] });
        })
        .catch(() => {
          setUploadingFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        });
    });
  }, [courseCode, queryClient, selectedTopic]);

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
            {topics.length > 0 ? (
              <div style={{ marginBottom: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <label style={{ font: 'var(--text-label-md)', color: 'var(--color-on-surface-variant)', whiteSpace: 'nowrap' }}>
                  Topic:
                </label>
                <select
                  value={selectedTopic}
                  onChange={e => setSelectedTopic(e.target.value)}
                  style={{
                    flex: 1, padding: 'var(--space-2) var(--space-3)',
                    font: 'var(--text-body-md)',
                    background: 'var(--color-surface-container-high)',
                    color: 'var(--color-on-surface)',
                    border: '1px solid var(--color-outline-variant)',
                    borderRadius: 8,
                  }}
                >
                  <option value="">-- Auto-detect / General --</option>
                  {topics.map(t => (
                    <option key={t.topic_name} value={t.topic_name}>{t.topic_name}</option>
                  ))}
                </select>
              </div>
            ) : (
              <div style={{ marginBottom: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--color-surface-container-high)', borderRadius: 8, font: 'var(--text-body-sm)', color: 'var(--color-on-surface-variant)', textAlign: 'center' }}>
                Upload a curriculum PDF to enable topic tagging for materials.
              </div>
            )}
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

            {activeTab === 'materials' && (
              <>
                <div className={styles.docList}>
                  {stats?.documents?.length > 0 ? (
                    stats.documents.map((doc, i) => (
                      <div key={i} className={styles.docItem}>
                        <div className={styles.docIcon}>
                          <FileText size={20} />
                        </div>
                        <div className={styles.docInfo}>
                          <span className={styles.docName}>{doc.name}</span>
                        </div>
                        <button
                          className={styles.deleteBtn}
                          onClick={() => handleDeleteDoc(doc.name)}
                          disabled={deletingFilename === doc.name}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className={styles.emptyDocs}>
                      <p style={{ font: 'var(--text-body-md)', color: 'var(--color-on-surface-variant)', textAlign: 'center' }}>
                        No materials uploaded yet.
                      </p>
                    </div>
                  )}
                </div>
                {topicAnalysis && analysisDocId && (
                  <div style={{ marginTop: 'var(--space-6)' }}>
                    <h3 className={styles.sectionTitle}>Topic Analysis</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      {topicAnalysis.topics.map((t, i) => (
                        <div key={i} className={styles.topicCard}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                            <span className={styles.topicName}>{t.topic_name}</span>
                            <span style={{ font: 'var(--text-body-sm)', color: 'var(--color-on-surface-variant)' }}>{t.coverage_pct}%</span>
                          </div>
                          <div style={{ height: 8, background: 'var(--color-surface-container-high)', borderRadius: 4, overflow: 'hidden', marginBottom: 4 }}>
                            <div style={{ height: '100%', width: `${Math.min(t.coverage_pct, 100)}%`, background: 'var(--color-primary)', borderRadius: 4, transition: 'width 0.3s' }} />
                          </div>
                          <div style={{ display: 'flex', gap: 'var(--space-3)', font: 'var(--text-body-sm)', color: 'var(--color-on-surface-variant)' }}>
                            <span>p.{t.page_min}-{t.page_max}</span>
                            <span>{t.depth}</span>
                            <span>{t.chunk_count} chunks</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    {topicAnalysis.module_coverage?.length > 0 && (
                      <div style={{ marginTop: 'var(--space-4)' }}>
                        <h4 style={{ font: 'var(--text-label-md)', marginBottom: 'var(--space-2)' }}>Module Coverage</h4>
                        {topicAnalysis.module_coverage.map((m, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', font: 'var(--text-body-sm)', padding: 'var(--space-1) 0' }}>
                            <span>{m.module}</span>
                            <span>{m.topics_covered}/{m.topics_total} topics ({m.coverage_pct}%)</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {topicAnalysis.extra_topics?.length > 0 && (
                      <div style={{ marginTop: 'var(--space-4)' }}>
                        <h4 style={{ font: 'var(--text-label-md)', marginBottom: 'var(--space-2)' }}>Extra Topics Found</h4>
                        {topicAnalysis.extra_topics.map((e, i) => (
                          <div key={i} style={{ font: 'var(--text-body-sm)', padding: 'var(--space-1) 0' }}>
                            {e.name} (p.{e.page_range[0]}-{e.page_range[1]})
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {activeTab === 'curriculum' && (
              <>
                {stats?.curriculum_docs?.length > 0 && (
                  <div className={styles.docList} style={{ marginBottom: 'var(--space-6)' }}>
                    {stats.curriculum_docs.map((doc, i) => (
                      <div key={i} className={styles.docItem}>
                        <div className={styles.docIcon}>
                          <FileText size={20} />
                        </div>
                        <div className={styles.docInfo}>
                          <span className={styles.docName}>{doc.name}</span>
                        </div>
                        <button
                          className={styles.deleteBtn}
                          onClick={() => handleDeleteDoc(doc.name)}
                          disabled={deletingFilename === doc.name}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
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
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
