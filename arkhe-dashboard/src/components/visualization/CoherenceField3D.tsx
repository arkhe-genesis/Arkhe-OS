// arkhe-dashboard/src/components/visualization/CoherenceField3D.tsx
'use client';
import dynamic from 'next/dynamic';

const ArkheCore3D = dynamic(() => import('../ArkheCore3D'), { ssr: false });

export function CoherenceField3D({ omega, kEth }: { omega: number; kEth: number; quantumFidelity: number }) {
  return (
    <div className="w-full h-full min-h-[400px] relative">
      <ArkheCore3D omega={omega} kEth={kEth} />
    </div>
  );
}
