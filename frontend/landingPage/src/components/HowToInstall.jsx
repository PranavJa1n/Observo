import React, { useState } from 'react';
import { Terminal, Copy, CheckCircle, Download, Settings, Play } from 'lucide-react';

const steps = [
  {
    number: '01',
    tag: 'Install',
    title: 'One-line install',
    description: 'Run the bootstrap script. It detects your OS, downloads the correct binary, and places observo on your PATH automatically.',
    command: 'curl -sL https://raw.githubusercontent.com/PranavJa1n/Observo/main/install.sh | bash',
    comment: '# Works on macOS, Linux & WSL',
    accent: '#6366f1',
    bg: 'rgba(99,102,241,0.06)',
  },
  {
    number: '02',
    tag: 'Configure',
    title: 'Interactive setup',
    description: 'Run init to configure your log paths, Google Gemini API key, and email alert settings. All stored locally in ~/.observo/config.json.',
    command: 'observo init',
    comment: '# Sets up ~/.observo/config.json interactively',
    accent: '#f59e0b',
    bg: 'rgba(245,158,11,0.06)',
  },
  {
    number: '03',
    tag: 'Monitor',
    title: 'Start the daemon',
    description: 'Launch the file watcher and AI pipeline. The local dashboard spins up at localhost:6969 and begins clustering your logs immediately.',
    command: 'observo start',
    comment: '# Dashboard at localhost:6969',
    accent: '#22c55e',
    bg: 'rgba(34,197,94,0.06)',
  },
];

function CopyButton({ command }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(command); setCopied(true); setTimeout(() => setCopied(false), 1800); }}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: '5px',
        color: copied ? '#22c55e' : 'rgba(255,255,255,0.3)',
        fontSize: '0.8rem', transition: 'color 0.2s', padding: '4px 8px',
        borderRadius: '6px',
      }}
    >
      {copied ? <CheckCircle size={13} /> : <Copy size={13} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

export default function HowToInstall() {
  return (
    <section id="install">
      {/* Section header */}
      <div style={{ marginBottom: '80px' }}>
        <div style={{
          display: 'inline-block', padding: '5px 14px', borderRadius: '20px',
          background: 'var(--icon-bg)', color: 'var(--text-muted)', fontWeight: 500,
          fontSize: '0.85rem', marginBottom: '20px',
          border: '1px solid var(--card-border)', letterSpacing: '0.02em',
        }}>
          Quick Start
        </div>
        <h2 style={{ fontSize: '3rem', lineHeight: '1.1', letterSpacing: '-0.03em', marginBottom: '16px' }}>
          Up and running in <span className="text-gradient">three commands.</span>
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.05rem', lineHeight: '1.7', maxWidth: '520px' }}>
          No Docker, no Kubernetes, no external databases. Just install, configure, and go.
        </p>
      </div>

      {/* Stacking cards */}
      <div style={{ position: 'relative' }}>
        {steps.map((step, i) => (
          <div
            key={i}
            style={{
              position: 'sticky',
              top: `${80 + i * 20}px`,
              zIndex: i + 1,
              marginBottom: i < steps.length - 1 ? '24px' : '0',
            }}
          >
            <div
              className="glass-panel"
              style={{
                padding: '40px 48px',
                background: 'var(--card-solid)',
                borderRadius: '18px',
                border: '1px solid var(--card-border)',
                boxShadow: `0 ${8 + i * 12}px ${40 + i * 20}px rgba(0,0,0,${0.4 + i * 0.1})`,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '60px',
                alignItems: 'center',
              }}
            >
              {/* Left: Text */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
                  <div style={{
                    width: '42px', height: '42px', borderRadius: '12px',
                    background: step.bg, border: `1px solid ${step.accent}33`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'monospace', fontWeight: 700, fontSize: '0.85rem',
                    color: step.accent,
                  }}>
                    {step.number}
                  </div>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.08em',
                    textTransform: 'uppercase', color: step.accent,
                  }}>
                    {step.tag}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.7rem', fontWeight: 700, marginBottom: '12px', letterSpacing: '-0.02em' }}>
                  {step.title}
                </h3>
                <p style={{ color: 'var(--text-muted)', lineHeight: '1.7', fontSize: '1rem' }}>
                  {step.description}
                </p>
              </div>

              {/* Right: Terminal */}
              <div style={{
                background: 'var(--code-bg)',
                borderRadius: '12px',
                border: '1px solid var(--card-border)',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: '10px 16px',
                  background: 'var(--sub-panel-bg)',
                  borderBottom: '1px solid var(--card-border)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '7px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                    <Terminal size={12} /> bash
                  </div>
                  <CopyButton command={step.command} />
                </div>
                <div style={{ padding: '20px 20px', fontFamily: 'monospace', fontSize: '0.9rem', lineHeight: '1.6', color: 'var(--text-main)', wordBreak: 'break-word' }}>
                  <span style={{ color: step.accent, userSelect: 'none' }}>$ </span>
                  {step.command}
                  <div style={{ color: '#555', marginTop: '6px', fontSize: '0.82rem' }}>{step.comment}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Requirements note */}
      <div style={{
        marginTop: '60px', padding: '20px 28px',
        borderRadius: '12px', background: 'var(--icon-bg)',
        border: '1px solid var(--card-border)',
        display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap',
      }}>
        <span style={{ color: '#555', fontSize: '0.85rem', fontWeight: 500 }}>Requirements</span>
        {['Go 1.21+', 'Python 3.9+', 'Google Gemini API Key', 'Linux / macOS / WSL'].map(r => (
          <span key={r} style={{ display: 'flex', alignItems: 'center', gap: '7px', fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            <span style={{ color: '#22c55e', fontSize: '0.7rem' }}>✓</span> {r}
          </span>
        ))}
      </div>
    </section>
  );
}
