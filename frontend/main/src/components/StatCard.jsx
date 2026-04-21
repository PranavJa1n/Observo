import React from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Clock } from 'lucide-react';

const iconMap = {
  incidents: <AlertTriangle size={22} color="#f59e0b" />,
  uptime:    <Clock size={22} color="#94a3b8" />,
  daemon:    <Activity size={22} color="#22c55e" />,
};

const accentMap = {
  incidents: '#f59e0b',
  uptime:    '#94a3b8',
  daemon:    '#22c55e',
};

export default function StatCard({ title, value, type, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="glass-panel"
      style={{ padding: '28px 24px', display: 'flex', alignItems: 'center', gap: '20px' }}
    >
      <div style={{
        background: 'var(--icon-bg)',
        width: '48px', height: '48px',
        borderRadius: '12px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px solid var(--card-border)',
        flexShrink: 0,
      }}>
        {iconMap[type]}
      </div>
      <div>
        <div style={{
          color: 'var(--text-muted)', fontSize: '0.78rem',
          marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.08em'
        }}>
          {title}
        </div>
        <div style={{
          fontSize: '1.9rem', fontWeight: 700,
          letterSpacing: '-0.03em',
          color: accentMap[type] || 'var(--text-main)'
        }}>
          {value}
        </div>
      </div>
    </motion.div>
  );
}
