const fs = require('fs');

// CHSHMonitorPanel
let chsh = fs.readFileSync('src/components/CHSHMonitorPanel.tsx', 'utf8');
chsh = chsh.replace("const state = useArkheSimulation();\n  const chsh = state.chshMonitor;", "");
fs.writeFileSync('src/components/CHSHMonitorPanel.tsx', chsh, 'utf8');

// DataCoherenceDashboard
let dcd = fs.readFileSync('src/components/DataCoherenceDashboard.tsx', 'utf8');
dcd = dcd.replace('domain =>', '(domain: any) =>');
dcd = dcd.replace('(log, i)', '(log: any, i: any)');
fs.writeFileSync('src/components/DataCoherenceDashboard.tsx', dcd, 'utf8');

// UnifiedConsciousnessPanel
let ucp = fs.readFileSync('src/components/UnifiedConsciousnessPanel.tsx', 'utf8');
ucp = ucp.replace('q =>', '(q: any) =>');
fs.writeFileSync('src/components/UnifiedConsciousnessPanel.tsx', ucp, 'utf8');
