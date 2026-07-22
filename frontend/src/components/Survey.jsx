import React, { useState } from 'react';
import { ArrowRight, ArrowLeft, Loader2, Music, CheckCircle2, Activity, Heart, Moon } from 'lucide-react';

const GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"];
const MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"];
const ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation"];
const SLEEP_QUALITIES = ["Good", "Fair", "Poor"];
const LANGUAGES = [
  "English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam", "Punjabi", 
  "Bengali", "Marathi", "Gujarati", "Odia", "Assamese", "Urdu", "Sanskrit", 
  "Korean", "Japanese", "Chinese", "Spanish", "French", "German", "Italian", 
  "Arabic", "Turkish", "Portuguese", "Russian"
];

export default function Survey({ token, apiBaseUrl, onViewChange }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Survey Inputs
  const [age, setAge] = useState(25);
  const [gender, setGender] = useState('Prefer not to say');
  const [mood, setMood] = useState('Happy');
  const [stress, setStress] = useState(5);
  const [sleepQuality, setSleepQuality] = useState('Good');
  const [anxiety, setAnxiety] = useState(5);
  const [favGenre, setFavGenre] = useState('Lo-fi');
  const [languagePref, setLanguagePref] = useState('English');
  const [activity, setActivity] = useState('Relaxation');

  // Result State
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${apiBaseUrl}/recommend/survey`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          age: parseInt(age),
          gender: gender,
          mood: mood,
          stress: parseInt(stress),
          sleep_quality: sleepQuality,
          anxiety: parseInt(anxiety),
          fav_genre: favGenre,
          language_pref: languagePref,
          activity: activity
        })
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to submit survey');
      }
      
      setResult(data);
      setStep(3);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSymptomTag = (playlistName) => {
    if (playlistName.includes("Classical")) {
      return { label: 'Deep Sleep & Relaxation Assist', color: 'var(--accent-cyan)' };
    } else if (playlistName.includes("Nature")) {
      return { label: 'Anxiety grounding / Mindfulness', color: 'var(--accent-emerald)' };
    } else if (playlistName.includes("Instrumental")) {
      return { label: 'Stress reduction / Calming focus', color: 'var(--primary)' };
    } else if (playlistName.includes("Pop")) {
      return { label: 'Energy booster / Exhaustion recovery', color: 'var(--accent-rose)' };
    } else {
      return { label: 'Study focus / Balanced mood', color: 'var(--text-secondary)' };
    }
  };

  return (
    <div style={{ maxWidth: '700px', margin: '2rem auto' }}>
      <div className="glass-panel" style={{ padding: '2.5rem', position: 'relative' }}>
        
        {/* Progress Bar */}
        {step < 3 && (
          <div style={{ display: 'flex', gap: '8px', marginBottom: '2.5rem' }}>
            <div style={{
              flex: 1,
              height: '4px',
              borderRadius: '2px',
              background: step >= 1 ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
              boxShadow: step >= 1 ? '0 0 10px var(--primary)' : 'none',
              transition: 'var(--transition-smooth)'
            }} />
            <div style={{
              flex: 1,
              height: '4px',
              borderRadius: '2px',
              background: step >= 2 ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
              boxShadow: step >= 2 ? '0 0 10px var(--primary)' : 'none',
              transition: 'var(--transition-smooth)'
            }} />
          </div>
        )}

        {/* STEP 1: DEMOGRAPHICS & BASIC HABITS */}
        {step === 1 && (
          <div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Heart style={{ color: 'var(--accent-rose)' }} />
              Demographics & Basics
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Let's gather some basic demographics and favorite genres.
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label className="input-label" htmlFor="age-input">Age</label>
                <input 
                  id="age-input"
                  type="number" 
                  className="input-field" 
                  min="1" 
                  max="120" 
                  value={age} 
                  onChange={(e) => setAge(e.target.value)} 
                  required
                />
              </div>
              
              <div>
                <label className="input-label" htmlFor="gender-input">Gender (Optional)</label>
                <select 
                  id="gender-input"
                  className="input-field"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  style={{ appearance: 'none', background: 'rgba(0, 0, 0, 0.2) url("data:image/svg+xml;utf8,<svg fill=\'%23ffffff\' height=\'24\' viewBox=\'0 0 24 24\' width=\'24\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M7 10l5 5 5-5z\'/><path d=\'M0 0h24v24H0z\' fill=\'none\'/></svg>") no-repeat 95% center' }}
                >
                  {GENDERS.map(g => <option key={g} value={g} style={{ background: '#1c1830' }}>{g}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
              <div>
                <label className="input-label" htmlFor="fav-genre-input">Favorite Music Genre</label>
                <select 
                  id="fav-genre-input"
                  className="input-field" 
                  value={favGenre} 
                  onChange={(e) => setFavGenre(e.target.value)}
                  style={{ appearance: 'none', background: 'rgba(0, 0, 0, 0.2) url("data:image/svg+xml;utf8,<svg fill=\'%23ffffff\' height=\'24\' viewBox=\'0 0 24 24\' width=\'24\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M7 10l5 5 5-5z\'/><path d=\'M0 0h24v24H0z\' fill=\'none\'/></svg>") no-repeat 95% center' }}
                >
                  {GENRES.map(g => <option key={g} value={g} style={{ background: '#1c1830' }}>{g}</option>)}
                </select>
              </div>
              
              <div>
                <label className="input-label" htmlFor="language-input">Language Preference</label>
                <select 
                  id="language-input"
                  className="input-field"
                  value={languagePref}
                  onChange={(e) => setLanguagePref(e.target.value)}
                  style={{ appearance: 'none', background: 'rgba(0, 0, 0, 0.2) url("data:image/svg+xml;utf8,<svg fill=\'%23ffffff\' height=\'24\' viewBox=\'0 0 24 24\' width=\'24\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M7 10l5 5 5-5z\'/><path d=\'M0 0h24v24H0z\' fill=\'none\'/></svg>") no-repeat 95% center' }}
                >
                  {LANGUAGES.map(l => <option key={l} value={l} style={{ background: '#1c1830' }}>{l}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button id="next-step-btn" className="btn-primary" onClick={() => setStep(2)}>
                Next Details
                <ArrowRight style={{ width: '18px', height: '18px' }} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: PSYCHOLOGICAL SELF-REPORT */}
        {step === 2 && (
          <div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity style={{ color: 'var(--accent-cyan)' }} />
              Mood & Wellness Assessment
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Select your current mood, activity, and severity levels.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.75rem' }}>
              <div>
                <label className="input-label" htmlFor="mood-input">Current Mood</label>
                <select 
                  id="mood-input"
                  className="input-field" 
                  value={mood} 
                  onChange={(e) => setMood(e.target.value)}
                  style={{ appearance: 'none', background: 'rgba(0, 0, 0, 0.2) url("data:image/svg+xml;utf8,<svg fill=\'%23ffffff\' height=\'24\' viewBox=\'0 0 24 24\' width=\'24\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M7 10l5 5 5-5z\'/><path d=\'M0 0h24v24H0z\' fill=\'none\'/></svg>") no-repeat 95% center' }}
                >
                  {MOODS.map(m => <option key={m} value={m} style={{ background: '#1c1830' }}>{m}</option>)}
                </select>
              </div>

              <div>
                <label className="input-label" htmlFor="activity-input">Current Activity</label>
                <select 
                  id="activity-input"
                  className="input-field" 
                  value={activity} 
                  onChange={(e) => setActivity(e.target.value)}
                  style={{ appearance: 'none', background: 'rgba(0, 0, 0, 0.2) url("data:image/svg+xml;utf8,<svg fill=\'%23ffffff\' height=\'24\' viewBox=\'0 0 24 24\' width=\'24\' xmlns=\'http://www.w3.org/2000/svg\'><path d=\'M7 10l5 5 5-5z\'/><path d=\'M0 0h24v24H0z\' fill=\'none\'/></svg>") no-repeat 95% center' }}
                >
                  {ACTIVITIES.map(act => <option key={act} value={act} style={{ background: '#1c1830' }}>{act}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.75rem' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label className="input-label" htmlFor="stress-slider">Stress level (1–10)</label>
                  <span style={{ color: stress >= 7 ? 'var(--accent-rose)' : 'var(--primary)', fontWeight: 600 }}>{stress}/10</span>
                </div>
                <input 
                  id="stress-slider"
                  type="range" 
                  min="1" 
                  max="10" 
                  className="slider-custom"
                  value={stress} 
                  onChange={(e) => setStress(e.target.value)} 
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label className="input-label" htmlFor="anxiety-slider">Anxiety level (1–10)</label>
                  <span style={{ color: anxiety >= 7 ? 'var(--accent-rose)' : 'var(--accent-cyan)', fontWeight: 600 }}>{anxiety}/10</span>
                </div>
                <input 
                  id="anxiety-slider"
                  type="range" 
                  min="1" 
                  max="10" 
                  className="slider-custom"
                  value={anxiety} 
                  onChange={(e) => setAnxiety(e.target.value)} 
                />
              </div>
            </div>

            <div style={{ marginBottom: '2.5rem' }}>
              <label className="input-label" htmlFor="sleep-quality-input">Sleep Quality</label>
              <div style={{ display: 'flex', gap: '1rem' }} id="sleep-quality-input">
                {SLEEP_QUALITIES.map(sq => (
                  <button
                    key={sq}
                    type="button"
                    onClick={() => setSleepQuality(sq)}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      borderRadius: '8px',
                      border: sleepQuality === sq ? '2px solid var(--primary)' : '1px solid var(--border-glass)',
                      background: sleepQuality === sq ? 'rgba(168, 85, 247, 0.1)' : 'rgba(0, 0, 0, 0.2)',
                      color: sleepQuality === sq ? 'var(--text-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                      transition: 'var(--transition-fast)'
                    }}
                  >
                    {sq === 'Good' && '😊 '}
                    {sq === 'Fair' && '😐 '}
                    {sq === 'Poor' && '😴 '}
                    {sq}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--accent-rose)',
                color: 'var(--accent-rose)',
                padding: '0.75rem',
                borderRadius: '8px',
                marginBottom: '1.25rem',
                fontSize: '0.875rem'
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button className="btn-secondary" onClick={() => setStep(1)} disabled={loading}>
                <ArrowLeft style={{ width: '18px', height: '18px' }} />
                Back
              </button>
              
              <button id="submit-survey-btn" className="btn-primary" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="spin" style={{ width: '18px', height: '18px' }} />
                    Analyzing State...
                  </>
                ) : (
                  <>
                    Predict Best Music
                    <Music style={{ width: '18px', height: '18px' }} />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: RESULTS */}
        {step === 3 && result && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', padding: '1rem', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.1)', marginBottom: '1.5rem' }}>
              <CheckCircle2 style={{ width: '48px', height: '48px', color: 'var(--accent-emerald)' }} />
            </div>
            
            <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>AI recommendation generated!</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Our trained XGBoost model has mapped your parameters to the best target soundscape.
            </p>

            <div className="glass-card" style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: `1px solid ${getSymptomTag(result.result_state).color}`,
              padding: '2rem',
              borderRadius: '16px',
              marginBottom: '2rem',
              position: 'relative'
            }}>
              <span style={{
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                color: 'var(--text-muted)'
              }}>Tailored Playlist</span>
              
              <h3 style={{
                fontSize: '2.5rem',
                fontWeight: 800,
                color: getSymptomTag(result.result_state).color,
                margin: '0.5rem 0 1rem 0'
              }}>
                {result.result_state}
              </h3>
              
              <span style={{
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'var(--text-primary)',
                padding: '0.4rem 0.8rem',
                borderRadius: '20px',
                fontSize: '0.85rem',
                fontWeight: 600,
                border: '1px solid var(--border-glass)'
              }}>
                {getSymptomTag(result.result_state).label}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <button 
                id="view-playlist-btn"
                className="btn-primary" 
                onClick={() => onViewChange('dashboard')} 
                style={{ width: '100%', justifyContent: 'center' }}
              >
                Go to Dashboard Playlist
                <Music style={{ width: '18px', height: '18px' }} />
              </button>
              
              <button 
                id="retake-survey-btn"
                className="btn-secondary" 
                onClick={() => {
                  setResult(null);
                  setStep(1);
                }} 
                style={{ width: '100%', justifyContent: 'center' }}
              >
                Retake Assessment
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
