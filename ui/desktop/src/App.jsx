import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [coherence, setCoherence] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCoherence();
    const interval = setInterval(fetchCoherence, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchCoherence = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/coherence');
      setCoherence(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch coherence:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Initializing Arkhe OS...</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🏛️ Arkhe OS - Nexus Dashboard</h1>
      </header>

      <main className="main">
        <div className="coherence-ring">
          <div className="ring">
            <div className="phi-c-display">
              Φ_C: {coherence?.phi_c?.toFixed(3) || 'N/A'}
            </div>
            <div className="status">
              Status: {coherence?.status || 'Unknown'}
            </div>
          </div>
        </div>

        <div className="metrics">
          <h2>System Metrics</h2>
          <div className="metric-grid">
            <div className="metric">
              <label>System Health</label>
              <value>{coherence?.metrics?.system_health?.toFixed(2) || 'N/A'}</value>
            </div>
            <div className="metric">
              <label>User Actions</label>
              <value>{coherence?.metrics?.user_actions?.toFixed(2) || 'N/A'}</value>
            </div>
            <div className="metric">
              <label>Network Consensus</label>
              <value>{coherence?.metrics?.network_consensus?.toFixed(2) || 'N/A'}</value>
            </div>
            <div className="metric">
              <label>AI Alignment</label>
              <value>{coherence?.metrics?.ai_alignment?.toFixed(2) || 'N/A'}</value>
            </div>
          </div>
        </div>

        <div className="navigation">
          <button className="nav-button">📱 Social Feed</button>
          <button className="nav-button">📺 IPTV Viewer</button>
          <button className="nav-button">📝 Contract Editor</button>
          <button className="nav-button">👤 Identity & Wallet</button>
        </div>
      </main>
    </div>
  );
}

export default App;