import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Terminal, Command } from 'lucide-react';
import { Link } from 'react-router-dom';

const LOG_LINES = [
  { type: 'info',  text: '[INFO]  2026-04-17 12:00:01  Server started on :8080' },
  { type: 'info',  text: '[INFO]  2026-04-17 12:00:03  Connected to database' },
  { type: 'warn',  text: '[WARN]  2026-04-17 12:00:07  High memory usage: 87%' },
  { type: 'error', text: '[ERROR] 2026-04-17 12:00:09  Unhandled exception in worker thread' },
  { type: 'info',  text: '[INFO]  2026-04-17 12:00:11  Request GET /api/users 200 OK' },
  { type: 'error', text: '[ERROR] 2026-04-17 12:00:12  Connection refused: redis:6379' },
  { type: 'info',  text: '[INFO]  2026-04-17 12:00:14  Request POST /api/orders 201 Created' },
  { type: 'warn',  text: '[WARN]  2026-04-17 12:00:16  Slow query detected: 4.2s' },
  { type: 'error', text: '[ERROR] 2026-04-17 12:00:17  Segmentation fault (core dumped)' },
  { type: 'info',  text: '[INFO]  2026-04-17 12:00:19  Cache hit ratio: 94.3%' },
  { type: 'cluster', text: '✦ Observo: Clustering 3 anomaly groups...' },
  { type: 'cluster', text: '✦ Observo: Root cause — redis connection pool exhausted' },
  { type: 'cluster', text: '✦ Fix: Increase maxconn in redis.conf to 512' },
];

const typeColor = {
  info:    '#71717a',
  warn:    '#d97706',
  error:   '#ef4444',
  cluster: '#22c55e',
};

function AnimatedTerminal() {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    let line = 0;
    const lines = el.querySelectorAll('.log-line');
    lines.forEach(l => { l.style.opacity = '0'; l.style.transform = 'translateY(6px)'; });

    const show = () => {
      if (line >= lines.length) return;
      lines[line].style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      lines[line].style.opacity = '1';
      lines[line].style.transform = 'translateY(0)';
      line++;
      setTimeout(show, line < 10 ? 400 : 700);
    };
    setTimeout(show, 600);
  }, []);

  return (
    <div style={{
      background: '#0d0d0d',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: '14px',
      overflow: 'hidden',
      boxShadow: '0 40px 80px rgba(0,0,0,0.6)',
      width: '100%',
      maxWidth: '560px',
    }}>
      {/* Title bar */}
      <div style={{
        background: '#161616',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }} />
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }} />
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28c840' }} />
        <span style={{ marginLeft: 8, fontSize: '0.8rem', color: '#555', fontFamily: 'monospace' }}>observo — log stream</span>
      </div>

      {/* Log lines */}
      <div ref={containerRef} style={{ padding: '20px', fontFamily: 'monospace', fontSize: '0.8rem', lineHeight: '1.9', minHeight: '320px' }}>
        {LOG_LINES.map((l, i) => (
          <div key={i} className="log-line" style={{ color: typeColor[l.type] || '#aaa', fontWeight: l.type === 'cluster' ? 600 : 400 }}>
            {l.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Hero() {
  return (
    <section style={{
      minHeight: '88vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '60px',
      paddingTop: '60px',
      paddingBottom: '60px',
    }}>
      {/* Left copy */}
      <motion.div
        style={{ flex: '1' }}
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div style={{
          display: 'inline-block',
          padding: '5px 14px',
          borderRadius: '20px',
          background: 'var(--icon-bg)',
          color: 'var(--text-muted)',
          fontWeight: 500,
          fontSize: '0.85rem',
          marginBottom: '24px',
          border: '1px solid var(--card-border)',
          letterSpacing: '0.02em',
        }}>
          v1.0 — Open Source
        </div>

        <h1 style={{ fontSize: '3.8rem', lineHeight: '1.1', marginBottom: '24px', letterSpacing: '-0.03em' }}>
          AI that reads your<br />logs so <span className="text-gradient">you don't have to.</span>
        </h1>

        <p style={{ fontSize: '1.15rem', color: 'var(--text-muted)', marginBottom: '40px', lineHeight: '1.7', maxWidth: '480px' }}>
          Observo watches your log files, clusters similar events with HDBSCAN, and uses an Agentic AI pipeline to explain anomalies and generate exact fix steps — in seconds.
        </p>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <a href="#install" className="primary-button">
            Get Started <ArrowRight size={18} />
          </a>
          <Link to="/commands" className="secondary-button">
            <Command size={18} /> Commands
          </Link>
          <a href="https://github.com/PranavJa1n/Observo" target="_blank" rel="noopener noreferrer" className="secondary-button">
            <Terminal size={18} /> GitHub
          </a>
        </div>

        {/* Stats row */}
        <div style={{ display: 'flex', gap: '40px', marginTop: '56px' }}>
          {[['< 1s', 'Analysis latency'], ['HDBSCAN', 'Clustering algorithm'], ['Local', 'Privacy first']].map(([val, label]) => (
            <div key={label}>
              <div style={{ fontSize: '1.3rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{val}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Right terminal */}
      <motion.div
        style={{ flex: '1', display: 'flex', justifyContent: 'flex-end' }}
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.7, delay: 0.2 }}
      >
        <AnimatedTerminal />
      </motion.div>
    </section>
  );
}
