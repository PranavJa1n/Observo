import React from 'react';
import { motion } from 'framer-motion';
import { Layers, Brain, Lock } from 'lucide-react';

const features = [
  {
    icon: <Layers size={32} color="var(--accent-blue)" />,
    title: 'Intelligent Clustering',
    desc: 'Using HDBSCAN and semantic embeddings, chaotic log streams are automatically grouped into stable, readable patterns without any manual Regex configuration.'
  },
  {
    icon: <Brain size={32} color="var(--accent-purple-light)" />,
    title: 'LangGraph AI Analysis',
    desc: 'When an anomaly is detected, our Multi-Stage AI Agent kicks in. It reads the bad logs and instantly generates English summaries, root causes, and fix steps.'
  },
  {
    icon: <Lock size={32} color="#4ade80" />,
    title: 'Local Privacy-First',
    desc: 'Observo watches your local directories directly. It only sends highly-specific anomalous clusters to the AI, saving you massive API costs and protecting normal logs.'
  }
];

export default function Features() {
  return (
    <section>
      <div style={{ textAlign: 'center', marginBottom: '60px' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '16px' }}>Why Observo?</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
          Stop wasting hours digging through endless application logs during incidents.
        </p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '30px' 
      }}>
        {features.map((feat, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: idx * 0.2 }}
            className="glass-panel"
            style={{ padding: '40px 30px' }}
          >
            <div style={{ 
              width: '64px', height: '64px', 
              borderRadius: '16px',
              background: 'var(--icon-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: '24px',
              border: '1px solid var(--card-border)'
            }}>
              {feat.icon}
            </div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '16px' }}>{feat.title}</h3>
            <p style={{ color: 'var(--text-muted)', lineHeight: '1.6' }}>{feat.desc}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
