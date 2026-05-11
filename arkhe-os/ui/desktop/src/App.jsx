import { useEffect, useState } from 'react'

function App() {
  const [coherence, setCoherence] = useState(null);
  const [kymChallenge, setKymChallenge] = useState(null);
  const [deployResult, setDeployResult] = useState(null);

  useEffect(() => {
    // Fetch Coherence
    const fetchCoherence = () => {
      fetch('/api/coherence')
        .then(r => r.json())
        .then(data => setCoherence(data))
        .catch(console.error);
    };
    fetchCoherence();
    const interval = setInterval(fetchCoherence, 5000);

    // Fetch KYM Challenge
    fetch('/api/kym/challenge')
      .then(r => r.json())
      .then(data => setKymChallenge(data.challenge))
      .catch(console.error);

    return () => clearInterval(interval);
  }, []);

  const handleDeploy = () => {
    fetch('/api/contract/deploy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: "intention { evolve } "})
    })
    .then(r => r.json())
    .then(setDeployResult)
    .catch(console.error);
  };

  return (
    <div>
      <h1>Arkhe OS Nexus</h1>

      <div className="card">
        <h2>Substrate 344: Coherence Engine</h2>
        {coherence ? (
          <div>
            <p><strong>Φ_C:</strong> {coherence.phi_c.toFixed(4)}</p>
            <p><strong>Status:</strong> {coherence.status}</p>
          </div>
        ) : <p>Loading...</p>}
      </div>

      <div className="card">
        <h2>Substrate 5006: KYM Identity</h2>
        <p>Current Challenge: <code>{kymChallenge || 'Loading...'}</code></p>
      </div>

      <div className="card">
        <h2>Substrate 321: LFIR Engine</h2>
        <button onClick={handleDeploy}>Deploy Mock Contract</button>
        {deployResult && (
          <pre style={{marginTop: '1rem', background: '#000', padding: '1rem'}}>
            {JSON.stringify(deployResult, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}

export default App
