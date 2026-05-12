import React, { useEffect, useState } from 'react';
interface SophonStatus { id: string; uptime: number; lastAction: string; }

const SophonWidget: React.FC<{ agentId: string }> = ({ agentId }) => {
    const [status, setStatus] = useState<SophonStatus | null>(null);
    useEffect(() => {
        fetch(`/api/sophon/${agentId}`).then(r => r.json()).then(setStatus);
    }, [agentId]);
    return <div>Sophon {agentId}: {status?.lastAction}</div>;
};
export default SophonWidget;
