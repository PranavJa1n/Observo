import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Terminal } from 'lucide-react';

function IncidentItem({ incident, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="glass-panel"
      style={{ marginBottom: '16px', overflow: 'hidden' }}
    >
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{ 
          padding: '24px', 
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transition: 'background 0.2s',
          backgroundColor: expanded ? 'var(--grid-color)' : 'transparent'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            background: 'var(--accent-purple-light)',
            boxShadow: '0 0 10px var(--accent-purple-light)'
          }} />
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-main)' }}>
              {incident.problem || "Anomaly Detected"}
            </h3>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              {new Date(incident.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <div>
          {expanded ? <ChevronUp color="var(--text-muted)" /> : <ChevronDown color="var(--text-muted)" />}
        </div>
      </div>
      
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', borderLeft: '3px solid var(--accent-blue)' }}>
                <strong style={{ color: 'var(--accent-blue)', display: 'block', marginBottom: '8px' }}>AI Summary</strong>
                <p style={{ lineHeight: 1.6, color: 'var(--text-main)' }}>{incident.ai_summary || "Analyzing anomaly patterns..."}</p>
              </div>

              <div style={{ background: 'var(--sub-panel-bg)', padding: '16px', borderRadius: '8px', borderLeft: '3px solid var(--accent-purple-light)' }}>
                <strong style={{ color: 'var(--accent-purple-light)', display: 'block', marginBottom: '8px' }}>Root Cause Analysis</strong>
                <p style={{ lineHeight: 1.6, color: 'var(--text-main)' }}>{incident.root_cause || "Pending deeper analysis..."}</p>
              </div>
              
              {incident.sample_logs && (
                <div style={{ background: 'var(--code-bg)', padding: '16px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--text-muted)' }}>
                    <Terminal size={16} /> Sample Logs
                  </div>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'var(--text-main)' }}>
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
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <h3 style={{ marginBottom: '12px', color: 'var(--text-main)' }}>No Active Incidents</h3>
        <p>Observo is monitoring your systems. Everything looks normal.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: '24px', fontSize: '1.5rem' }}>Recent Anomalies</h2>
      {incidents.map((incident, idx) => (
        <IncidentItem key={incident.id || idx} incident={incident} index={idx} />
      ))}
    </div>
  );
}
