import React, { useState, useEffect } from 'react';
import { User, Lock, Save, X, CheckCircle, AlertCircle, Sparkles, Music, Shield } from 'lucide-react';

const GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"];
const LANGUAGES = ["English", "Spanish", "Hindi", "Other"];
const ACTIVITIES = ["Relaxation", "Studying", "Sleeping", "Meditation", "Exercise"];

export default function UserProfileModal({ isOpen, onClose, token, apiBaseUrl, onProfileUpdated }) {
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' or 'security'
  
  // Profile form state
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [favGenre, setFavGenre] = useState('Lo-fi');
  const [languagePref, setLanguagePref] = useState('English');
  const [defaultActivity, setDefaultActivity] = useState('Relaxation');
  const [createdAt, setCreatedAt] = useState('');

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Status feedback
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    if (isOpen && token) {
      fetchUserProfile();
    }
  }, [isOpen, token]);

  const fetchUserProfile = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBaseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error("Failed to load user profile");
      const data = await res.json();
      setUsername(data.username || '');
      setEmail(data.email || '');
      setFullName(data.full_name || '');
      setFavGenre(data.fav_genre || 'Lo-fi');
      setLanguagePref(data.language_pref || 'English');
      setDefaultActivity(data.default_activity || 'Relaxation');
      setCreatedAt(data.created_at || '');
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBaseUrl}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          fav_genre: favGenre,
          language_pref: languagePref,
          default_activity: defaultActivity
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update profile");
      
      setMessage({ type: 'success', text: 'Profile preferences updated successfully!' });
      if (onProfileUpdated) {
        onProfileUpdated(data);
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (newPassword.length < 6) {
      setMessage({ type: 'error', text: 'New password must be at least 6 characters' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBaseUrl}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Password update failed");

      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(10, 8, 20, 0.8)',
      backdropFilter: 'blur(12px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
        borderRadius: '24px',
        padding: '2rem',
        position: 'relative',
        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
        border: '1px solid var(--border-glass)'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-glass)',
            color: 'var(--text-secondary)',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
        >
          <X style={{ width: '18px', height: '18px' }} />
        </button>

        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{
            width: '46px',
            height: '46px',
            borderRadius: '16px',
            background: 'var(--primary-glow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid var(--border-glass)'
          }}>
            <User style={{ color: 'var(--primary)', width: '24px', height: '24px' }} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Account & Preferences</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Manage your personal details and soundscape preferences
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '1.5rem',
          background: 'rgba(0, 0, 0, 0.2)',
          padding: '0.25rem',
          borderRadius: '12px'
        }}>
          <button
            onClick={() => { setActiveTab('profile'); setMessage({ type: '', text: '' }); }}
            style={{
              flex: 1,
              padding: '0.6rem 1rem',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.88rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              background: activeTab === 'profile' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'profile' ? '#ffffff' : 'var(--text-secondary)',
              transition: 'all 0.2s ease'
            }}
          >
            <Sparkles style={{ width: '16px', height: '16px' }} />
            Profile & Music
          </button>
          
          <button
            onClick={() => { setActiveTab('security'); setMessage({ type: '', text: '' }); }}
            style={{
              flex: 1,
              padding: '0.6rem 1rem',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.88rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              background: activeTab === 'security' ? 'var(--primary)' : 'transparent',
              color: activeTab === 'security' ? '#ffffff' : 'var(--text-secondary)',
              transition: 'all 0.2s ease'
            }}
          >
            <Shield style={{ width: '16px', height: '16px' }} />
            Security & Password
          </button>
        </div>

        {/* Status Message */}
        {message.text && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
            background: message.type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: `1px solid ${message.type === 'error' ? 'var(--accent-rose)' : 'var(--accent-emerald)'}`,
            color: message.type === 'error' ? 'var(--accent-rose)' : 'var(--accent-emerald)'
          }}>
            {message.type === 'error' ? (
              <AlertCircle style={{ width: '16px', height: '16px', shrink: 0 }} />
            ) : (
              <CheckCircle style={{ width: '16px', height: '16px', shrink: 0 }} />
            )}
            <span>{message.text}</span>
          </div>
        )}

        {/* Tab 1: Profile & Preferences */}
        {activeTab === 'profile' && (
          <form onSubmit={handleProfileSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
              <div>
                <label className="input-label">Username</label>
                <input
                  className="input-field"
                  type="text"
                  value={username}
                  disabled
                  style={{ opacity: 0.65, cursor: 'not-allowed' }}
                />
              </div>
              <div>
                <label className="input-label">Full Name</label>
                <input
                  className="input-field"
                  type="text"
                  placeholder="e.g. Alex Johnson"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label className="input-label">Email Address</label>
              <input
                className="input-field"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
              <div>
                <label className="input-label">Preferred Music Genre</label>
                <select
                  className="input-field"
                  value={favGenre}
                  onChange={(e) => setFavGenre(e.target.value)}
                  style={{ appearance: 'none' }}
                >
                  {GENRES.map(g => (
                    <option key={g} value={g} style={{ background: '#1c1830' }}>{g}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="input-label">Default Activity</label>
                <select
                  className="input-field"
                  value={defaultActivity}
                  onChange={(e) => setDefaultActivity(e.target.value)}
                  style={{ appearance: 'none' }}
                >
                  {ACTIVITIES.map(a => (
                    <option key={a} value={a} style={{ background: '#1c1830' }}>{a}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label className="input-label">Preferred Language</label>
              <select
                className="input-field"
                value={languagePref}
                onChange={(e) => setLanguagePref(e.target.value)}
                style={{ appearance: 'none' }}
              >
                {LANGUAGES.map(l => (
                  <option key={l} value={l} style={{ background: '#1c1830' }}>{l}</option>
                ))}
              </select>
            </div>

            {createdAt && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '1.5rem' }}>
                Account created on: {createdAt}
              </p>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}
            >
              <Save style={{ width: '16px', height: '16px' }} />
              {loading ? 'Saving Changes...' : 'Save Preferences'}
            </button>
          </form>
        )}

        {/* Tab 2: Security & Password */}
        {activeTab === 'security' && (
          <form onSubmit={handlePasswordSubmit}>
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="input-label">Current Password</label>
              <input
                className="input-field"
                type="password"
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label className="input-label">New Password</label>
              <input
                className="input-field"
                type="password"
                placeholder="Minimum 6 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label className="input-label">Confirm New Password</label>
              <input
                className="input-field"
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}
            >
              <Lock style={{ width: '16px', height: '16px' }} />
              {loading ? 'Updating Password...' : 'Update Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
