import React from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Clock } from 'lucide-react';

const iconMap = {
  incidents: <AlertTriangle size={24} color="var(--accent-purple-light)" />,
  uptime: <Clock size={24} color="var(--accent-blue)" />,
  daemon: <Activity size={24} color="#4ade80" />
};

export default function StatCard({ title, value, type, delay = 0 }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="glass-panel"
      style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '20px' }}
    >
      <div style={{
        background: 'var(--icon-bg)',
        padding: '16px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {iconMap[type]}
      </div>
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
          {title}
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold' }} className="text-gradient">
          {value}
        </div>
      </div>
    </motion.div>
  );
}
