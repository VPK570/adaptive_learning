"use client";

import React, { useState } from 'react';
import Modal from '@/app/components/Modal';
import FormField from '@/app/components/FormField';
import { coursesApi } from '@/lib/api/courses';

export default function AddCourseModal({ isOpen, onClose, onSuccess }) {
  const [courseCode, setCourseCode] = useState('');
  const [courseName, setCourseName] = useState('');
  const [description, setDescription] = useState('');
  const [icon, setIcon] = useState('📚');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async e => {
    e.preventDefault();
    if (!courseCode.trim() || !courseName.trim() || !description.trim()) {
      setError('Course Code, Name, and Description are required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await coursesApi.create({
        course_code: courseCode.trim().toUpperCase(),
        course_name: courseName.trim(),
        description: description.trim(),
        icon: icon || '📚',
      });
      setCourseCode('');
      setCourseName('');
      setDescription('');
      setIcon('📚');
      onSuccess();
      onClose();
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to create course');
    } finally {
      setSaving(false);
    }
  };

  const footer = (
    <>
      <button
        onClick={onClose}
        style={{
          padding: '10px 20px', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-outline-variant)', background: 'transparent',
          color: 'var(--color-on-surface-variant)', font: 'var(--text-label-md)',
          cursor: 'pointer',
        }}
      >
        Cancel
      </button>
      <button
        onClick={handleSubmit}
        disabled={saving}
        style={{
          padding: '10px 20px', borderRadius: 'var(--radius-md)',
          border: 'none', background: 'var(--color-primary)',
          color: 'var(--color-on-primary)', font: 'var(--text-label-md)',
          cursor: 'pointer', opacity: saving ? 0.6 : 1,
        }}
      >
        {saving ? 'Creating...' : 'Create Course'}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Course" footer={footer}>
      {error && (
        <p style={{ color: 'var(--color-error)', font: 'var(--text-body-md)', margin: 0 }}>{error}</p>
      )}
      <FormField label="Course Code *" value={courseCode} onChange={e => setCourseCode(e.target.value)} placeholder="e.g. CS101" min={undefined} max={undefined} />
      <FormField label="Course Name *" value={courseName} onChange={e => setCourseName(e.target.value)} placeholder="e.g. Introduction to Computer Science" min={undefined} max={undefined} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <label style={{ font: 'var(--text-label-md)', color: 'var(--color-on-surface-variant)', textTransform: 'uppercase' }}>Description *</label>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Describe the course content and objectives..."
          rows={3}
          style={{
            width: '100%', background: 'var(--color-surface-container)',
            border: '1px solid var(--color-outline-variant)', borderRadius: 'var(--radius-md)',
            padding: '12px 16px', color: 'var(--color-on-background)', font: 'var(--text-body-md)',
            outline: 'none', resize: 'vertical', minHeight: 80,
          }}
          onFocus={e => { e.target.style.borderColor = 'var(--color-primary)'; e.target.style.background = 'var(--color-surface-container-high)'; }}
          onBlur={e => { e.target.style.borderColor = 'var(--color-outline-variant)'; e.target.style.background = 'var(--color-surface-container)'; }}
        />
      </div>
      <FormField label="Icon (optional)" value={icon} onChange={e => setIcon(e.target.value)} placeholder="📚" min={undefined} max={undefined} />
    </Modal>
  );
}
