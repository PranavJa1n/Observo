import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Terminal, Copy, CheckCircle } from 'lucide-react';

export default function Installation() {
  const [copied, setCopied] = useState(false);
  const codeString = `go run cmd/main.go init\ngo run cmd/main.go start`;

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
            Observo doesn't require massive architecture shifts. Initialize the CLI in your application directory, provide your API key, and it instantly begins clustering.
          </p>
          
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-purple-light)' }} />
              Requires Go 1.21+ & Python 3.9+
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

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          style={{ flex: '1', minWidth: '300px' }}
        >
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
            
            <div style={{ padding: '24px', fontFamily: 'monospace', fontSize: '1rem', lineHeight: '1.8' }}>
              <div><span style={{ color: 'var(--accent-purple-light)' }}>$</span> go run cmd/main.go init</div>
              <div style={{ color: 'var(--text-muted)', marginBottom: '12px' }}># Interactively setup your local config</div>
              <div><span style={{ color: 'var(--accent-purple-light)' }}>$</span> go run cmd/main.go start</div>
              <div style={{ color: 'var(--text-muted)' }}># Monitor logs & serve dashboard</div>
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
