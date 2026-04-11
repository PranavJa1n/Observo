import React, { useState, useEffect } from 'react';
import { useDashboardData } from './hooks/useDashboardData';
import Background3D from './components/Background3D';
import StatCard from './components/StatCard';
import IncidentList from './components/IncidentList';
import { Sun, Moon } from 'lucide-react';

function App() {
  const { stats, incidents, loading, error } = useDashboardData();
  const [isLightMode, setIsLightMode] = useState(false);

  useEffect(() => {
    if (isLightMode) {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
  }, [isLightMode]);

  // Handle UI gracefully if error occurs, no full page block


  return (
    <div style={{ minHeight: '100vh', padding: '40px 20px', position: 'relative' }}>
      <Background3D />
      
      <div style={{ maxWidth: '1200px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
        
        <header style={{ marginBottom: '48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="text-gradient" style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Observo</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
              AI-Powered Log Analysis Dashboard
              {error && <span style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '20px', background: 'rgba(255, 75, 75, 0.15)', color: '#ff6b6b', border: '1px solid rgba(255, 75, 75, 0.3)' }}>Backend Offline</span>}
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {loading && <div style={{ color: 'var(--accent-purple-light)' }}>Syncing...</div>}
            
            <button 
              onClick={() => setIsLightMode(!isLightMode)}
              style={{
                background: 'var(--card-bg)',
                border: '1px solid var(--card-border)',
                color: 'var(--text-main)',
                padding: '10px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
              }}
              title="Toggle Theme"
            >
              {isLightMode ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
        </header>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '24px',
          marginBottom: '48px' 
        }}>
          <StatCard 
            title="Daemon Status" 
            value={stats.running ? "Running" : "Stopped"} 
            type="daemon" 
            delay={0.1} 
          />
          <StatCard 
            title="Total Incidents" 
            value={stats.incidents_count || 0} 
            type="incidents" 
            delay={0.2} 
          />
          <StatCard 
            title="System Uptime" 
            value={stats.uptime_human || '0s'} 
            type="uptime" 
            delay={0.3} 
          />
        </div>

        <main>
          <IncidentList incidents={incidents} />
        </main>
        
      </div>
    </div>
  );
}

export default App;
