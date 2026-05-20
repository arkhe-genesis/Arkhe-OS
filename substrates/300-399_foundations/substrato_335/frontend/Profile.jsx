// Profile.jsx — Perfil do Pesquisador
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';

const Profile = ({ identity, phiCHistory }) => {
  const data = phiCHistory.map((phi, index) => ({ day: index + 1, phi_c: phi }));

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Cabeçalho */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6" style={{ backgroundColor: '#C3C3E5' }}>
        <div className="flex items-center space-x-4">
          <img src="/avatar-placeholder.png" alt="avatar" className="w-24 h-24 rounded-full border-4 border-white shadow" />
          <div>
            <h1 className="text-3xl font-bold" style={{ color: '#6A5ACD' }}>{identity.display_name}</h1>
            <p className="text-gray-600">{identity.institution}</p>
            <p className="text-sm text-gray-500">ORCID: {identity.orcid}</p>
          </div>
        </div>
        <div className="mt-4 flex space-x-8">
          <div className="text-center">
            <span className="block text-2xl font-bold">{identity.contributions?.filter(c => c.type === 'paper').length || 0}</span>
            <span className="text-sm text-gray-600">Papers</span>
          </div>
          <div className="text-center">
            <span className="block text-2xl font-bold">{identity.reputation_score.toFixed(1)}</span>
            <span className="text-sm text-gray-600">Reputação</span>
          </div>
        </div>
      </div>

      {/* Gráfico de Φ_C */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-xl font-bold mb-4" style={{ color: '#6A5ACD' }}>Evolução da Coerência (Φ_C)</h2>
        <LineChart width={600} height={300} data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis domain={[0.5, 0.8]} />
          <Tooltip />
          <ReferenceLine y={0.577553} stroke="#FF7043" strokeDasharray="3 3" label="Ghost (√3/3)" />
          <Line type="monotone" dataKey="phi_c" stroke="#6A5ACD" strokeWidth={2} dot={false} />
        </LineChart>
      </div>

      {/* Comunidades */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4" style={{ color: '#6A5ACD' }}>Comunidades</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg hover:shadow-md transition">
            <h3 className="font-semibold">Biofotônica & Luciferase</h3>
            <p className="text-sm text-gray-500">238 membros</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg hover:shadow-md transition">
            <h3 className="font-semibold">Quantum Consciousness</h3>
            <p className="text-sm text-gray-500">512 membros</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg hover:shadow-md transition">
            <h3 className="font-semibold">Arkhe Constitutional Math</h3>
            <p className="text-sm text-gray-500">189 membros</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
