import { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export function useDashboardData() {
  const [stats, setStats] = useState({
    running: false,
    incidents_count: 0,
    uptime_seconds: 0,
    uptime_human: 'Unknown',
  });
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const [statsRes, incidentsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/stats`),
        fetch(`${API_BASE_URL}/api/incidents`)
      ]);
      
      if (!statsRes.ok || !incidentsRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const statsData = await statsRes.json();
      const incidentsData = await incidentsRes.json();

      setStats(statsData);
      setIncidents(incidentsData || []);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not connect to Observo backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return { stats, incidents, loading, error };
}
