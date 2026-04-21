import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Terminal, AlertCircle } from 'lucide-react';

function IncidentItem({ incident, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className="glass-panel"
      style={{ marginBottom: '12px', overflow: 'hidden' }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '20px 24px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transition: 'background 0.2s',
          backgroundColor: expanded ? 'rgba(255,255,255,0.02)' : 'transparent',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: '#f59e0b',
            boxShadow: '0 0 8px rgba(245,158,11,0.5)',
            flexShrink: 0,
          }} />
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', lineHeight: 1.4 }}>
              {incident.problem || 'Anomaly Detected'}
            </h3>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              {new Date(incident.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <div style={{ color: '#3a3a3a', flexShrink: 0 }}>
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '16px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>

              <div style={{ height: '16px' }} />

              <div style={{ background: '#0d0d0d', padding: '16px 18px', borderRadius: '10px', borderLeft: '2px solid #94a3b8' }}>
                <strong style={{ color: '#94a3b8', display: 'block', marginBottom: '8px', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  AI Summary
                </strong>
                <p style={{ lineHeight: 1.65, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                  {incident.ai_summary || 'Analyzing anomaly patterns...'}
                </p>
              </div>

              <div style={{ background: '#0d0d0d', padding: '16px 18px', borderRadius: '10px', borderLeft: '2px solid #f59e0b' }}>
                <strong style={{ color: '#f59e0b', display: 'block', marginBottom: '8px', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Root Cause Analysis
                </strong>
                <p style={{ lineHeight: 1.65, color: 'var(--text-main)', fontSize: '0.95rem' }}>
                  {incident.root_cause || 'Pending deeper analysis...'}
                </p>
              </div>

              {incident.sample_logs && (
                <div style={{ background: '#0d0d0d', padding: '16px 18px', borderRadius: '10px', fontFamily: 'monospace', fontSize: '0.82rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--text-muted)' }}>
                    <Terminal size={14} /> Sample Logs
                  </div>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: '#71717a', lineHeight: 1.7 }}>
                    {incident.sample_logs}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function IncidentList({ incidents }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <div style={{
          width: '48px', height: '48px', borderRadius: '12px',
          background: 'var(--icon-bg)', border: '1px solid var(--card-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 16px',
        }}>
          <AlertCircle size={22} color="var(--text-muted)" />
        </div>
        <h3 style={{ marginBottom: '8px', color: 'var(--text-main)', fontSize: '1rem', fontWeight: 600 }}>
          No Active Incidents
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Observo is monitoring your systems. Everything looks normal.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: '20px', fontSize: '1.2rem', color: 'var(--text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Recent Anomalies
      </h2>
      {incidents.map((incident, idx) => (
        <IncidentItem key={incident.id || idx} incident={incident} index={idx} />
      ))}
    </div>
  );
}
