"use client";

import React, { useState } from 'react';

export default function Home() {
  const [activeTab, setActiveTab] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({ email: '', password: '' });
  const [isLoading, setIsLoading] = useState(false);

  const tabs = ['Student', 'Faculty', 'Admin'];

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({ email: '', password: '' });

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
      // Fake network request
      await new Promise((resolve) => setTimeout(resolve, 1500));
      console.log(`Login intent registered successfully for role: ${tabs[activeTab]}`);
    } catch (err) {
      console.error(err);
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
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
              <path d="M6 12v5c3 3 9 3 12 0v-5"/>
            </svg>
          </div>
          <h1 className="auth-title">UniAI</h1>
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
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/>
                  <path d="M2 6l10 7 10-7"/>
                </svg>
              </span>
              <input 
                type="email" 
                id="email" 
                name="email" 
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
              <a href="#" className="auth-link">Forgot?</a>
            </div>
            <div className="input-wrapper">
              <span className="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </span>
              <input 
                type="password" 
                id="password" 
                name="password" 
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

          <button 
            type="submit" 
            className={`btn btn-primary ${isLoading ? 'is-loading' : ''}`} 
            disabled={isLoading}
          >
            <span className="btn-text">Sign In</span>
            {!isLoading ? (
              <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
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
            Don't have an account? <a href="#" className="auth-link">Create an account</a>
          </p>
          <div className="trust-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="M12 8v4"/>
              <path d="M12 16h.01"/>
            </svg>
            <span>Your data stays within your institution's infrastructure</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
