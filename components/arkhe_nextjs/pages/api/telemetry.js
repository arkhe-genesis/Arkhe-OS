export default async function handler(req, res) {
  try {
    // Proxy to Python Orchestrator (port 9080)
    const pythonRes = await fetch('http://localhost:9080/metrics');
    const data = await pythonRes.json();
    res.status(200).json({
      omega: data.omega.current_value,
      status: data.system.status,
      timestamp: Date.now()
    });
  } catch (e) {
    // Fallback if backend is not reachable during build/test
    res.status(200).json({ omega: 0.94, status: "OFFLINE_SIMULATION" });
  }
}
