import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Terminal, Copy, CheckCircle } from 'lucide-react';

export default function Installation() {
  const [copied, setCopied] = useState(false);
  const codeString = `curl -sL https://raw.githubusercontent.com/PranavJa1n/Observo/main/install.sh | bash\nobservo init\nobservo start`;

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="install">
      <div className="glass-panel" style={{ padding: '60px 40px', display: 'flex', flexWrap: 'wrap', gap: '40px', alignItems: 'center' }}>
        
        <div style={{ flex: '1', minWidth: '300px' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '20px' }}>Up and running in seconds.</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', lineHeight: '1.6', marginBottom: '30px' }}>
            Observo doesn't require massive architecture shifts. Just run our automated installation script, supply your API key, and it instantly begins clustering your logs.
          </p>
          
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-purple-light)' }} />
              Installs binary cross-platform effortlessly
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-purple-light)' }} />
              No complex external databases needed
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-purple-light)' }} />
              Comes with local realtime dashboard (Port 6969)
            </li>
          </ul>
        </div>

        <div style={{ flex: '1', minWidth: '300px' }}>
          <div style={{ 
            background: 'var(--code-bg)', 
            borderRadius: '12px', 
            border: '1px solid var(--card-border)',
            overflow: 'hidden'
          }}>
            <div style={{ 
              background: 'var(--sub-panel-bg)', 
              padding: '12px 20px', 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--card-border)'
            }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                <Terminal size={16} /> Terminal
              </div>
              <button 
                onClick={handleCopy}
                style={{ 
                  background: 'none', border: 'none', color: 'var(--text-muted)', 
                  cursor: 'pointer', display: 'flex', alignItems: 'center' 
                }}
              >
                {copied ? <CheckCircle size={16} color="#4ade80" /> : <Copy size={16} />}
              </button>
            </div>
            
            <div style={{ padding: '24px', fontFamily: 'monospace', fontSize: '0.95rem', lineHeight: '1.8', color: 'var(--text-main)', wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
              <div><span style={{ color: 'var(--accent-purple-light)' }}>$</span> curl -sL https://raw.githubusercontent.com/PranavJa1n/Observo/main/install.sh | bash</div>
              <div style={{ color: 'var(--text-muted)', marginBottom: '12px' }}># 1. Download and install core binary</div>
              <div><span style={{ color: 'var(--accent-purple-light)' }}>$</span> observo init</div>
              <div style={{ color: 'var(--text-muted)', marginBottom: '12px' }}># 2. Interactively setup your local config</div>
              <div><span style={{ color: 'var(--accent-purple-light)' }}>$</span> observo start</div>
              <div style={{ color: 'var(--text-muted)' }}># 3. Monitor logs & serve dashboard</div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
