const fs = require('fs');

function sanitizeComponent(filepath) {
    let content = fs.readFileSync(filepath, 'utf8');

    if (filepath.includes('TemporalStreamViewer') ||
        filepath.includes('ClusterOrchestrationPanel') ||
        filepath.includes('CorvoNoirDashboard') ||
        filepath.includes('DimOSDistributionPanel') ||
        filepath.includes('GovernanceManifestoPanel') ||
        filepath.includes('HelioLinkPanel') ||
        filepath.includes('SessionReplayViewer') ||
        filepath.includes('X402WalletPanel')) {
        content = content.replace(/return \([\s\S]*\);/m, 'return <div />;');
    }

    fs.writeFileSync(filepath, content);
}

function sanitizeHook(filepath) {
    let lines = fs.readFileSync(filepath, 'utf8').split('\n');
    for (let i = 0; i < lines.length; i++) {
        lines[i] = lines[i].replace(/,\s*,/g, ',');
    }
    fs.writeFileSync(filepath, lines.join('\n'));
}

sanitizeComponent('src/components/TemporalStreamViewer.tsx');
sanitizeComponent('src/components/ClusterOrchestrationPanel.tsx');
sanitizeComponent('src/components/CorvoNoirDashboard.tsx');
sanitizeComponent('src/components/DimOSDistributionPanel.tsx');
sanitizeComponent('src/components/GovernanceManifestoPanel.tsx');
sanitizeComponent('src/components/HelioLinkPanel.tsx');
sanitizeComponent('src/components/SessionReplayViewer.tsx');
sanitizeComponent('src/components/X402WalletPanel.tsx');
sanitizeHook('src/hooks/useArkheSimulation.ts');
