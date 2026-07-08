"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UploadCloud, CheckCircle, FileText, ArrowRight } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import Dropzone from '@/app/components/Dropzone';
import FileTypeIcon from '@/app/components/FileTypeIcon';
import Badge from '@/app/components/Badge';
import ProgressBar from '@/app/components/ProgressBar';
import { mockFacultyUser } from '@/lib/mockData';
import styles from './UploadMaterials.module.css';

export default function UploadMaterials({ params }) {
  const router = useRouter();
  const courseCode = params.code || 'CS-301';
  
  const breadcrumbs = [
    { label: 'Dashboard', href: '/faculty/dashboard' },
    { label: courseCode }
  ];

  const [files, setFiles] = useState([
    { id: 1, name: 'Syllabus_Fall.pdf', status: 'ready', size: '2.4 MB' },
    { id: 2, name: 'Lecture_1_Intro.pdf', status: 'processing', size: '5.1 MB', progress: 45 },
  ]);

  const [selectedFileId, setSelectedFileId] = useState(2);

  const handleDrop = (newFiles) => {
    const addedFiles = newFiles.map((f, i) => ({
      id: Date.now() + i,
      name: f.name,
      status: 'processing',
      size: `${(f.size / (1024 * 1024)).toFixed(1)} MB`,
      progress: 0
    }));
    setFiles([...files, ...addedFiles]);
    setSelectedFileId(addedFiles[0].id);
  };

  const selectedFile = files.find(f => f.id === selectedFileId);

  return (
    <AppShell 
      navRole="faculty" 
      activeNavKey="courses" 
      topBarVariant="breadcrumbBack"
      breadcrumbs={breadcrumbs}
      onBack={() => router.back()}
      user={mockFacultyUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.titleBlock}>
            <h1 className={styles.pageTitle}>Course Materials</h1>
            <p className={styles.pageSubtitle}>Upload and manage knowledge base documents for {courseCode}.</p>
          </div>
        </header>

        <div className={styles.layout}>
          {/* Left Panel */}
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
                    <FileTypeIcon filename={file.name} isProcessing={file.status === 'processing'} />
                    <div className={styles.fileMeta}>
                      <span className={styles.fileName}>{file.name}</span>
                      <span className={styles.fileSize}>{file.size}</span>
                    </div>
                    {file.status === 'ready' ? (
                      <Badge variant="solid" color="primary">Ready</Badge>
                    ) : (
                      <Badge variant="pulse">Processing</Badge>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Panel */}
          <div className={styles.rightPanel}>
            {!selectedFile ? (
              <div className={styles.emptyState}>
                <FileText size={48} className={styles.emptyIcon} />
                <h3>Select a file</h3>
                <p>Choose a file from the left to view its processing status.</p>
              </div>
            ) : selectedFile.status === 'processing' ? (
              <div className={styles.processingState}>
                <div className={styles.processingHeader}>
                  <FileTypeIcon filename={selectedFile.name} />
                  <div className={styles.processingMeta}>
                    <span className={styles.processingName}>{selectedFile.name}</span>
                    <span className={styles.processingStatusText}>Extracting and vectorizing content...</span>
                  </div>
                </div>
                <div className={styles.progressSection}>
                  <ProgressBar percent={selectedFile.progress || 45} showGradient />
                  <span className={styles.progressValue}>{selectedFile.progress || 45}%</span>
                </div>
                <ul className={styles.processingSteps}>
                  <li className={styles.stepDone}>
                    <CheckCircle size={16} /> Text Extraction
                  </li>
                  <li className={styles.stepActive}>
                    <div className={styles.spinner}></div> Chunking
                  </li>
                  <li className={styles.stepPending}>
                    <div className={styles.circle}></div> Embedding Generation
                  </li>
                </ul>
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
                    <span className={styles.statValue}>142</span>
                  </div>
                  <div className={styles.statMini}>
                    <span className={styles.statLabel}>Tokens</span>
                    <span className={styles.statValue}>~45k</span>
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
