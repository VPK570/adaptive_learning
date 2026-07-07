"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Wand2, Plus, Settings, FileText, ChevronDown } from 'lucide-react';
import AppShell from '@/app/components/AppShell';
import FormField from '@/app/components/FormField';
import CheckboxCard from '@/app/components/CheckboxCard';
import RemovableSection from '@/app/components/RemovableSection';
import PaperPreview from '@/app/components/PaperPreview';
import BloomPill from '@/app/components/BloomPill';
import { mockFacultyUser, generateSections, generatedPaper } from '@/lib/mockData';
import styles from './Generate.module.css';

export default function QuestionPaperGenerator() {
  const router = useRouter();
  const [step, setStep] = useState('configure'); // 'configure' | 'preview'
  const [courseName, setCourseName] = useState('CS401: Advanced Data Structures');
  const [duration, setDuration] = useState('180');
  const [totalMarks, setTotalMarks] = useState('100');
  const [bloomLevels, setBloomLevels] = useState({
    Remember: true,
    Understand: true,
    Apply: true,
    Analyze: false,
    Evaluate: false,
    Create: false,
  });
  const [sections, setSections] = useState(generateSections);

  const breadcrumbs = [
    { label: 'Dashboard', href: '/faculty/dashboard' },
    { label: 'Generate Paper' }
  ];

  const toggleBloom = (level) => {
    setBloomLevels(prev => ({ ...prev, [level]: !prev[level] }));
  };

  const removeSection = (id) => {
    setSections(prev => prev.filter(s => s.id !== id));
  };

  const handleGenerate = () => {
    setStep('preview');
  };

  // Flatten all questions for the preview component
  const allQuestions = generatedPaper.sections.flatMap(section =>
    section.questions.map(q => ({
      text: q.text,
      bloomTier: q.bloom[0],
      chunks: Math.floor(Math.random() * 8) + 2,
    }))
  );

  if (step === 'preview') {
    return (
      <AppShell
        navRole="faculty"
        activeNavKey="courses"
        topBarVariant="breadcrumbBack"
        breadcrumbs={[...breadcrumbs, { label: 'Preview' }]}
        onBack={() => setStep('configure')}
        user={mockFacultyUser}
      >
        <div className={styles.previewLayout}>
          <PaperPreview courseTitle={generatedPaper.title} questions={allQuestions} />
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
      user={mockFacultyUser}
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.titleBlock}>
            <h1 className={styles.pageTitle}>Question Paper Generator</h1>
            <p className={styles.pageSubtitle}>Configure parameters and let AI generate exam questions from your course materials.</p>
          </div>
        </header>

        <div className={styles.formLayout}>
          {/* Left: Configuration */}
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
                <h2 className={styles.sectionTitle}>
                  <FileText size={18} />
                  Sections
                </h2>
                <button className={styles.addBtn}>
                  <Plus size={16} />
                  Add Section
                </button>
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

            <button className={styles.generateBtn} onClick={handleGenerate}>
              <Wand2 size={18} />
              Generate Question Paper
            </button>
          </div>

          {/* Right: Live preview / summary */}
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
                  {Object.entries(bloomLevels)
                    .filter(([, v]) => v)
                    .map(([level]) => (
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
