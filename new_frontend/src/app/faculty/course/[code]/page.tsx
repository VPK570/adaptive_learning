"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle, FileText, ArrowRight, Upload } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import Dropzone from '@/app/components/Dropzone';
import FileTypeIcon from '@/app/components/FileTypeIcon';
import Badge from '@/app/components/Badge';
import ProgressBar from '@/app/components/ProgressBar';
import { ingestionApi } from '@/lib/api/ingestion';
import { coursesApi } from '@/lib/api/courses';
import styles from './UploadMaterials.module.css';

interface UploadFile {
  id: number;
  name: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  size: string;
  progress: number;
  result?: { chunks?: number; tokens?: number };
}

export default function UploadMaterials({ params }: { params: { code: string } }) {
  const router = useRouter();
  const courseCode = params.code || '';
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!courseCode) return;
    const controller = new AbortController();
    coursesApi.get(courseCode)
      .then(() => {})
      .catch(() => {});
    // ponytail: curriculum listing uses coursesApi.getTopics — doesn't return file names;
    // skip pre-populating file list for now, files appear after upload
    if (!controller.signal.aborted) setLoading(false);
    return () => controller.abort();
  }, [courseCode]);

  const handleDrop = useCallback((newFiles: File[]) => {
    newFiles.forEach((file) => {
      const fileId = Date.now() + Math.random();
      const newFile: UploadFile = {
        id: fileId,
        name: file.name,
        status: 'uploading',
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        progress: 0,
      };
      setFiles(prev => [...prev, newFile]);
      setSelectedFileId(fileId);

      ingestionApi.ingestPdf(
        file,
        courseCode,
        '',
        (pct) => {
          setFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, progress: pct } : f
          ));
        },
      )
        .then((result) => {
          setFiles(prev => prev.map(f =>
            f.id === fileId
              ? { ...f, status: 'ready', progress: 100, result: { chunks: result?.chunks || result?.total_chunks, tokens: result?.tokens } }
              : f
          ));
        })
        .catch(() => {
          setFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, status: 'error', progress: 0 } : f
          ));
        });
    });
  }, [courseCode]);

  const breadcrumbs = [
    { label: 'Dashboard', href: '/faculty/dashboard' },
    { label: courseCode }
  ];

  return (
    <AppShell
      navRole="faculty"
      activeNavKey="courses"
      topBarVariant="breadcrumbBack"
      breadcrumbs={breadcrumbs}
      onBack={() => router.back()}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.titleBlock}>
            <h1 className={styles.pageTitle}>Course Materials</h1>
            <p className={styles.pageSubtitle}>Upload and manage knowledge base documents for {courseCode}.</p>
          </div>
        </header>

        <div className={styles.layout}>
          <div className={styles.leftPanel}>
            <Dropzone onDrop={handleDrop} />

            <div className={styles.fileListSection}>
              <h3 className={styles.sectionTitle}>Uploaded Resources ({files.length})</h3>
              <div className={styles.fileList}>
                {files.map(file => (
                  <button
                    key={file.id}
                    className={`${styles.fileItem} ${selectedFileId === file.id ? styles.selectedFile : ''}`}
                    onClick={() => setSelectedFileId(file.id)}
                  >
                    <FileTypeIcon filename={file.name} isProcessing={file.status !== 'ready'} />
                    <div className={styles.fileMeta}>
                      <span className={styles.fileName}>{file.name}</span>
                      <span className={styles.fileSize}>{file.size}</span>
                    </div>
                    {file.status === 'ready' ? (
                      <Badge variant="solid" color="primary">Ready</Badge>
                    ) : file.status === 'error' ? (
                      <Badge variant="solid" color="danger">Failed</Badge>
                    ) : file.status === 'uploading' ? (
                      <Badge variant="pulse">{file.progress}%</Badge>
                    ) : (
                      <Badge variant="pulse">Processing</Badge>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className={styles.rightPanel}>
            {!selectedFile ? (
              <div className={styles.emptyState}>
                <Upload size={48} className={styles.emptyIcon} />
                <h3>Drop files to upload</h3>
                <p>Drag and drop PDF documents to add them to the knowledge base.</p>
              </div>
            ) : selectedFile.status === 'uploading' ? (
              <div className={styles.processingState}>
                <div className={styles.processingHeader}>
                  <FileTypeIcon filename={selectedFile.name} />
                  <div className={styles.processingMeta}>
                    <span className={styles.processingName}>{selectedFile.name}</span>
                    <span className={styles.processingStatusText}>Uploading...</span>
                  </div>
                </div>
                <div className={styles.progressSection}>
                  <ProgressBar percent={selectedFile.progress} showGradient />
                  <span className={styles.progressValue}>{selectedFile.progress}%</span>
                </div>
              </div>
            ) : selectedFile.status === 'error' ? (
              <div className={styles.readyCard}>
                <div className={styles.readyHeader}>
                  <FileText size={32} className={styles.emptyIcon} />
                  <h2>Upload Failed</h2>
                  <p>{selectedFile.name} could not be processed. Try again.</p>
                </div>
              </div>
            ) : (
              <div className={styles.readyCard}>
                <div className={styles.readyHeader}>
                  <CheckCircle size={32} className={styles.successIcon} />
                  <h2>Processing Complete</h2>
                  <p>{selectedFile.name} is now available in the knowledge base.</p>
                </div>
                <div className={styles.statsRow}>
                  <div className={styles.statMini}>
                    <span className={styles.statLabel}>Chunks</span>
                    <span className={styles.statValue}>{selectedFile.result?.chunks ?? '—'}</span>
                  </div>
                  <div className={styles.statMini}>
                    <span className={styles.statLabel}>Status</span>
                    <span className={styles.statValue}>Ready</span>
                  </div>
                </div>
                <div className={styles.actions}>
                  <button
                    className={styles.primaryBtn}
                    onClick={() => router.push('/faculty/generate')}
                  >
                    <span>Generate Question Paper</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
