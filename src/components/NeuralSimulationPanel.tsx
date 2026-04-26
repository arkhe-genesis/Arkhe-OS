import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from './ui';

const NeuralSimulationPanel: React.FC = () => {
  const [omega, setOmega] = useState(0.971);
  const [events, setEvents] = useState({ or: 0, spikes: 0 });
  const [status, setStatus] = useState<'STABLE' | 'DRIFTING' | 'CALIBRATING'>('STABLE');
  const [baseline, setBaseline] = useState<number | null>(null);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [calibrationProgress, setCalibrationProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulação visual de oscilação
      const target = baseline || 0.971;
      const newOmega = target + (Math.random() - 0.5) * 0.01;
      setOmega(newOmega);
      setEvents(prev => ({
        or: prev.or + Math.floor(Math.random() * 5),
        spikes: prev.spikes + Math.floor(Math.random() * 3)
      }));
      if (!isCalibrating) {
        setStatus(Math.abs(target - newOmega) > 0.005 ? 'DRIFTING' : 'STABLE');
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [baseline, isCalibrating]);

  const startCalibration = () => {
    setIsCalibrating(true);
    setStatus('CALIBRATING');
    setCalibrationProgress(0);

    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      setCalibrationProgress(progress);
      if (progress >= 100) {
        clearInterval(interval);
        setIsCalibrating(false);
        const newBaseline = 0.95 + Math.random() * 0.04;
        setBaseline(newBaseline);
        setStatus('STABLE');
      }
    }, 200);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>🧠 Interface de Coerência Neural (FS-180.5)</CardTitle>
            <Badge variant={status === 'STABLE' ? 'outline' : 'destructive'}>{status}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Atrator de Coerência (Ω)</span>
              <span className="font-mono text-arkhe-cerenkov">{omega.toFixed(4)}</span>
            </div>
            <Progress value={omega * 100} color={status === 'DRIFTING' ? 'amber' : 'cerenkov'} />
          </div>

          {baseline && (
            <div className="p-3 bg-white/5 border border-arkhe-border rounded-md text-xs font-mono">
              <span className="text-arkhe-muted">BASELINE INDIVIDUAL:</span>
              <span className="ml-2 text-arkhe-omega">{baseline.toFixed(4)}</span>
            </div>
          )}

          {isCalibrating && (
            <div className="space-y-1">
              <div className="text-[10px] uppercase text-arkhe-muted font-mono">Calibração em curso...</div>
              <Progress value={calibrationProgress} color="cyan" />
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-black/20 rounded-lg border border-white/5">
              <div className="text-[10px] text-muted-foreground uppercase font-mono">Eventos OR (Penrose)</div>
              <div className="text-2xl font-bold text-arkhe-cyan">{events.or}</div>
            </div>
            <div className="p-4 bg-black/20 rounded-lg border border-white/5">
              <div className="text-[10px] text-muted-foreground uppercase font-mono">Spikes LIF (Neural)</div>
              <div className="text-2xl font-bold text-arkhe-cerenkov">{events.spikes}</div>
            </div>
          </div>

          <div className="border-t border-arkhe-border pt-4">
            <div className="text-sm font-semibold mb-3 font-mono">Controle de Biofeedback</div>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" disabled={isCalibrating} onClick={startCalibration}>
                {baseline ? 'Recalibrar' : 'Calibração Individual'}
              </Button>
              <Button size="sm" variant="outline" disabled={isCalibrating || !baseline}>
                Estabilizar Atrator
              </Button>
              <Button size="sm" variant="outline" disabled={isCalibrating} className="text-arkhe-fissure border-arkhe-fissure/30">
                Emergência
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NeuralSimulationPanel;
