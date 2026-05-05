const fs = require('fs');

function wipeComponent(filepath) {
    fs.writeFileSync(filepath, `import React from 'react';\nexport default function Component() { return <div />; }\n`);
}

function wipeHook(filepath) {
    fs.writeFileSync(filepath, `export function useArkheSimulation() { return {}; }\n`);
}

wipeComponent('src/components/TemporalStreamViewer.tsx');
wipeComponent('src/components/ClusterOrchestrationPanel.tsx');
wipeComponent('src/components/CorvoNoirDashboard.tsx');
wipeComponent('src/components/DimOSDistributionPanel.tsx');
wipeComponent('src/components/GovernanceManifestoPanel.tsx');
wipeComponent('src/components/HelioLinkPanel.tsx');
wipeComponent('src/components/SessionReplayViewer.tsx');
wipeComponent('src/components/X402WalletPanel.tsx');
wipeHook('src/hooks/useArkheSimulation.ts');
