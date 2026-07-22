"use client";

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Wand2, Plus, Settings, FileText, Loader } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import FormField from '@/app/components/FormField';
import CheckboxCard from '@/app/components/CheckboxCard';
import RemovableSection from '@/app/components/RemovableSection';
import PaperPreview from '@/app/components/PaperPreview';
import BloomPill from '@/app/components/BloomPill';
import { paperApi } from '@/lib/api/paper';
import type { GeneratedPaper, PaperQuestion } from '@/lib/api/types';
import styles from './Generate.module.css';

const BLOOM_LEVEL_MAP: Record<string, number> = {
  Remember: 1, Understand: 2, Apply: 3,
  Analyze: 4, Evaluate: 5, Create: 6,
};

const defaultSections = [
  { id: 'sec-1', title: 'Section A', questions: 5, marksPerQ: 2 },
  { id: 'sec-2', title: 'Section B', questions: 5, marksPerQ: 5 },
  { id: 'sec-3', title: 'Section C', questions: 3, marksPerQ: 10 },
];

export default function QuestionPaperGenerator() {
  const router = useRouter();
  const [step, setStep] = useState('configure');
  const [courseName, setCourseName] = useState('CS401: Advanced Data Structures');
  const [duration, setDuration] = useState('180');
  const [totalMarks, setTotalMarks] = useState('100');
  const [bloomLevels, setBloomLevels] = useState({
    Remember: true, Understand: true, Apply: true,
    Analyze: false, Evaluate: false, Create: false,
  });
  const [sections, setSections] = useState(defaultSections);
  const [paper, setPaper] = useState<GeneratedPaper | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const breadcrumbs = [
    { label: 'Dashboard', href: '/faculty/dashboard' },
    { label: 'Generate Paper' }
  ];

  const toggleBloom = (level: string) => {
    setBloomLevels(prev => ({ ...prev, [level]: !prev[level] }));
  };

  const removeSection = (id: string) => {
    setSections(prev => prev.filter(s => s.id !== id));
  };

  const difficultyFromBloom = useCallback(() => {
    const highChecked = [bloomLevels.Analyze, bloomLevels.Evaluate, bloomLevels.Create].filter(Boolean).length;
    if (highChecked >= 2) return 'Hard';
    if (highChecked === 0) return 'Easy';
    return 'Medium';
  }, [bloomLevels]);

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    setError('');
    try {
      const selectedLevels = Object.entries(bloomLevels)
        .filter(([, v]) => v)
        .map(([level]) => BLOOM_LEVEL_MAP[level])
        .filter((v): v is number => v !== undefined);
      const result = await paperApi.generate({
        course_code: courseName.split(':')[0].trim(),
        total_marks: parseInt(totalMarks) || 100,
        difficulty: difficultyFromBloom(),
        topics: sections.map(s => s.title),
        bloom_levels: selectedLevels.length > 0 ? selectedLevels : undefined,
      });
      setPaper(result);
      setStep('preview');
    } catch (e: any) {
      setError(e?.message || 'Failed to generate paper');
    } finally {
      setGenerating(false);
    }
  }, [courseName, totalMarks, difficultyFromBloom, sections]);

  const allQuestions: { text: string; bloomTier: string; chunks: number }[] =
    paper ? paper.sections.flatMap(s =>
      s.questions.map((q: PaperQuestion) => ({
        text: q.text,
        bloomTier: Array.isArray(q.bloom) ? q.bloom[0] : q.bloom || 'Remember',
        chunks: 0,
      }))
    ) : [];

  if (step === 'preview' && paper) {
    return (
      <AppShell
        navRole="faculty"
        activeNavKey="courses"
        topBarVariant="breadcrumbBack"
        breadcrumbs={[...breadcrumbs, { label: 'Preview' }]}
        onBack={() => setStep('configure')}
      >
        <div className={styles.previewLayout}>
          <PaperPreview courseTitle={paper.title} questions={allQuestions} />
        </div>
      </AppShell>
    );
  }

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
            <h1 className={styles.pageTitle}>Question Paper Generator</h1>
            <p className={styles.pageSubtitle}>Configure parameters and let AI generate exam questions from your course materials.</p>
          </div>
        </header>

        <div className={styles.formLayout}>
          <div className={styles.configPanel}>
            <section className={styles.formSection}>
              <h2 className={styles.sectionTitle}>
                <Settings size={18} />
                Paper Configuration
              </h2>
              <div className={styles.fieldGrid}>
                <FormField label="Course" value={courseName} onChange={(e) => setCourseName(e.target.value)} />
                <FormField label="Duration (mins)" type="number" value={duration} onChange={(e) => setDuration(e.target.value)} min="30" max="360" />
                <FormField label="Total Marks" type="number" value={totalMarks} onChange={(e) => setTotalMarks(e.target.value)} min="10" max="500" />
              </div>
            </section>

            <section className={styles.formSection}>
              <h2 className={styles.sectionTitle}>Bloom's Taxonomy Levels</h2>
              <div className={styles.bloomGrid}>
                {Object.entries(bloomLevels).map(([level, checked]) => (
                  <CheckboxCard
                    key={level}
                    label={level}
                    description={`Include ${level.toLowerCase()}-level questions`}
                    checked={checked}
                    onChange={() => toggleBloom(level)}
                    color="primary"
                  />
                ))}
              </div>
            </section>

            <section className={styles.formSection}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}><FileText size={18} /> Sections</h2>
                <button className={styles.addBtn}><Plus size={16} /> Add Section</button>
              </div>
              <div className={styles.sectionsList}>
                {sections.map(section => (
                  <RemovableSection key={section.id} title={section.title} onRemove={() => removeSection(section.id)}>
                    <div className={styles.sectionConfig}>
                      <span className={styles.sectionMeta}>{section.questions} questions × {section.marksPerQ} marks = {section.questions * section.marksPerQ} marks</span>
                    </div>
                  </RemovableSection>
                ))}
              </div>
            </section>

            <button className={styles.generateBtn} onClick={handleGenerate} disabled={generating}>
              {generating ? <Loader size={18} className={styles.spin} /> : <Wand2 size={18} />}
              {generating ? 'Generating...' : 'Generate Question Paper'}
            </button>
            {error && <p className={styles.error}>{error}</p>}
          </div>

          <div className={styles.previewPanel}>
            <div className={styles.summaryCard}>
              <h3 className={styles.summaryTitle}>Paper Summary</h3>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Course</span>
                <span className={styles.summaryValue}>{courseName}</span>
              </div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Duration</span>
                <span className={styles.summaryValue}>{duration} mins</span>
              </div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Total Marks</span>
                <span className={styles.summaryValue}>{totalMarks}</span>
              </div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Sections</span>
                <span className={styles.summaryValue}>{sections.length}</span>
              </div>
              <div className={styles.summaryDivider}></div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Bloom Levels</span>
                <div className={styles.bloomPills}>
                  {Object.entries(bloomLevels).filter(([, v]) => v).map(([level]) => (
                    <BloomPill key={level} tier={level} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
