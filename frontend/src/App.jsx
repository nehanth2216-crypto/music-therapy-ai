import React, { useState, useEffect } from 'react';
import { ShieldCheck, LogOut, Disc, ClipboardList, BarChart3, User, Sparkles } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Survey from './components/Survey';
import ModelComparison from './components/ModelComparison';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000/api`;

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState(localStorage.getItem('username') || '');
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'survey', 'analytics'
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  
  // Auth Form State
  const [authUsername, setAuthUsername] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
    }
  }, [token, username]);

  const handleLogout = () => {
    setToken('');
    setUsername('');
    setAuthUsername('');
    setAuthEmail('');
    setAuthPassword('');
    setAuthError('');
    setAuthSuccess('');
    setCurrentView('dashboard');
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    
    const endpoint = authMode === 'signup' ? '/auth/signup' : '/auth/login';
    const body = authMode === 'signup' 
      ? { username: authUsername, email: authEmail, password: authPassword }
      : { username: authUsername, password: authPassword };
      
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      
      setToken(data.access_token);
      setUsername(data.username);
      setAuthSuccess('Welcome! Logged in successfully.');
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const renderAuthForm = () => {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '85vh',
        padding: '1.5rem'
      }}>
        <div className="glass-panel" style={{
          width: '100%',
          maxWidth: '450px',
          padding: '2.5rem',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Decorative Glow */}
          <div style={{
            position: 'absolute',
            top: '-50px',
            right: '-50px',
            width: '150px',
            height: '150px',
            background: 'var(--primary-glow)',
            filter: 'blur(40px)',
            borderRadius: '50%',
            pointerEvents: 'none'
          }} />
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', justifyContent: 'center' }}>
            <Disc className="spin" style={{ color: 'var(--primary)', width: '36px', height: '36px' }} />
            <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
              Harmony<span style={{ color: 'var(--primary)' }}>Rec</span>
            </h1>
          </div>
          
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.95rem' }}>
            AI-Curated Soundscapes for Mental Wellness
          </p>

          <form onSubmit={handleAuthSubmit}>
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="input-label" htmlFor="username-input">Username</label>
              <input 
                id="username-input"
                className="input-field" 
                type="text" 
                placeholder="Enter your username"
                value={authUsername}
                onChange={(e) => setAuthUsername(e.target.value)}
                required
              />
            </div>
            
            {authMode === 'signup' && (
              <div style={{ marginBottom: '1.25rem' }}>
                <label className="input-label" htmlFor="email-input">Email Address</label>
                <input 
                  id="email-input"
                  className="input-field" 
                  type="email" 
                  placeholder="name@example.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </div>
            )}
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="input-label" htmlFor="password-input">Password</label>
              <input 
                id="password-input"
                className="input-field" 
                type="password" 
                placeholder="••••••••"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                required
              />
            </div>

            {authError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--accent-rose)',
                color: 'var(--accent-rose)',
                padding: '0.75rem',
                borderRadius: '8px',
                marginBottom: '1.25rem',
                fontSize: '0.875rem'
              }}>
                {authError}
              </div>
            )}

            <button id="auth-submit-btn" className="btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center', padding: '0.9rem' }}>
              {authMode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>
              {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
            </span>
            <button 
              id="toggle-auth-btn"
              onClick={() => {
                setAuthMode(authMode === 'login' ? 'signup' : 'login');
                setAuthError('');
              }} 
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: 'var(--font-primary)'
              }}
            >
              {authMode === 'login' ? 'Sign Up' : 'Log In'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderActiveView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard token={token} apiBaseUrl={API_BASE_URL} onViewChange={setCurrentView} />;
      case 'survey':
        return <Survey token={token} apiBaseUrl={API_BASE_URL} onViewChange={setCurrentView} />;
      case 'analytics':
        return <ModelComparison token={token} apiBaseUrl={API_BASE_URL} />;
      default:
        return <Dashboard token={token} apiBaseUrl={API_BASE_URL} onViewChange={setCurrentView} />;
    }
  };

  if (!token) {
    return (
      <main style={{ minHeight: '100vh' }}>
        {renderAuthForm()}
      </main>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar Header */}
      <header className="glass-panel" style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        borderRadius: '0 0 16px 16px',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none',
        padding: '0.75rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(20, 16, 32, 0.75)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }} onClick={() => setCurrentView('dashboard')}>
          <Disc className="spin" style={{ color: 'var(--primary)', width: '28px', height: '28px' }} />
          <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.3px' }}>
            Harmony<span style={{ color: 'var(--primary)' }}>Rec</span>
          </span>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            id="nav-dashboard-btn"
            onClick={() => setCurrentView('dashboard')}
            className={currentView === 'dashboard' ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
          >
            <Sparkles style={{ width: '16px', height: '16px' }} />
            Dashboard
          </button>
          
          <button 
            id="nav-survey-btn"
            onClick={() => setCurrentView('survey')}
            className={currentView === 'survey' ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
          >
            <ClipboardList style={{ width: '16px', height: '16px' }} />
            Take Survey
          </button>
          
          <button 
            id="nav-analytics-btn"
            onClick={() => setCurrentView('analytics')}
            className={currentView === 'analytics' ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
          >
            <BarChart3 style={{ width: '16px', height: '16px' }} />
            ML Analytics
          </button>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <User style={{ width: '16px', height: '16px', color: 'var(--accent-cyan)' }} />
            <span>{username}</span>
          </div>
          
          <button 
            id="nav-logout-btn"
            onClick={handleLogout}
            className="btn-secondary"
            style={{
              padding: '0.5rem 0.75rem',
              fontSize: '0.85rem',
              borderColor: 'rgba(239, 68, 68, 0.2)',
              color: 'var(--accent-rose)'
            }}
          >
            <LogOut style={{ width: '14px', height: '14px' }} />
            Logout
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
        {renderActiveView()}
      </main>
      
      {/* Footer */}
      <footer style={{
        padding: '1.5rem 2rem',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.85rem',
        borderTop: '1px solid var(--border-glass)',
        marginTop: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.25rem', marginBottom: '0.25rem' }}>
          <ShieldCheck style={{ width: '14px', height: '14px', color: 'var(--accent-emerald)' }} />
          <span>HarmonyRec runs locally with calibrated clinical-grade model evaluations</span>
        </div>
        <p>© 2026 HarmonyRec. Tailored for emotional wellness.</p>
      </footer>
    </div>
  );
}
