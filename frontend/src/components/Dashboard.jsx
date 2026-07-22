import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, Volume2, Music, Calendar, Clock, Smile, Sparkles, ClipboardList, AlertCircle, Disc, Heart, Star, Send, HeartHandshake, Bell, BookOpen, VolumeX } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"];

export default function Dashboard({ token, apiBaseUrl, onViewChange }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Audio Player State
  const [currentTracks, setCurrentTracks] = useState([]);
  const [activeTrackIndex, setActiveTrackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [currentMoodState, setCurrentMoodState] = useState('None');
  const [latestSurveyId, setLatestSurveyId] = useState(null);
  
  // Favorite tracks
  const [favorites, setFavorites] = useState([]);
  
  // Rating & Feedback State
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [helped, setHelped] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  // Daily Journal State
  const [journals, setJournals] = useState([]);
  const [journalMood, setJournalMood] = useState('Happy');
  const [journalStress, setJournalStress] = useState(5);
  const [journalText, setJournalText] = useState('');
  const [journalSuccess, setJournalSuccess] = useState('');

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([
    { sender: 'bot', text: 'Hi! I am your AI Wellness Companion. Let me know if you need breathing exercises, stress tips, study advice, or music suggestions!' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Break Timer State
  const [timerActive, setTimerActive] = useState(false);
  const [timerMinutes, setTimerMinutes] = useState(20);
  const [timerSecondsLeft, setTimerSecondsLeft] = useState(1200);
  const [timerInstance, setTimerInstance] = useState(null);
  const [timerAlert, setTimerAlert] = useState(false);

  // Grounding breathing visualizer state
  const [breathingState, setBreathingState] = useState('Idle'); // 'Idle', 'Inhale', 'Hold', 'Exhale'
  const [breathingSecs, setBreathingSecs] = useState(4);
  const [breathingActive, setBreathingActive] = useState(false);

  const audioRef = useRef(null);

  const fetchDashboardData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch history, favorites, and journals concurrently
      const [resHistory, resFavs, resJournals] = await Promise.all([
        fetch(`${apiBaseUrl}/recommend/history`, { method: 'GET', headers }),
        fetch(`${apiBaseUrl}/favorites`, { method: 'GET', headers }),
        fetch(`${apiBaseUrl}/journal`, { method: 'GET', headers })
      ]);

      // Parse JSON responses concurrently
      const [historyData, favsData, journalData] = await Promise.all([
        resHistory.ok ? resHistory.json() : Promise.resolve([]),
        resFavs.ok ? resFavs.json() : Promise.resolve([]),
        resJournals.ok ? resJournals.json() : Promise.resolve([])
      ]);

      if (resHistory.ok) {
        setHistory(historyData);
        if (historyData.length > 0) {
          const latest = historyData[historyData.length - 1];
          setCurrentTracks(latest.tracks || []);
          setCurrentMoodState(latest.result_state || 'Calming');
          setLatestSurveyId(latest.id);
          // Set feedback default if already submitted
          setRating(latest.rating || 0);
          setHelped(latest.helped);
        }
      }

      if (resFavs.ok) {
        setFavorites(favsData);
      }

      if (resJournals.ok) {
        setJournals(journalData);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // HTML5 Audio playback logic
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying && currentTracks.length > 0 && currentTracks[activeTrackIndex]?.preview_url) {
        audioRef.current.play().catch(() => setIsPlaying(false));
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, activeTrackIndex, currentTracks]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  // Break Timer loop
  useEffect(() => {
    if (timerActive && timerSecondsLeft > 0) {
      const interval = setInterval(() => {
        setTimerSecondsLeft(prev => prev - 1);
      }, 1000);
      return () => clearInterval(interval);
    } else if (timerActive && timerSecondsLeft === 0) {
      setTimerActive(false);
      setTimerAlert(true);
      if (Notification.permission === "granted") {
        new Notification("Break Time!", { body: "Time to take a 5-minute relaxation break! Listen to some soothing classical sounds.", icon: "/favicon.svg" });
      } else {
        alert("🚨 Relaxation Break! Time to stretch, take deep breaths, and let classical music calm your mind.");
      }
    }
  }, [timerActive, timerSecondsLeft]);

  // Grounding breathing loops
  useEffect(() => {
    let timer;
    if (breathingActive) {
      if (breathingSecs > 0) {
        timer = setTimeout(() => setBreathingSecs(prev => prev - 1), 1000);
      } else {
        // Transition breathing state: Inhale (4s) -> Hold (4s) -> Exhale (4s) -> Repeat
        if (breathingState === 'Inhale') {
          setBreathingState('Hold');
          setBreathingSecs(4);
        } else if (breathingState === 'Hold') {
          setBreathingState('Exhale');
          setBreathingSecs(4);
        } else {
          setBreathingState('Inhale');
          setBreathingSecs(4);
        }
      }
    }
    return () => clearTimeout(timer);
  }, [breathingActive, breathingSecs, breathingState]);

  const activeTrack = currentTracks[activeTrackIndex];

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const recordTrackPlay = (track) => {
    if (!track || !token) return;
    fetch(`${apiBaseUrl}/music/history`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: track.title,
        artist: track.artist,
        duration: track.duration,
        album_image: track.album_image,
        play_url: track.play_url,
        preview_url: track.preview_url
      })
    }).catch(() => {});
  };

  const handlePlayPause = (index) => {
    if (index !== undefined) {
      if (index === activeTrackIndex) {
        const nextState = !isPlaying;
        setIsPlaying(nextState);
        if (nextState && currentTracks[index]) {
          recordTrackPlay(currentTracks[index]);
        }
      } else {
        setActiveTrackIndex(index);
        setIsPlaying(true);
        if (currentTracks[index]) {
          recordTrackPlay(currentTracks[index]);
        }
      }
    } else {
      const nextState = !isPlaying;
      setIsPlaying(nextState);
      if (nextState && currentTracks[activeTrackIndex]) {
        recordTrackPlay(currentTracks[activeTrackIndex]);
      }
    }
  };

  const handleNextTrack = () => {
    if (currentTracks.length === 0) return;
    const nextIndex = (activeTrackIndex + 1) % currentTracks.length;
    setActiveTrackIndex(nextIndex);
    setCurrentTime(0);
    setIsPlaying(true);
    if (currentTracks[nextIndex]) {
      recordTrackPlay(currentTracks[nextIndex]);
    }
  };

  const handlePrevTrack = () => {
    if (currentTracks.length === 0) return;
    setActiveTrackIndex((prev) => (prev - 1 + currentTracks.length) % currentTracks.length);
    setCurrentTime(0);
    setIsPlaying(true);
  };

  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const toggleFavorite = async (track) => {
    try {
      const res = await fetch(`${apiBaseUrl}/favorites/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: track.title,
          artist: track.artist,
          duration: track.duration,
          album_image: track.album_image,
          play_url: track.play_url,
          preview_url: track.preview_url
        })
      });
      if (res.ok) {
        // Refresh local favorites
        const resFavs = await fetch(`${apiBaseUrl}/favorites`, {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resFavs.ok) {
          const favsData = await resFavs.json();
          setFavorites(favsData);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const isFavorite = (track) => {
    return favorites.some(f => f.title === track.title && f.artist === track.artist);
  };

  // Submit User Feedback
  const submitFeedback = async (score, helpVal) => {
    if (!latestSurveyId) return;
    try {
      const response = await fetch(`${apiBaseUrl}/recommend/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          survey_id: latestSurveyId,
          rating: score,
          helped: helpVal !== null ? helpVal : helped === true
        })
      });
      if (response.ok) {
        setRating(score);
        if (helpVal !== null) setHelped(helpVal);
        setFeedbackSuccess('Feedback submitted. Thank you!');
        setTimeout(() => setFeedbackSuccess(''), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Submit Daily Journal Entry
  const handleJournalSubmit = async (e) => {
    e.preventDefault();
    if (!journalText.trim()) return;
    try {
      const res = await fetch(`${apiBaseUrl}/journal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          mood: journalMood,
          stress: parseInt(journalStress),
          journal_text: journalText
        })
      });
      if (res.ok) {
        const newEntry = await res.json();
        setJournals(prev => [newEntry, ...prev]);
        setJournalText('');
        setJournalSuccess('Journal entry saved successfully.');
        setTimeout(() => setJournalSuccess(''), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Chatbot submission
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/chatbot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          current_mood: history.length > 0 ? history[history.length - 1].mood : "None"
        })
      });
      const data = await response.json();
      setChatMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I am offline right now. Try again later.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const startBreakTimer = () => {
    setTimerSecondsLeft(timerMinutes * 60);
    setTimerActive(true);
    setTimerAlert(false);
    if (Notification.permission === "default") {
      Notification.requestPermission();
    }
  };

  const startBreathing = () => {
    setBreathingState('Inhale');
    setBreathingSecs(4);
    setBreathingActive(true);
  };

  const formatTime = (time) => {
    if (isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  const getMoodColor = (mood) => {
    switch (mood) {
      case 'Happy': return 'var(--accent-cyan)';
      case 'Sad': return 'var(--primary)';
      case 'Anxiety': return 'var(--accent-emerald)';
      case 'Angry': return 'var(--accent-rose)';
      case 'Tired': return 'var(--text-muted)';
      default: return 'var(--text-secondary)';
    }
  };

  const renderHistoryChart = () => {
    if (history.length === 0) return null;

    const labels = history.map((s, index) => {
      const date = new Date(s.timestamp);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    });

    const stressData = history.map(s => s.stress);
    const anxietyData = history.map(s => s.anxiety);

    const data = {
      labels,
      datasets: [
        {
          label: 'Stress level',
          data: stressData,
          borderColor: 'hsl(345, 100%, 60%)',
          backgroundColor: 'rgba(244, 63, 94, 0.1)',
          tension: 0.35,
          fill: true,
        },
        {
          label: 'Anxiety level',
          data: anxietyData,
          borderColor: 'hsl(185, 100%, 50%)',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          tension: 0.35,
          fill: true,
        }
      ]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: 'hsl(210, 14%, 75%)',
            font: { family: 'Outfit', size: 12 }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'hsl(210, 10%, 55%)', font: { family: 'Outfit' } }
        },
        y: {
          min: 1,
          max: 10,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: 'hsl(210, 10%, 55%)', font: { family: 'Outfit' } }
        }
      }
    };

    return <Line data={data} options={options} height={220} />;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Loading Wellness Dashboard...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Welcome Banner */}
      <div className="glass-panel" style={{
        padding: '2rem 2.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1.5rem',
        position: 'relative'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Smile style={{ color: 'var(--accent-cyan)', width: '20px', height: '20px' }} />
            <span style={{ color: 'var(--accent-cyan)', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase' }}>Wellness Hub</span>
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>Your Healing Center</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '650px' }}>
            {history.length > 0
              ? `Recommended soundscape: ${currentMoodState}. Use the player below to listen to curated Spotify songs matching your emotional parameters.`
              : 'Complete your health profile to retrieve a targeted recommendation list generated by our machine learning models.'
            }
          </p>
        </div>

        {history.length > 0 && (
          <div className="glass-card" style={{
            borderColor: getMoodColor(history[history.length - 1].mood),
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            textAlign: 'right',
            minWidth: '220px'
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Last Logged Mood</span>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: getMoodColor(history[history.length - 1].mood) }}>
              {history[history.length - 1].mood}
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Stress Level: {history[history.length - 1].stress}/10
            </span>
          </div>
        )}
      </div>

      {history.length === 0 ? (
        <div className="glass-panel" style={{ padding: '4rem 2rem', textAlign: 'center', minHeight: '350px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <AlertCircle style={{ width: '56px', height: '56px', color: 'var(--primary)', marginBottom: '1.5rem' }} />
          <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Diagnostic Survey Found</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', marginBottom: '2rem' }}>
            We need to evaluate your current emotional state first to curate a custom therapeutic playlist.
          </p>
          <button id="dashboard-take-survey-btn" className="btn-primary" onClick={() => onViewChange('survey')}>
            Take Diagnostic Survey
            <ClipboardList style={{ width: '18px', height: '18px' }} />
          </button>
        </div>
      ) : (
        <div className="dashboard-grid">
          
          {/* Main Area: Player, Playlist, Feedback, and Grounding */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            {/* Custom Premium Audio Player */}
            <div className="glass-panel" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Music style={{ color: 'var(--primary)', width: '18px', height: '18px' }} />
                  Therapeutic Audio Player
                </h3>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Mood Match: <strong style={{ color: 'var(--accent-cyan)' }}>97%</strong>
                </span>
              </div>

              {activeTrack ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '2rem' }}>
                  
                  {/* Album Cover Art */}
                  <div style={{ position: 'relative', width: '120px', height: '120px' }}>
                    <img 
                      src={activeTrack.album_image || "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=150&h=150&fit=crop"} 
                      alt="Album art" 
                      style={{
                        width: '100%',
                        height: '100%',
                        borderRadius: '12px',
                        objectFit: 'cover',
                        border: '2px solid var(--border-glass)',
                        boxShadow: isPlaying ? '0 0 15px var(--primary-glow)' : 'none'
                      }}
                    />
                    {isPlaying && (
                      <div style={{
                        position: 'absolute',
                        bottom: '4px',
                        right: '4px',
                        background: 'var(--bg-deep)',
                        borderRadius: '50%',
                        padding: '4px',
                        border: '1px solid var(--primary)'
                      }}>
                        <Disc className="spin" style={{ color: 'var(--primary)', width: '16px', height: '16px' }} />
                      </div>
                    )}
                  </div>

                  {/* Track Meta Details */}
                  <div style={{ flex: 1, minWidth: '220px' }}>
                    <h4 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                      {activeTrack.title}
                    </h4>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem', fontWeight: 500 }}>
                      {activeTrack.artist}
                    </p>
                    
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '0.2rem 0.5rem',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid var(--border-glass)',
                        borderRadius: '4px',
                        color: 'var(--text-muted)'
                      }}>
                        Duration: {activeTrack.duration}
                      </span>
                      
                      {activeTrack.preview_url ? (
                        <span style={{
                          fontSize: '0.75rem',
                          padding: '0.2rem 0.5rem',
                          background: 'rgba(16, 185, 129, 0.1)',
                          border: '1px solid var(--accent-emerald)',
                          borderRadius: '4px',
                          color: 'var(--accent-emerald)'
                        }}>
                          Preview Available
                        </span>
                      ) : (
                        <span style={{
                          fontSize: '0.75rem',
                          padding: '0.2rem 0.5rem',
                          background: 'rgba(239, 68, 68, 0.1)',
                          border: '1px solid var(--accent-rose)',
                          borderRadius: '4px',
                          color: 'var(--accent-rose)'
                        }}>
                          Full Stream Only
                        </span>
                      )}
                    </div>
                  </div>

                </div>
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>Select a track to listen.</p>
              )}

              {/* HTML5 Audio Player */}
              {activeTrack?.preview_url && (
                <audio
                  ref={audioRef}
                  src={activeTrack.preview_url}
                  onTimeUpdate={handleTimeUpdate}
                  onEnded={handleNextTrack}
                />
              )}

              {/* Progress Slider */}
              {activeTrack?.preview_url && (
                <div style={{ marginTop: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                  </div>
                  <input 
                    id="music-progress-slider"
                    type="range" 
                    min="0" 
                    max={duration || 100} 
                    value={currentTime} 
                    onChange={handleSeek} 
                    className="slider-custom"
                  />
                </div>
              )}

              {/* Controls */}
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <button id="player-prev-btn" className="btn-secondary" style={{ padding: '0.5rem', borderRadius: '50%' }} onClick={handlePrevTrack}>
                    <SkipBack style={{ width: '16px', height: '16px' }} />
                  </button>
                  
                  {activeTrack?.preview_url ? (
                    <button id="player-play-btn" className="btn-primary" style={{ padding: '0.75rem', borderRadius: '50%' }} onClick={() => handlePlayPause()}>
                      {isPlaying ? <Pause style={{ width: '18px', height: '18px' }} /> : <Play style={{ width: '18px', height: '18px' }} />}
                    </button>
                  ) : (
                    <div style={{ width: '42px', height: '42px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <VolumeX style={{ width: '20px', height: '20px', color: 'var(--text-muted)' }} title="No audio preview" />
                    </div>
                  )}
                  
                  <button id="player-next-btn" className="btn-secondary" style={{ padding: '0.5rem', borderRadius: '50%' }} onClick={handleNextTrack}>
                    <SkipForward style={{ width: '16px', height: '16px' }} />
                  </button>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {activeTrack && (
                    <button 
                      className="btn-secondary" 
                      onClick={() => toggleFavorite(activeTrack)}
                      style={{ borderColor: isFavorite(activeTrack) ? 'var(--accent-rose)' : 'var(--border-glass)' }}
                    >
                      <Heart style={{ width: '16px', height: '16px', fill: isFavorite(activeTrack) ? 'var(--accent-rose)' : 'none', color: isFavorite(activeTrack) ? 'var(--accent-rose)' : 'var(--text-secondary)' }} />
                      {isFavorite(activeTrack) ? 'Saved' : 'Save'}
                    </button>
                  )}

                  {activeTrack?.play_url && (
                    <a 
                      href={activeTrack.play_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="btn-primary"
                      style={{ textDecoration: 'none' }}
                    >
                      ▶ Play on Spotify
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Spotify Recommended Tracks List */}
            <div className="glass-panel" style={{ padding: '1.5rem 2rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                Curated Recommendations
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {currentTracks.map((track, idx) => (
                  <div 
                    key={idx}
                    className="track-queue-item"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      background: idx === activeTrackIndex ? 'rgba(255,255,255,0.06)' : 'transparent',
                      border: idx === activeTrackIndex ? '1px solid var(--border-neon)' : '1px solid transparent',
                      cursor: 'pointer'
                    }}
                    onClick={() => handlePlayPause(idx)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <img 
                        src={track.album_image || "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=150&h=150&fit=crop"} 
                        alt="" 
                        style={{ width: '40px', height: '40px', borderRadius: '4px', objectFit: 'cover' }}
                      />
                      <div>
                        <div style={{ fontWeight: 600, color: idx === activeTrackIndex ? 'var(--primary)' : 'var(--text-primary)', fontSize: '0.95rem' }}>
                          {track.title}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {track.artist}
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{track.duration}</span>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(track);
                        }} 
                        style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                      >
                        <Heart style={{ width: '14px', height: '14px', fill: isFavorite(track) ? 'var(--accent-rose)' : 'none', color: isFavorite(track) ? 'var(--accent-rose)' : 'var(--text-muted)' }} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Star Rating User Feedback Widget */}
            <div className="glass-panel" style={{ padding: '1.5rem 2rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Did this music help you?</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Your feedback directly improves future machine learning curations.
              </p>

              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => submitFeedback(star, null)}
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}
                    >
                      <Star 
                        style={{ 
                          width: '28px', 
                          height: '28px', 
                          fill: star <= (hoverRating || rating) ? 'var(--primary)' : 'none', 
                          color: star <= (hoverRating || rating) ? 'var(--primary)' : 'var(--text-muted)' 
                        }} 
                      />
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button 
                    className="btn-secondary"
                    onClick={() => submitFeedback(rating, true)}
                    style={{ borderColor: helped === true ? 'var(--accent-emerald)' : 'var(--border-glass)', background: helped === true ? 'rgba(16, 185, 129, 0.08)' : 'transparent', padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                  >
                    Yes, it helped
                  </button>
                  <button 
                    className="btn-secondary"
                    onClick={() => submitFeedback(rating, false)}
                    style={{ borderColor: helped === false ? 'var(--accent-rose)' : 'var(--border-glass)', background: helped === false ? 'rgba(239, 68, 68, 0.08)' : 'transparent', padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                  >
                    No, not really
                  </button>
                </div>
              </div>
              
              {feedbackSuccess && (
                <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent-emerald)', fontWeight: 500 }}>
                  {feedbackSuccess}
                </div>
              )}
            </div>

            {/* Emergency Support links and Guided Grounding Tool */}
            <div className="glass-panel" style={{ padding: '2rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <HeartHandshake style={{ color: 'var(--accent-rose)', width: '20px', height: '20px' }} />
                Anxiety Grounding & Emergency Support
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }} className="grounding-subgrid">
                
                {/* Breathing Grounder */}
                <div className="glass-card" style={{ textAlign: 'center', padding: '1.5rem' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.5rem' }}>5-4-3-2-1 Grounding Breather</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                    Feeling overwhelmed? Activate this breathing guidance circle.
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '140px', marginBottom: '1rem' }}>
                    <div 
                      style={{
                        width: breathingState === 'Inhale' ? '120px' : breathingState === 'Hold' ? '120px' : breathingState === 'Exhale' ? '60px' : '60px',
                        height: breathingState === 'Inhale' ? '120px' : breathingState === 'Hold' ? '120px' : breathingState === 'Exhale' ? '60px' : '60px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, var(--accent-cyan) 0%, var(--primary) 100%)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 0 20px var(--primary-glow)',
                        transition: 'all 4s linear',
                        color: 'var(--bg-deep)',
                        fontWeight: 800
                      }}
                    >
                      <div>{breathingState}</div>
                      <div style={{ fontSize: '0.85rem' }}>{breathingActive ? `${breathingSecs}s` : ''}</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem' }}>
                    {!breathingActive ? (
                      <button className="btn-primary" onClick={startBreathing} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                        Start Breather
                      </button>
                    ) : (
                      <button className="btn-secondary" onClick={() => setBreathingActive(false)} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                        Stop Guidance
                      </button>
                    )}
                  </div>
                </div>

                {/* Support lines */}
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Crisis Helplines</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                    If you are experiencing severe distress, please connect with standard professional support:
                  </p>
                  <ul style={{ listStyle: 'none', paddingLeft: 0, fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <li>🇺🇸 <strong>National Crisis Lifeline:</strong> Call/Text 988 (Available 24/7)</li>
                    <li>🇬🇧 <strong>Samaritans UK:</strong> Call 116 123 (Available 24/7)</li>
                    <li>🇮🇳 <strong>KIRAN Helpline:</strong> 1800-599-0019 (Available 24/7)</li>
                    <li>🌎 <strong>Crisis Text Line:</strong> Text HOME to 741741</li>
                  </ul>
                </div>
              </div>
            </div>

          </div>

          {/* Sidebar Area: Trends, Daily Journal, Chatbot, Relaxation break */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            {/* Break Notification timer */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Bell style={{ color: 'var(--primary)', width: '16px', height: '16px' }} />
                Relaxation Break Alerts
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
                Set a notification reminder to step back from screens.
              </p>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                <select 
                  id="break-timer-select"
                  className="input-field" 
                  value={timerMinutes} 
                  onChange={(e) => {
                    setTimerMinutes(parseInt(e.target.value));
                    setTimerSecondsLeft(parseInt(e.target.value) * 60);
                  }}
                  disabled={timerActive}
                  style={{ flex: 1, padding: '0.5rem', fontSize: '0.85rem' }}
                >
                  <option value={1}>1 Minute (Test)</option>
                  <option value={20}>20 Minutes</option>
                  <option value={40}>40 Minutes</option>
                  <option value={60}>60 Minutes</option>
                </select>

                {!timerActive ? (
                  <button className="btn-primary" onClick={startBreakTimer} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                    Start
                  </button>
                ) : (
                  <button className="btn-secondary" onClick={() => setTimerActive(false)} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', color: 'var(--accent-rose)', borderColor: 'rgba(239,68,68,0.2)' }}>
                    Stop
                  </button>
                )}
              </div>

              {timerActive && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Remaining time:</span>
                  <strong style={{ color: 'var(--primary)' }}>
                    {Math.floor(timerSecondsLeft / 60)}:{(timerSecondsLeft % 60).toString().padStart(2, '0')}
                  </strong>
                </div>
              )}
            </div>

            {/* Historical trends chart */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar style={{ color: 'var(--accent-cyan)', width: '16px', height: '16px' }} />
                Mood Tracking Trends
              </h4>
              <div style={{ height: '220px', position: 'relative' }}>
                {renderHistoryChart()}
              </div>
            </div>

            {/* Daily Mood Journal widget */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BookOpen style={{ color: 'var(--accent-emerald)', width: '16px', height: '16px' }} />
                Daily Mood Journal
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
                Log thoughts to keep track of your mental health history.
              </p>

              <form onSubmit={handleJournalSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <label className="input-label" htmlFor="journal-mood-select" style={{ fontSize: '0.75rem' }}>Mood</label>
                    <select 
                      id="journal-mood-select"
                      className="input-field" 
                      value={journalMood} 
                      onChange={(e) => setJournalMood(e.target.value)}
                      style={{ padding: '0.4rem', fontSize: '0.8rem' }}
                    >
                      {MOODS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="input-label" htmlFor="journal-stress-slider" style={{ fontSize: '0.75rem' }}>Stress: {journalStress}</label>
                    <input 
                      id="journal-stress-slider"
                      type="range" 
                      min="1" 
                      max="10" 
                      className="slider-custom"
                      value={journalStress} 
                      onChange={(e) => setJournalStress(e.target.value)} 
                    />
                  </div>
                </div>

                <textarea
                  className="input-field"
                  placeholder="How was your day? Log your thoughts..."
                  value={journalText}
                  onChange={(e) => setJournalText(e.target.value)}
                  style={{ resize: 'none', height: '70px', padding: '0.5rem', fontSize: '0.85rem', fontFamily: 'var(--font-secondary)' }}
                />

                <button type="submit" className="btn-primary" style={{ justifyContent: 'center', padding: '0.5rem', fontSize: '0.85rem' }}>
                  Save Journal Entry
                </button>
              </form>

              {journalSuccess && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--accent-emerald)', fontWeight: 500 }}>
                  {journalSuccess}
                </div>
              )}

              {/* Journal log listing */}
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '180px', overflowY: 'auto' }}>
                {journals.map((e) => {
                  const date = new Date(e.timestamp);
                  return (
                    <div key={e.id} className="glass-card" style={{ padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.01)', borderRadius: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                        <span style={{ color: getMoodColor(e.mood), fontWeight: 700 }}>{e.mood} (Stress: {e.stress}/10)</span>
                        <span style={{ color: 'var(--text-muted)' }}>{date.toLocaleDateString()}</span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>{e.journal_text}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* AI Chatbot for wellness tips */}
            <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '350px' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles style={{ color: 'var(--accent-cyan)', width: '16px', height: '16px' }} />
                Wellness Companion Chat
              </h4>
              
              {/* Messages window */}
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', margin: '0.75rem 0', paddingRight: '0.25rem' }}>
                {chatMessages.map((msg, index) => (
                  <div 
                    key={index}
                    style={{
                      alignSelf: msg.sender === 'bot' ? 'flex-start' : 'flex-end',
                      background: msg.sender === 'bot' ? 'rgba(255,255,255,0.04)' : 'rgba(168, 85, 247, 0.1)',
                      border: msg.sender === 'bot' ? '1px solid var(--border-glass)' : '1px solid var(--border-neon)',
                      borderRadius: msg.sender === 'bot' ? '12px 12px 12px 2px' : '12px 12px 2px 12px',
                      padding: '0.6rem 0.8rem',
                      maxWidth: '85%',
                      fontSize: '0.825rem',
                      color: 'var(--text-primary)',
                      lineHeight: 1.4,
                      wordBreak: 'break-word'
                    }}
                  >
                    {msg.text}
                  </div>
                ))}
                {chatLoading && (
                  <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '8px' }}>
                    <div className="visualizer-container" style={{ height: '12px', width: '30px', gap: '2px' }}>
                      <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
                      <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
                      <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat input */}
              <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text"
                  className="input-field"
                  placeholder="Ask for anxiety tips..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.825rem' }}
                />
                <button type="submit" className="btn-primary" style={{ padding: '0.4rem 0.75rem' }}>
                  <Send style={{ width: '14px', height: '14px' }} />
                </button>
              </form>
            </div>

          </div>

        </div>
      )}
    </div>
  );
}
