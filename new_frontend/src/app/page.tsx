"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from "next/navigation";
import { GraduationCap, Mail, Lock, ArrowRight, Shield, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

export default function Home() {
  const [activeTab, setActiveTab] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({ email: '', password: '' });
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated, user, login: storeLogin } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && user) {
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get('redirect');
      if (redirect) { router.replace(redirect); return; }
      if (user.role === 'faculty') router.replace('/faculty/dashboard');
      else if (user.role === 'admin') router.replace('/admin/dashboard');
      else router.replace('/student/dashboard');
    }
  }, [isAuthenticated, user, router]);

  const tabs = ['Student', 'Faculty', 'Admin'];
  const roleMap = { Student: 'student', Faculty: 'faculty', Admin: 'admin' };

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({ email: '', password: '' });
    setServerError('');

    let isValid = true;
    const newErrors = { email: '', password: '' };

    if (!email.trim()) {
      newErrors.email = 'Email address is required.';
      isValid = false;
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address.';
      isValid = false;
    }

    if (!password) {
      newErrors.password = 'Password is required.';
      isValid = false;
    }

    if (!isValid) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);

    try {
      const selectedRole = roleMap[tabs[activeTab]];
      await storeLogin(email, password);

      const { user } = useAuthStore.getState();
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get('redirect');
      if (redirect) { router.push(redirect); return; }
      const redirectRole = user?.role || selectedRole;
      if (redirectRole === 'faculty') {
        router.push('/faculty/dashboard');
      } else if (redirectRole === 'admin') {
        router.push('/admin/dashboard');
      } else {
        router.push('/student/dashboard');
      }
    } catch (err) {
      setServerError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="glow-bg"></div>
      <main className="auth-card">
        <header className="auth-header">
          <div className="brand-logo" aria-hidden="true">
            <GraduationCap size={24} />
          </div>
          <h1 className="auth-title">Vbook LM</h1>
          <p className="auth-subtitle">University AI Platform</p>
        </header>

        <div className="role-tabs">
          <div 
            className="role-tab-slider" 
            style={{ transform: `translateX(${activeTab * 100}%)` }}
          ></div>
          {tabs.map((tab, index) => (
            <button 
              key={tab}
              className={`role-tab ${activeTab === index ? 'is-active' : ''}`} 
              type="button" 
              onClick={() => setActiveTab(index)}
            >
              {tab}
            </button>
          ))}
        </div>

        <form className="auth-form" noValidate onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">Institutional Email</label>
            <div className="input-wrapper">
              <span className="input-icon">
                <Mail size={18} />
              </span>
              <input 
                type="email" 
                id="email" 
                name="email" 
                autoComplete="email"
                className={`form-input ${errors.email ? 'is-invalid' : ''}`} 
                placeholder="name@university.edu"
                required 
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors({ ...errors, email: '' });
                }}
              />
            </div>
            {errors.email && <span className="form-error is-visible">{errors.email}</span>}
          </div>

          <div className="form-group">
            <div className="form-label-row">
              <label htmlFor="password" className="form-label">Password</label>
              <button type="button" className="auth-link" onClick={() => alert('Password reset coming soon.')} style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', fontSize: '12px' }}>Forgot?</button>
            </div>
            <div className="input-wrapper">
              <span className="input-icon">
                <Lock size={18} />
              </span>
              <input 
                type="password" 
                id="password" 
                name="password" 
                autoComplete="current-password"
                className={`form-input ${errors.password ? 'is-invalid' : ''}`} 
                placeholder="••••••••"
                required 
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors({ ...errors, password: '' });
                }}
              />
            </div>
            {errors.password && <span className="form-error is-visible">{errors.password}</span>}
          </div>

          {serverError && <div className="form-error is-visible" style={{ textAlign: 'center', marginBottom: '8px' }}>{serverError}</div>}

          <button 
            type="submit" 
            className={`btn btn-primary ${isLoading ? 'is-loading' : ''}`} 
            disabled={isLoading}
          >
            <span className="btn-text">Sign In</span>
            {!isLoading ? (
              <ArrowRight size={18} className="btn-icon" />
            ) : (
              <span className="btn-loader" aria-hidden="true">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 18V22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4.92993 4.93005L7.75993 7.76005" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16.24 16.24L19.07 19.07" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 12H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M18 12H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4.92993 19.07L7.75993 16.24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16.24 7.76005L19.07 4.93005" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
            )}
          </button>
        </form>

        <footer className="auth-footer">
          <p className="auth-footer-text">
            Don&apos;t have an account? <a href="/register" className="auth-link">Create an account</a>
          </p>
          <div className="trust-badge">
            <Shield size={12} />
            <span>Your data stays within your institution&apos;s infrastructure</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
