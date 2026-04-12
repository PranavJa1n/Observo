import React, { useState } from 'react';
import { Terminal, Copy, CheckCircle, Download, Settings, Play } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: <Download size={22} color="#667eea" />,
    title: 'Install Observo',
    description: 'Run the one-line install script to download and set up the Observo binary on your machine.',
    command: 'curl -sL https://raw.githubusercontent.com/PranavJa1n/Observo/main/install.sh | bash',
    comment: '# Downloads and installs the Observo binary'
  },
  {
    number: '02',
    icon: <Settings size={22} color="#9b51e0" />,
    title: 'Initialize Config',
    description: 'Run the init command to interactively configure your log paths, API keys, and alert settings.',
    command: 'observo init',
    comment: '# Interactive setup — sets up ~/.observo/config.json'
  },
  {
    number: '03',
    icon: <Play size={22} color="#4ade80" />,
    title: 'Start Monitoring',
    description: 'Launch the daemon. Observo will begin watching your logs and serve the dashboard on port 6969.',
    command: 'observo start',
    comment: '# Starts file watcher + dashboard at localhost:6969'
  }
];

function StepCard({ step, index }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(step.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div style={{ 
      display: 'flex', 
      gap: '24px', 
      alignItems: 'flex-start',
      animation: `fadeUp 0.5s ease forwards`,
      animationDelay: `${index * 0.15}s`,
      opacity: 0
    }}>
      {/* Step Number + Line */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          width: '48px', height: '48px',
          borderRadius: '50%',
          background: 'var(--icon-bg)',
          border: '1px solid var(--card-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'monospace',
          fontWeight: 'bold',
          fontSize: '0.85rem',
          color: 'var(--accent-purple-light)',
          flexShrink: 0
        }}>
          {step.number}
        </div>
        {index < steps.length - 1 && (
          <div style={{ width: '1px', flex: 1, minHeight: '40px', background: 'var(--card-border)', marginTop: '8px' }} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingBottom: index < steps.length - 1 ? '40px' : '0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          {step.icon}
          <h3 style={{ fontSize: '1.3rem' }}>{step.title}</h3>
        </div>
        <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '16px' }}>
          {step.description}
        </p>

        {/* Terminal Command */}
        <div style={{
          background: 'var(--code-bg)',
          border: '1px solid var(--card-border)',
          borderRadius: '10px',
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'var(--sub-panel-bg)',
            padding: '8px 16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            borderBottom: '1px solid var(--card-border)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <Terminal size={13} /> bash
            </div>
            <button onClick={handleCopy} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px',
              color: copied ? '#4ade80' : 'var(--text-muted)',
              fontSize: '0.8rem', transition: 'color 0.2s'
            }}>
              {copied ? <><CheckCircle size={13} /> Copied!</> : <><Copy size={13} /> Copy</>}
            </button>
          </div>
          <div style={{ padding: '16px 20px', fontFamily: 'monospace', fontSize: '0.95rem', lineHeight: '1.7', color: 'var(--text-main)' }}>
            <span style={{ color: 'var(--accent-purple-light)', userSelect: 'none' }}>$ </span>
            {step.command}
            <div style={{ color: 'var(--text-muted)', marginTop: '4px', fontSize: '0.85rem' }}>{step.comment}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HowToInstall() {
  return (
    <section id="install">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '80px', alignItems: 'start' }}>
        
        {/* Left: Header */}
        <div style={{ position: 'sticky', top: '120px' }}>
          <div style={{
            display: 'inline-block',
            padding: '5px 12px',
            borderRadius: '20px',
            background: 'var(--icon-bg)',
            color: 'var(--accent-purple-light)',
            fontWeight: 600,
            fontSize: '0.85rem',
            marginBottom: '20px',
            border: '1px solid var(--card-border)'
          }}>
            Quick Start
          </div>
          <h2 style={{ fontSize: '3rem', lineHeight: '1.1', marginBottom: '20px' }}>
            How to <span className="text-gradient">Install</span>
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', lineHeight: '1.7' }}>
            Get Observo up and running in under a minute. Just three commands and your logs are being intelligently monitored.
          </p>

          <div style={{ marginTop: '40px', padding: '20px', borderRadius: '10px', background: 'var(--icon-bg)', border: '1px solid var(--card-border)' }}>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '8px' }}>Requirements</p>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {['Go 1.21+', 'Python 3.9+', 'Google Gemini API Key'].map(req => (
                <li key={req} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                  <span style={{ color: '#4ade80' }}>✓</span> {req}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right: Steps */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {steps.map((step, i) => (
            <StepCard key={i} step={step} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
