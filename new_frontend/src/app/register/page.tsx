"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.register(email, password, role);
      router.push('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="glow-bg"></div>
      <main className="auth-card">
        <header className="auth-header">
          <div className="brand-logo" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
              <path d="M6 12v5c3 3 9 3 12 0v-5"/>
            </svg>
          </div>
          <h1 className="auth-title">Create Account</h1>
          <p className="auth-subtitle">Join the Vbook LM platform</p>
        </header>

        <form className="auth-form" noValidate onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">Institutional Email</label>
            <div className="input-wrapper">
              <span className="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/>
                  <path d="M2 6l10 7 10-7"/>
                </svg>
              </span>
              <input
                type="email" id="email" name="email" className="form-input"
                placeholder="name@university.edu" required
                value={email} onChange={e => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="input-wrapper">
              <span className="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </span>
              <input
                type="password" id="password" name="password" className="form-input"
                placeholder="••••••••" required
                value={password} onChange={e => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="role" className="form-label">Role</label>
            <select
              id="role" value={role} onChange={e => setRole(e.target.value)}
              style={{
                width: '100%', padding: 'var(--space-3) var(--space-4)',
                borderRadius: 'var(--radius-md)', border: '1px solid var(--color-outline-variant)',
                background: 'var(--color-surface-container-low)', color: 'var(--color-on-surface)',
                font: 'inherit', fontSize: '0.9rem', outline: 'none',
              }}
            >
              <option value="student">Student</option>
              <option value="faculty">Faculty</option>
            </select>
          </div>

          {error && <div className="form-error is-visible" style={{ textAlign: 'center', marginBottom: '8px' }}>{error}</div>}

          <button type="submit" className={`btn btn-primary ${loading ? 'is-loading' : ''}`} disabled={loading}>
            <span className="btn-text">{loading ? 'Creating account...' : 'Create Account'}</span>
            {!loading && (
              <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            )}
          </button>
        </form>

        <footer className="auth-footer">
          <p className="auth-footer-text">
            Already have an account? <a href="/" className="auth-link">Sign in</a>
          </p>
        </footer>
      </main>
    </div>
  );
}
