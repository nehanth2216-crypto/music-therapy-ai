import React, { useState } from 'react';
import { ArrowRight, ArrowLeft, Loader2, Music, CheckCircle2, Activity, Heart, Moon } from 'lucide-react';

const GENRES = ["Melody", "Dance", "Pop", "Folk", "Rock", "Acoustic", "Ballad", "Classical", "Instrumental", "Lo-fi", "Nature Sounds"];
const MOODS = ["Happy", "Sad", "Calm", "Stressed", "Anxious", "Angry", "Energetic", "Romantic", "Bored", "Focused", "Relaxed", "Tired"];
const ACTIVITIES = ["Studying", "Working", "Workout", "Running", "Walking", "Driving", "Relaxing", "Meditation", "Sleeping", "Party", "Gaming", "Cooking"];
const ENERGIES = ["Low", "Medium", "High"];
const SLEEP_QUALITIES = ["Good", "Fair", "Poor"];
const GENDERS = ["Male", "Female", "Other", "Prefer not to say"];
const LANGUAGES = ["Telugu", "Tamil", "Hindi", "Malayalam", "English"];

export default function Survey({ token, apiBaseUrl, onViewChange, onSurveyComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Survey Inputs
  const [age, setAge] = useState(25);
  const [gender, setGender] = useState('Prefer not to say');
  const [mood, setMood] = useState('Calm');
  const [stress, setStress] = useState(5);
  const [sleepQuality, setSleepQuality] = useState('Good');
  const [anxiety, setAnxiety] = useState(5);
  const [favGenre, setFavGenre] = useState('Melody');
  const [languagePref, setLanguagePref] = useState('Telugu');
  const [activity, setActivity] = useState('Studying');
  const [energy, setEnergy] = useState('Low');
  const [modelName, setModelName] = useState('LightGBM');

  // Result State
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token && token.trim() !== '') {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${apiBaseUrl}/recommend/survey`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          age: parseInt(age) || 25,
          gender: gender,
          mood: mood,
          stress: parseInt(stress) || 5,
          sleep_quality: sleepQuality,
          anxiety: parseInt(anxiety) || 5,
          fav_genre: favGenre,
          language_pref: languagePref,
          activity: activity,
          energy: energy,
          model_name: modelName
        })
      });
      
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to submit survey');
      }
      
      setResult(data);
      setStep(3);

      // Instantly trigger playback of recommended music!
      if (onSurveyComplete && data.tracks && data.tracks.length > 0) {
        onSurveyComplete(data.tracks);
      }
    } catch (err) {
      console.error("Survey submission error:", err);
      const msg = (err.message === 'Failed to fetch' || err.name === 'TypeError')
        ? 'Unable to connect to backend server. Please run run.bat to start the backend on http://127.0.0.1:8000.'
        : (err.message || 'Failed to submit survey. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const getSymptomTag = (playlistName) => {
    const nameStr = (playlistName || "").toString();
    if (nameStr.includes("Classical")) {
      return { label: 'Deep Sleep & Relaxation Assist', color: 'var(--accent-cyan)' };
    } else if (nameStr.includes("Nature")) {
      return { label: 'Anxiety grounding / Mindfulness', color: 'var(--accent-emerald)' };
    } else if (nameStr.includes("Instrumental")) {
      return { label: 'Stress reduction / Calming focus', color: 'var(--primary)' };
    } else if (nameStr.includes("Pop")) {
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

            <div style={{ marginBottom: '1.75rem' }}>
              <label className="input-label" htmlFor="energy-input">Current Energy Level</label>
              <div style={{ display: 'flex', gap: '1rem' }} id="energy-input">
                {ENERGIES.map(lvl => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setEnergy(lvl)}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      borderRadius: '8px',
                      border: energy === lvl ? '2px solid var(--primary)' : '1px solid var(--border-glass)',
                      background: energy === lvl ? 'rgba(168, 85, 247, 0.15)' : 'rgba(0, 0, 0, 0.2)',
                      color: energy === lvl ? 'var(--text-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                      transition: 'var(--transition-fast)'
                    }}
                  >
                    {lvl === 'Low' && '🍃 Low Energy'}
                    {lvl === 'Medium' && '⚡ Medium Energy'}
                    {lvl === 'High' && '🔥 High Energy'}
                  </button>
                ))}
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

            <div style={{ marginBottom: '2rem' }}>
              <label className="input-label" htmlFor="model-select">AI Prediction Model</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem' }} id="model-select">
                {[
                  { id: 'LightGBM', name: 'LightGBM', badge: 'Champion (Fastest)' },
                  { id: 'CatBoost', name: 'CatBoost', badge: 'Categorical Pro' },
                  { id: 'Ensemble', name: 'Ensemble', badge: 'LightGBM + CatBoost' }
                ].map(m => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setModelName(m.id)}
                    style={{
                      padding: '0.65rem 0.75rem',
                      borderRadius: '10px',
                      border: modelName === m.id ? '2px solid var(--primary)' : '1px solid var(--border-glass)',
                      background: modelName === m.id ? 'rgba(99, 102, 241, 0.18)' : 'rgba(0, 0, 0, 0.25)',
                      color: modelName === m.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontWeight: 600,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.2rem',
                      transition: 'var(--transition-fast)'
                    }}
                  >
                    <span style={{ fontSize: '0.9rem' }}>{m.name}</span>
                    <span style={{ fontSize: '0.68rem', color: modelName === m.id ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>{m.badge}</span>
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
              Our trained {result.model_used || modelName} model has mapped your parameters to the best target soundscape.
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
              
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', justifyContent: 'center', marginTop: '1rem' }}>
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

                <span style={{
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: 'var(--primary)',
                  padding: '0.4rem 0.8rem',
                  borderRadius: '20px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: '1px solid rgba(99, 102, 241, 0.3)'
                }}>
                  ⚡ Model: {result.model_used || modelName}
                </span>

                <span style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: 'var(--accent-emerald)',
                  padding: '0.4rem 0.8rem',
                  borderRadius: '20px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  🎯 Confidence: {((result.prediction_confidence || 0.95) * 100).toFixed(1)}%
                </span>

                <span style={{
                  background: 'rgba(244, 63, 94, 0.15)',
                  color: 'var(--accent-rose)',
                  padding: '0.4rem 0.8rem',
                  borderRadius: '20px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: '1px solid rgba(244, 63, 94, 0.3)'
                }}>
                  🎵 {result.tracks?.length || 0} Spotify Tracks Ready
                </span>
              </div>
            </div>

            {/* Top Recommended Spotify Songs Preview */}
            {result.tracks && result.tracks.length > 0 && (
              <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>🎧</span> Top Matched Songs from Spotify:
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {result.tracks.slice(0, 3).map((trk, tIdx) => (
                    <div
                      key={tIdx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.75rem 1rem',
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '12px',
                        gap: '0.75rem'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-emerald)', minWidth: '20px' }}>
                          #{tIdx + 1}
                        </span>
                        {trk.album_image && (
                          <img
                            src={trk.album_image}
                            alt=""
                            style={{ width: '40px', height: '40px', borderRadius: '8px', objectFit: 'cover' }}
                          />
                        )}
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: '0.9rem', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {trk.song || trk.title}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {trk.artist || trk.artist_or_source} • {trk.language} • {trk.genre}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.15)', padding: '0.2rem 0.5rem', borderRadius: '12px' }}>
                          {trk.score || trk.match_score || 95}%
                        </span>
                        <a
                          href={trk.play_url || trk.spotify_url || `https://open.spotify.com/search/${encodeURIComponent((trk.song || trk.title) + ' ' + (trk.artist || ''))}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            padding: '0.35rem 0.65rem',
                            background: 'rgba(29, 185, 84, 0.15)',
                            border: '1px solid rgba(29, 185, 84, 0.4)',
                            color: '#1db954',
                            borderRadius: '8px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textDecoration: 'none'
                          }}
                          title="Open on Spotify"
                        >
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.503 17.308c-.218.358-.68.472-1.038.254-2.846-1.738-6.428-2.13-10.65-1.167-.406.094-.811-.16-.904-.567-.094-.407.16-.811.567-.905 4.622-1.055 8.583-.615 11.77 1.332.359.218.473.68.255 1.053zm1.468-3.264c-.274.444-.86.587-1.304.313-3.259-2.003-8.227-2.585-12.082-1.413-.497.151-1.026-.134-1.177-.631-.151-.497.134-1.026.631-1.177 4.412-1.341 9.889-.695 13.62 1.604.444.274.587.86.312 1.304zm.126-3.41c-3.908-2.321-10.354-2.535-14.086-1.402-.6.183-1.237-.16-1.42-.76-.183-.6.16-1.237.76-1.42 4.298-1.305 11.418-1.052 15.918 1.62.54.321.716 1.023.395 1.563-.321.54-1.023.716-1.567.4z"/>
                          </svg>
                          Spotify
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

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
