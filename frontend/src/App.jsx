import React, { useState, useEffect } from 'react';
import { ShieldCheck, LogOut, Disc, ClipboardList, BarChart3, User, Sparkles, Key, CheckCircle, ArrowLeft, Settings, Shield } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Survey from './components/Survey';
import ModelComparison from './components/ModelComparison';
import UserProfileModal from './components/UserProfileModal';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000/api`;
const GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"];

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState(localStorage.getItem('username') || '');
  const [userProfile, setUserProfile] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'survey', 'analytics'
  const [authMode, setAuthMode] = useState('login'); // 'login', 'signup', 'forgot', 'reset'
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  
  // Auth Form State
  const [authUsername, setAuthUsername] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authFavGenre, setAuthFavGenre] = useState('Lo-fi');
  const [authPassword, setAuthPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');

  // Password Recovery State
  const [forgotInput, setForgotInput] = useState('');
  const [generatedResetToken, setGeneratedResetToken] = useState('');
  const [resetTokenInput, setResetTokenInput] = useState('');
  const [newPasswordInput, setNewPasswordInput] = useState('');

  // Verify session on mount and restore user details
  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
      verifySession(token);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      setUserProfile(null);
    }
  }, [token]);

  const verifySession = async (authToken) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (response.ok) {
        const profileData = await response.json();
        setUserProfile(profileData);
        setUsername(profileData.username);
      } else {
        // Token is invalid or expired
        handleLogout();
      }
    } catch (err) {
      // Backend unavailable or network issue; keep offline token state if needed
      console.warn("Could not verify session with backend:", err);
    }
  };

  const handleLogout = () => {
    setToken('');
    setUsername('');
    setUserProfile(null);
    setAuthUsername('');
    setAuthEmail('');
    setAuthFullName('');
    setAuthPassword('');
    setAuthError('');
    setAuthSuccess('');
    setCurrentView('dashboard');
    setIsProfileOpen(false);
    localStorage.removeItem('token');
    localStorage.removeItem('username');
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    
    if (authMode === 'login') {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: authUsername,
            password: authPassword,
            remember_me: rememberMe
          })
        });
        
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Authentication failed');
        }
        
        setToken(data.access_token);
        setUsername(data.username);
        setAuthSuccess('Welcome back! Logged in successfully.');
      } catch (err) {
        setAuthError(err.message);
      }
    } else if (authMode === 'signup') {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: authUsername,
            email: authEmail,
            password: authPassword,
            full_name: authFullName,
            fav_genre: authFavGenre
          })
        });
        
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Registration failed');
        }
        
        setToken(data.access_token);
        setUsername(data.username);
        setAuthSuccess('Account created successfully! Welcome to HarmonyRec.');
      } catch (err) {
        setAuthError(err.message);
      }
    }
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_or_username: forgotInput })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to process request');
      
      if (data.reset_token) {
        setGeneratedResetToken(data.reset_token);
        setResetTokenInput(data.reset_token);
        setAuthSuccess('Reset token generated! You can now reset your password below.');
      } else {
        setAuthSuccess(data.message);
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reset_token: resetTokenInput,
          new_password: newPasswordInput
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to reset password');

      setAuthSuccess('Password reset successfully! Please sign in with your new password.');
      setAuthMode('login');
      setAuthPassword(newPasswordInput);
      setGeneratedResetToken('');
      setResetTokenInput('');
      setNewPasswordInput('');
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
          maxWidth: '480px',
          padding: '2.5rem',
          position: 'relative',
          overflow: 'hidden',
          borderRadius: '24px'
        }}>
          {/* Decorative Glow */}
          <div style={{
            position: 'absolute',
            top: '-50px',
            right: '-50px',
            width: '180px',
            height: '180px',
            background: 'var(--primary-glow)',
            filter: 'blur(45px)',
            borderRadius: '50%',
            pointerEvents: 'none'
          }} />
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', justifyContent: 'center' }}>
            <Disc className="spin" style={{ color: 'var(--primary)', width: '38px', height: '38px' }} />
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
              Harmony<span style={{ color: 'var(--primary)' }}>Rec</span>
            </h1>
          </div>
          
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.92rem' }}>
            AI-Curated Music Therapy & Mental Wellness
          </p>

          {/* Forgot Password Flow */}
          {authMode === 'forgot' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <button
                  type="button"
                  onClick={() => { setAuthMode('login'); setAuthError(''); setAuthSuccess(''); }}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                >
                  <ArrowLeft style={{ width: '16px', height: '16px' }} /> Back to Sign In
                </button>
              </div>

              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Reset Your Password</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                Enter your registered email address or username to receive password reset instructions.
              </p>

              <form onSubmit={handleForgotSubmit}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label className="input-label" htmlFor="forgot-input">Email or Username</label>
                  <input
                    id="forgot-input"
                    className="input-field"
                    type="text"
                    placeholder="Enter email or username"
                    value={forgotInput}
                    onChange={(e) => setForgotInput(e.target.value)}
                    required
                  />
                </div>

                {authError && (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                    {authError}
                  </div>
                )}

                {authSuccess && (
                  <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-emerald)', color: 'var(--accent-emerald)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                    {authSuccess}
                  </div>
                )}

                <button className="btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}>
                  <Key style={{ width: '16px', height: '16px' }} />
                  Request Password Reset
                </button>
              </form>

              {generatedResetToken && (
                <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-glass)' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', marginBottom: '0.75rem', fontWeight: 600 }}>
                    Reset token generated for evaluation:
                  </p>
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.8rem', wordBreak: 'break-all', fontFamily: 'monospace', color: 'var(--primary)', marginBottom: '1rem' }}>
                    {generatedResetToken}
                  </div>
                  <button
                    onClick={() => { setAuthMode('reset'); setAuthError(''); setAuthSuccess(''); }}
                    className="btn-secondary"
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    Proceed to Reset Password
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Reset Password Form */}
          {authMode === 'reset' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                <button
                  type="button"
                  onClick={() => { setAuthMode('forgot'); setAuthError(''); setAuthSuccess(''); }}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                >
                  <ArrowLeft style={{ width: '16px', height: '16px' }} /> Back
                </button>
              </div>

              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Set New Password</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                Paste your reset token and enter your new password below.
              </p>

              <form onSubmit={handleResetSubmit}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <label className="input-label" htmlFor="reset-token-input">Reset Token</label>
                  <input
                    id="reset-token-input"
                    className="input-field"
                    type="text"
                    placeholder="Enter reset token"
                    value={resetTokenInput}
                    onChange={(e) => setResetTokenInput(e.target.value)}
                    required
                  />
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label className="input-label" htmlFor="new-password-input">New Password</label>
                  <input
                    id="new-password-input"
                    className="input-field"
                    type="password"
                    placeholder="Minimum 6 characters"
                    value={newPasswordInput}
                    onChange={(e) => setNewPasswordInput(e.target.value)}
                    required
                  />
                </div>

                {authError && (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-rose)', color: 'var(--accent-rose)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                    {authError}
                  </div>
                )}

                <button className="btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}>
                  Set New Password & Sign In
                </button>
              </form>
            </div>
          )}

          {/* Login or Signup Forms */}
          {(authMode === 'login' || authMode === 'signup') && (
            <form onSubmit={handleAuthSubmit}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label className="input-label" htmlFor="username-input">
                  {authMode === 'login' ? 'Username or Email' : 'Username'}
                </label>
                <input 
                  id="username-input"
                  className="input-field" 
                  type="text" 
                  placeholder={authMode === 'login' ? 'Enter username or email' : 'Choose a unique username'}
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                  required
                />
              </div>

              {authMode === 'signup' && (
                <>
                  <div style={{ marginBottom: '1.25rem' }}>
                    <label className="input-label" htmlFor="fullname-input">Full Name (Optional)</label>
                    <input 
                      id="fullname-input"
                      className="input-field" 
                      type="text" 
                      placeholder="e.g. Alex Johnson"
                      value={authFullName}
                      onChange={(e) => setAuthFullName(e.target.value)}
                    />
                  </div>

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

                  <div style={{ marginBottom: '1.25rem' }}>
                    <label className="input-label" htmlFor="genre-input">Preferred Music Style</label>
                    <select
                      id="genre-input"
                      className="input-field"
                      value={authFavGenre}
                      onChange={(e) => setAuthFavGenre(e.target.value)}
                      style={{ appearance: 'none' }}
                    >
                      {GENRES.map(g => (
                        <option key={g} value={g} style={{ background: '#1c1830' }}>{g}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}
              
              <div style={{ marginBottom: authMode === 'login' ? '1rem' : '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <label className="input-label" htmlFor="password-input" style={{ marginBottom: 0 }}>Password</label>
                  {authMode === 'login' && (
                    <button
                      type="button"
                      onClick={() => { setAuthMode('forgot'); setAuthError(''); setAuthSuccess(''); }}
                      style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
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

              {/* Remember Me Option */}
              {authMode === 'login' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
                  <input
                    id="remember-me-checkbox"
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    style={{ accentColor: 'var(--primary)', width: '16px', height: '16px', cursor: 'pointer' }}
                  />
                  <label htmlFor="remember-me-checkbox" style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }}>
                    Remember me on this device (30 days)
                  </label>
                </div>
              )}

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

              {authSuccess && (
                <div style={{
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid var(--accent-emerald)',
                  color: 'var(--accent-emerald)',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  marginBottom: '1.25rem',
                  fontSize: '0.875rem'
                }}>
                  {authSuccess}
                </div>
              )}

              <button id="auth-submit-btn" className="btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center', padding: '0.9rem' }}>
                {authMode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </form>
          )}

          {(authMode === 'login' || authMode === 'signup') && (
            <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>
                {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
              </span>
              <button 
                id="toggle-auth-btn"
                onClick={() => {
                  setAuthMode(authMode === 'login' ? 'signup' : 'login');
                  setAuthError('');
                  setAuthSuccess('');
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
          )}
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

        {/* User Badge & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <button 
            id="nav-user-profile-btn"
            onClick={() => setIsProfileOpen(true)}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-glass)',
              borderRadius: '20px',
              padding: '0.4rem 0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            title="Click to view & edit profile preferences"
          >
            <div style={{
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              background: 'var(--primary-glow)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--primary)'
            }}>
              <User style={{ width: '14px', height: '14px' }} />
            </div>
            <span style={{ fontWeight: 600 }}>{userProfile?.full_name || username}</span>
            <Settings style={{ width: '14px', height: '14px', color: 'var(--text-muted)' }} />
          </button>
          
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

      {/* User Profile & Settings Modal */}
      <UserProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        token={token}
        apiBaseUrl={API_BASE_URL}
        onProfileUpdated={(updated) => {
          setUserProfile(updated);
          if (updated.username) setUsername(updated.username);
        }}
      />
      
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
