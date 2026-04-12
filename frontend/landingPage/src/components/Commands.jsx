import React from 'react';
import { motion } from 'framer-motion';
import { Terminal as TerminalIcon, ShieldCheck, Play, StopCircle, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

const commandList = [
  {
    cmd: "observo init",
    title: "Initialize Configuration",
    icon: <Settings color="var(--accent-purple-light)" size={24} />,
    desc: "Sets up your ~/.observo/config.json interactively. Prompts for your log path, email for alerts, and Google API Key for the LangGraph agent."
  },
  {
    cmd: "observo start",
    title: "Start Monitoring daemon",
    icon: <Play color="#4ade80" size={24} />,
    desc: "Starts the file-watcher on your targeted logs and spins up the Local Dashboard on port 6969. Use --daemon to push it into the background."
  },
  {
    cmd: "observo status",
    title: "Check System Health",
    icon: <ShieldCheck color="var(--accent-blue)" size={24} />,
    desc: "Instantly prints out whether the Go Daemon and Python Service are actively running and healthy on your machine."
  },
  {
    cmd: "observo stop",
    title: "Halt Execution",
    icon: <StopCircle color="#ff4b4b" size={24} />,
    desc: "Safely shuts down the background daemon and releases port 6969 and background file locks."
  }
];

export default function Commands({ isLightMode }) {
  return (
    <div style={{ minHeight: '80vh', padding: '100px 20px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '40px' }}>
        <Link to="/" style={{ color: 'var(--accent-purple-light)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
          ← Back to Home
        </Link>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <h1 style={{ fontSize: '3.5rem', marginBottom: '20px' }}>CLI <span className="text-gradient">Reference</span></h1>
        <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', marginBottom: '60px', maxWidth: '600px', lineHeight: '1.6' }}>
          Observo operates entirely through a lightweight Command Line Interface designed for speed and reliability.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {commandList.map((c, i) => (
            <motion.div 
              key={i} 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              className="glass-panel" 
              style={{ padding: '30px', display: 'flex', gap: '30px', alignItems: 'flex-start' }}
            >
              <div style={{ 
                background: 'var(--icon-bg)', 
                padding: '16px', 
                borderRadius: '12px',
                border: '1px solid var(--card-border)'
              }}>
                {c.icon}
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '1.4rem', marginBottom: '8px' }}>{c.title}</h3>
                <div style={{ 
                  background: 'var(--code-bg)', 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  padding: '8px 16px', 
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  color: 'var(--text-main)',
                  marginBottom: '16px',
                  border: '1px solid var(--card-border)'
                }}>
                  <TerminalIcon size={14} color="var(--text-muted)" /> {c.cmd}
                </div>
                <p style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>{c.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
