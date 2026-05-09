// dashboard/verified_interpretation.js
async function requestVerifiedInterpretation(metrics, proofHash) {
  const response = await fetch('/api/interpret', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      metrics: metrics,
      proof_hash: proofHash,
      context: "User requested poetic interpretation of current manifold state."
    })
  });

  const result = await response.json();

  // Display with verification badge
  const badge = result.proof_verified ? '🟢 Verified' : '🟡 Unverified';
  document.getElementById('interpretation').innerHTML = `
    <div class="proof-badge">${badge}</div>
    <div class="llm-response">${result.interpretation}</div>
    <div class="proof-ref">Proof: <code>${result.proof_hash}</code></div>
  `;
}
