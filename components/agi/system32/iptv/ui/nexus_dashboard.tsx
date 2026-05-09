// nexus_dashboard.tsx — Interface Nexus para IPTV Soberano
// Integra com Substrato 5003 (Nexus UI)
import { useEffect, useState } from "react";
import { useNexusAPI } from "@arkhe/nexus-sdk";

export default function IPTVDashboard() {
  const [channels, setChannels] = useState([]);
  const api = useNexusAPI();

  useEffect(() => {
    api.discoverIPTVChannels().then(setChannels);
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
      {channels.map((ch) => (
        <div key={ch.id} className="p-4 border rounded bg-gray-900 text-white">
          <h3 className="font-bold">{ch.title}</h3>
          <div className="flex items-center mt-2">
            <span className="text-yellow-400">Φ-REP: {ch.phi_rep.toFixed(2)}</span>
            <span className="ml-3 text-sm">👁 {ch.viewers} assistindo</span>
          </div>
          <button
            onClick={() => api.joinStream(ch.id)}
            className="mt-3 px-4 py-1 bg-blue-600 rounded hover:bg-blue-500"
          >
            Assistir
          </button>
        </div>
      ))}
    </div>
  );
}
