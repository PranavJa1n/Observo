import React, { useState, useEffect } from 'react';
import { HashRouter, Routes, Route, Link } from 'react-router-dom';
import Hero from './components/Hero';
import Features from './components/Features';
import HowToInstall from './components/HowToInstall';
import Commands from './components/Commands';
import { Sun, Moon, Database, Command, Terminal, Globe } from 'lucide-react';

function Landing() {
  return (
    <main>
      <Hero />
      <Features />
      <HowToInstall />
    </main>
  );
}

function App() {
  const [isLightMode, setIsLightMode] = useState(false);

  useEffect(() => {
    if (isLightMode) {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
  }, [isLightMode]);

  return (
    <HashRouter>
      <div style={{ minHeight: '100vh', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        {/* Subtle grid background */}
        <div style={{
          position: 'fixed', top: 0, left: 0,
          width: '100vw', height: '100vh',
          zIndex: -1, pointerEvents: 'none',
          backgroundImage: `linear-gradient(var(--grid-color) 1px, transparent 1px), linear-gradient(90deg, var(--grid-color) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }} />

        <header style={{
          padding: '24px 40px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'relative',
          zIndex: 100,
          borderBottom: '1px solid var(--card-border)',
          background: 'var(--card-bg)',
          backdropFilter: 'blur(12px)'
        }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none', color: 'var(--text-main)', fontWeight: 'bold', fontSize: '1.4rem' }}>
            <Database color="var(--accent-purple-light)" /> Observo
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <Link to="/commands" style={{ textDecoration: 'none', color: 'var(--text-main)', fontWeight: 500 }}>
              Commands
            </Link>
            <button
              onClick={() => setIsLightMode(!isLightMode)}
              style={{
                background: 'var(--code-bg)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-main)',
                padding: '10px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
              }}
              title="Toggle Theme"
            >
              {isLightMode ? <Moon size={18} /> : <Sun size={18} />}
            </button>
          </div>
        </header>

        <div style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/commands" element={<Commands isLightMode={isLightMode} />} />
          </Routes>
        </div>

        <footer style={{
          padding: '80px 40px',
          background: 'var(--icon-bg)',
          borderTop: '1px solid var(--card-border)',
          marginTop: '60px'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '40px' }}>
            <div>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.4rem', marginBottom: '20px' }}>
                <Database color="var(--accent-purple-light)" /> Observo
              </h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>
                The open-source AI log analysis engine. Turn your server errors into plain english fixes in milliseconds.
              </p>
            </div>

            <div>
              <h4 style={{ marginBottom: '20px', color: 'var(--text-main)' }}>Resources</h4>
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <li><Link to="/commands" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>CLI Commands Reference</Link></li>
                <li><a href="#" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>LangGraph Documentation</a></li>
                <li><a href="#" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>HDBSCAN Whitepaper</a></li>
              </ul>
            </div>

            <div>
              <h4 style={{ marginBottom: '20px', color: 'var(--text-main)' }}>Connect</h4>
              <div style={{ display: 'flex', gap: '16px' }}>
                <a href="https://github.com/PranavJa1n/Observo" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-muted)' }}>
                  <Terminal size={24} />
                </a>
                <a href="#" style={{ color: 'var(--text-muted)' }}>
                  <Globe size={24} />
                </a>
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: '60px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            <p>© 2026 Observo. Built by Pranav Jain & Madhav Garg.</p>
          </div>
        </footer>
      </div>
    </HashRouter>
  );
}

export default App;
