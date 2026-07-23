import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, Music, Heart, Moon, Wind, Smile, Play, Volume2, Lightbulb, Compass, RefreshCw } from 'lucide-react';

export default function AIChatAssistant({ token, apiBaseUrl, onPlayTrack }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      category: 'welcome',
      text: "Hello! I am your AI Wellness Assistant. I am here to help you reduce stress, discover therapeutic music, and support your mental well-being.",
      suggestedTracks: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const quickPrompts = [
    { label: "Suggest Relaxing Songs", query: "Suggest songs for anxiety relief and relaxation", icon: Music, color: "var(--primary)" },
    { label: "Relaxation Techniques", query: "Recommend a 5-minute relaxation and breathing technique", icon: Wind, color: "var(--accent-cyan)" },
    { label: "Motivational Quote", query: "Give me an uplifting motivational quote for mental health", icon: Lightbulb, color: "var(--accent-amber)" },
    { label: "Meditation Music", query: "Recommend deep meditation music for sleep and focus", icon: Moon, color: "var(--accent-purple)" },
    { label: "Mental Wellness Q&A", query: "How can I manage daily stress and overcome burnout?", icon: Heart, color: "var(--accent-rose)" }
  ];

  const handleSend = async (customQuery = null) => {
    const textToSend = customQuery || input;
    if (!textToSend.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!customQuery) setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/chatbot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: textToSend })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch response from AI Assistant');
      }

      const data = await response.json();
      
      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.reply || "I'm here to support your mental wellness journey. Try listening to one of our curated playlists!",
        category: data.category || 'general',
        suggestedTracks: data.suggested_tracks || [],
        quote: data.quote || null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: "I'm sorry, I ran into a slight network issue. Try a grounding 4-7-8 breathing session while I re-establish connection!",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner */}
      <div className="glass-panel" style={{
        padding: '1.75rem 2rem',
        borderRadius: '24px',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))',
        border: '1px solid var(--border-neon)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'var(--primary-glow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px var(--primary-glow)'
          }}>
            <Bot style={{ width: '30px', height: '30px', color: '#fff' }} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.2rem' }}>
              AI Wellness & Music Assistant
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Your 24/7 companion for music recommendations, stress reduction, quotes, and mental wellness guidance.
            </p>
          </div>
        </div>

        <button
          onClick={() => setMessages([{
            id: Date.now(),
            sender: 'bot',
            text: "Chat history cleared. How can I assist your emotional well-being right now?",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }])}
          className="btn-secondary"
          style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
        >
          <RefreshCw style={{ width: '14px', height: '14px' }} /> Clear Chat
        </button>
      </div>

      {/* Quick Category Action Chips */}
      <div style={{ display: 'flex', gap: '0.65rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
        {quickPrompts.map((prompt, idx) => {
          const Icon = prompt.icon;
          return (
            <button
              key={idx}
              onClick={() => handleSend(prompt.query)}
              disabled={loading}
              className="glass-panel"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.1rem',
                borderRadius: '50px',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                cursor: loading ? 'not-allowed' : 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease',
                border: '1px solid var(--border-glass)',
                background: 'rgba(255, 255, 255, 0.03)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = prompt.color}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-glass)'}
            >
              <Icon style={{ width: '15px', height: '15px', color: prompt.color }} />
              {prompt.label}
            </button>
          );
        })}
      </div>

      {/* Chat Conversation Box */}
      <div className="glass-panel" style={{
        borderRadius: '24px',
        padding: '1.75rem',
        minHeight: '480px',
        maxHeight: '600px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-lg)'
      }}>
        
        {/* Messages Scroll Area */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          paddingRight: '0.5rem',
          marginBottom: '1.25rem'
        }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: msg.sender === 'user' ? '75%' : '88%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <div style={{
                background: msg.sender === 'user' 
                  ? 'linear-gradient(135deg, var(--primary), var(--secondary))' 
                  : 'rgba(255, 255, 255, 0.04)',
                border: msg.sender === 'user' 
                  ? 'none' 
                  : '1px solid var(--border-glass)',
                borderRadius: msg.sender === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                padding: '1rem 1.25rem',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                lineHeight: '1.6',
                boxShadow: msg.sender === 'user' ? '0 4px 15px rgba(99, 102, 241, 0.3)' : 'none'
              }}>
                {/* Text Content */}
                <div style={{ whiteSpace: 'pre-wrap' }}>
                  {msg.text}
                </div>

                {/* Motivational Quote Render */}
                {msg.quote && (
                  <div style={{
                    marginTop: '1rem',
                    padding: '1rem 1.25rem',
                    borderRadius: '14px',
                    background: 'rgba(245, 158, 11, 0.12)',
                    borderLeft: '4px solid var(--accent-amber)',
                    fontStyle: 'italic'
                  }}>
                    <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                      "{msg.quote.quote}"
                    </p>
                    <span style={{ fontSize: '0.825rem', color: 'var(--accent-amber)', fontStyle: 'normal', fontWeight: 700 }}>
                      — {msg.quote.author}
                    </span>
                  </div>
                )}

                {/* Suggested Song Cards with Embedded YouTube Search Players */}
                {msg.suggestedTracks && msg.suggestedTracks.length > 0 && (
                  <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      🎵 Recommended Embedded Song Players
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.85rem' }}>
                      {msg.suggestedTracks.map((track, tIdx) => (
                        <div
                          key={tIdx}
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.6rem',
                            background: 'rgba(0, 0, 0, 0.45)',
                            padding: '0.85rem',
                            borderRadius: '16px',
                            border: '1px solid var(--border-glass)'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <img
                              loading="lazy"
                              decoding="async"
                              src={track.album_image || "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=100&h=100&fit=crop"}
                              alt={track.title}
                              style={{ width: '42px', height: '42px', borderRadius: '8px', objectFit: 'cover' }}
                            />
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontSize: '0.875rem', fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {track.title}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {track.artist} {track.mood ? `• Mood: ${track.mood}` : ''}
                              </div>
                            </div>
                            {onPlayTrack && (
                              <button
                                onClick={() => onPlayTrack(track)}
                                style={{
                                  background: 'var(--primary)',
                                  border: 'none',
                                  color: '#fff',
                                  borderRadius: '50%',
                                  width: '32px',
                                  height: '32px',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  cursor: 'pointer',
                                  transition: 'transform 0.15s ease'
                                }}
                                title="Set active track"
                                onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
                                onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                              >
                                <Play style={{ width: '14px', height: '14px', marginLeft: '2px' }} />
                              </button>
                            )}
                          </div>

                          {/* Dynamic YouTube Search Embed Iframe */}
                          <iframe
                            width="100%"
                            height="160"
                            src={track.embed_url || `https://www.youtube.com/embed?listType=search&list=${encodeURIComponent((track.artist || '') + ' ' + (track.title || ''))}`}
                            title={track.title}
                            frameBorder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            style={{ borderRadius: '12px', border: '1px solid var(--border-glass)', background: '#000' }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
              <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '0.35rem', padding: '0 0.25rem' }}>
                {msg.timestamp}
              </span>
            </div>
          ))}

          {loading && (
            <div style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.03)', padding: '0.85rem 1.25rem', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
              <Bot style={{ width: '18px', height: '18px', color: 'var(--primary)' }} />
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>AI Assistant is reflecting...</span>
              <div className="visualizer-container" style={{ height: '14px', width: '24px', gap: '2px' }}>
                <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
                <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
                <div className="visualizer-bar" style={{ width: '2px', height: '100%' }} />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Ask about songs, breathing techniques, motivational quotes, meditation..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            style={{ flex: 1, padding: '0.85rem 1.25rem', fontSize: '0.925rem', borderRadius: '16px' }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-primary"
            style={{
              padding: '0.85rem 1.5rem',
              borderRadius: '16px',
              opacity: (loading || !input.trim()) ? 0.6 : 1,
              cursor: (loading || !input.trim()) ? 'not-allowed' : 'pointer'
            }}
          >
            <Send style={{ width: '18px', height: '18px' }} />
            <span>Send</span>
          </button>
        </form>

      </div>

    </div>
  );
}
