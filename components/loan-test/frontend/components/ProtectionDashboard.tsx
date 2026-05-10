import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface ProtectionDashboardProps {
  healthFactor: number;
  riskTimestamp: number; // In seconds
}

const ProtectionDashboard: React.FC<ProtectionDashboardProps> = ({ healthFactor, riskTimestamp }) => {
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const GRACE_PERIOD = 24 * 60 * 60; // 24 hours in seconds

  useEffect(() => {
    const timer = setInterval(() => {
      if (riskTimestamp > 0) {
        const now = Math.floor(Date.now() / 1000);
        const elapsed = now - riskTimestamp;
        const remaining = GRACE_PERIOD - elapsed;
        setTimeLeft(remaining > 0 ? remaining : 0);
      } else {
        setTimeLeft(0);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [riskTimestamp]);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h} hours ${m} mins ${s} secs`;
  };

  const getStatus = () => {
    if (healthFactor >= 1.0) {
      return {
        label: 'Equity Secure',
        color: 'text-emerald-500',
        bgColor: 'bg-emerald-500/10',
        borderColor: 'border-emerald-500/20',
        icon: <CheckCircle className="w-6 h-6 text-emerald-500" />,
        status: 'green'
      };
    } else if (timeLeft > 0) {
      return {
        label: 'Safety Net Active',
        color: 'text-amber-500',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/20',
        icon: <AlertTriangle className="w-6 h-6 text-amber-500" />,
        status: 'yellow'
      };
    } else {
      return {
        label: 'Protection Expired',
        color: 'text-red-500',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/20',
        icon: <Shield className="w-6 h-6 text-red-500" />,
        status: 'red'
      };
    }
  };

  const status = getStatus();

  return (
    <div className={`p-6 rounded-xl border ${status.borderColor} ${status.bgColor} space-y-4 font-sans max-w-md`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {status.icon}
          <div>
            <h3 className={`text-lg font-bold tracking-tight ${status.color}`}>
              {status.label}
            </h3>
            <p className="text-neutral-500 text-xs uppercase tracking-widest font-mono">
              Neverland Protection Protocol
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-neutral-500 uppercase tracking-widest font-mono">Health Factor</p>
          <p className={`text-xl font-bold font-mono ${status.color}`}>
            {healthFactor.toFixed(4)}
          </p>
        </div>
      </div>

      {status.status === 'yellow' && (
        <div className="bg-black/20 p-4 rounded-lg border border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
            <span className="text-sm font-medium text-amber-200">Liquidation Protected</span>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-amber-500/70 uppercase tracking-widest font-mono">Remaining</p>
            <p className="text-sm font-bold text-amber-100 font-mono">
              {formatTime(timeLeft)}
            </p>
          </div>
        </div>
      )}

      {status.status === 'red' && (
        <div className="bg-red-500/20 p-3 rounded border border-red-500/30">
          <p className="text-xs text-red-200 leading-relaxed">
            <strong>Warning:</strong> Your asset is no longer protected. Add collateral or repay debt immediately to avoid liquidation.
          </p>
        </div>
      )}

      <div className="pt-2">
        <p className="text-[10px] text-neutral-500 italic leading-snug">
          "Protecting asset ownership and preventing displacement during temporary market dips."
        </p>
      </div>
    </div>
  );
};

export default ProtectionDashboard;
