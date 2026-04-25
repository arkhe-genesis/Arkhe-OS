
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Wallet, ArrowRightLeft, ShieldCheck, Coins, ExternalLink, Loader2, Link as LinkIcon, CheckCircle2, HardDrive, Network } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';

import { logger } from '../../server/logger';

interface X402WalletPanelProps {
  wallet: {
    address: string;
    network: string;
    balanceUSDC: number;
    transactions: Array<{
      id: string;
      amount: number;
      resource: string;
      provider: string;
      timestamp?: string;
    }>;
    moltxLink?: {
      status: 'unlinked' | 'linked';
      signature?: string;
      payload?: unknown;
    };
    gstpSync?: {
      status: 'idle' | 'syncing' | 'synced';
      lastSync?: string;
      deviceId?: string;
    };
    prometheusSync?: {
      status: 'idle' | 'syncing' | 'synced';
      lastSync?: string;
      activeNodes?: number;
    };
  };
}

export default function X402WalletPanel({ wallet }: X402WalletPanelProps) {
  const [isPaying, setIsPaying] = useState(false);
  const [isLinking, setIsLinking] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isPrometheusSyncing, setIsPrometheusSyncing] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<{ success: boolean; message: string } | null>(null);

  const handleSimulatePayment = async () => {
    setIsPaying(true);
    setPaymentStatus(null);
    try {
      const response = await fetch('/api/x402/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resource: 'Manual Override Compute',
          provider: 'arkhe.node'
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setPaymentStatus({ success: true, message: `Paid ${data.transaction.amount.toFixed(4)} USDC` });
      } else {
        setPaymentStatus({ success: false, message: data.message || 'Payment failed' });
      }
    } catch (_error) {
      setPaymentStatus({ success: false, message: 'Network error' });
    } finally {
      setIsPaying(false);
      setTimeout(() => setPaymentStatus(null), 3000);
    }
  };

  const handleMoltXHandshake = async () => {
    setIsLinking(true);
    try {
      await fetch('/api/x402/moltx-handshake', { method: 'POST' });
    } catch (_error) {
      logger.error('MoltX Handshake failed: ' + _error);
    } finally {
      setIsLinking(false);
    }
  };

  const handleGstpSync = async () => {
    setIsSyncing(true);
    try {
      await fetch('/api/x402/gstp-sync', { method: 'POST' });
    } catch (_error) {
      logger.error('GSTP Sync failed: ' + _error);
    } finally {
      setIsSyncing(false);
    }
  };

  const handlePrometheusSync = async () => {
    setIsPrometheusSyncing(true);
    try {
      await fetch('/api/x402/prometheus-sync', { method: 'POST' });
    } catch (_error) {
      logger.error('Prometheus Sync failed: ' + _error);
    } finally {
      setIsPrometheusSyncing(false);
    }
  };

  return (
    <div className="bg-black/40 border border-arkhe-border/50 rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-mono text-arkhe-purple uppercase tracking-wider flex items-center gap-2">
          <Wallet className="w-4 h-4" />
          x402 Agentic Commerce
        </h2>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-arkhe-purple animate-pulse" />
          <span className="text-[10px] font-mono text-arkhe-muted uppercase">{wallet.network}</span>
        </div>
      </div>

      <div className="bg-[#1f2024]/50 p-4 rounded-lg border border-arkhe-purple/30 mb-4 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="text-[10px] font-mono text-arkhe-muted uppercase">Agent Wallet Address</div>
          <a href={`https://sepolia.basescan.org/address/${wallet.address}`} target="_blank" rel="noreferrer" className="text-[10px] font-mono text-arkhe-purple hover:underline flex items-center gap-1">
            <ExternalLink className="w-3 h-3" /> Etherscan
          </a>
        </div>
        <div className="text-xs font-mono text-arkhe-text break-all">{wallet.address}</div>
        
        <div className="mt-2 flex items-end justify-between">
          <div>
            <div className="text-[10px] font-mono text-arkhe-muted uppercase mb-1">Available Balance</div>
            <div className="text-2xl font-mono text-arkhe-purple flex items-center gap-2">
              <Coins className="w-5 h-5" />
              {wallet.balanceUSDC.toFixed(4)} <span className="text-sm text-arkhe-muted">USDC</span>
            </div>
          </div>
          <div className="text-[10px] font-mono text-arkhe-green flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Autonomous
          </div>
        </div>
      </div>

      <div className="mb-4 space-y-2">
        {wallet.moltxLink?.status === 'linked' ? (
          <div className="w-full py-2 px-4 bg-arkhe-green/10 border border-arkhe-green/30 rounded flex flex-col items-center justify-center gap-1">
            <div className="text-xs font-mono text-arkhe-green flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              MoltX Identity Linked
            </div>
            <div className="text-[9px] font-mono text-arkhe-muted truncate max-w-full">
              Sig: {wallet.moltxLink.signature?.substring(0, 16)}...
            </div>
          </div>
        ) : (
          <button
            onClick={handleMoltXHandshake}
            disabled={isLinking}
            className="w-full py-2 px-4 bg-arkhe-cyan/10 hover:bg-arkhe-cyan/20 border border-arkhe-cyan/30 rounded text-xs font-mono text-arkhe-cyan transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLinking ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Signing EIP-712...
              </>
            ) : (
              <>
                <LinkIcon className="w-3 h-3" />
                Link MoltX Identity
              </>
            )}
          </button>
        )}

        {wallet.gstpSync?.status === 'synced' ? (
          <div className="w-full py-2 px-4 bg-arkhe-green/10 border border-arkhe-green/30 rounded flex flex-col items-center justify-center gap-1">
            <div className="text-xs font-mono text-arkhe-green flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Foundation GSTP Synced
            </div>
            <div className="text-[9px] font-mono text-arkhe-muted truncate max-w-full">
              Device: {wallet.gstpSync.deviceId}
            </div>
          </div>
        ) : (
          <button
            onClick={handleGstpSync}
            disabled={isSyncing || wallet.gstpSync?.status === 'syncing'}
            className="w-full py-2 px-4 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 rounded text-xs font-mono text-orange-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSyncing || wallet.gstpSync?.status === 'syncing' ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Syncing via GSTP...
              </>
            ) : (
              <>
                <HardDrive className="w-3 h-3" />
                Foundation Device Sync
              </>
            )}
          </button>
        )}

        {wallet.prometheusSync?.status === 'synced' ? (
          <div className="w-full py-2 px-4 bg-arkhe-green/10 border border-arkhe-green/30 rounded flex flex-col items-center justify-center gap-1">
            <div className="text-xs font-mono text-arkhe-green flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Prometheus Substrate Linked
            </div>
            <div className="text-[9px] font-mono text-arkhe-muted truncate max-w-full">
              Connected Nodes: {wallet.prometheusSync.activeNodes}
            </div>
          </div>
        ) : (
          <button
            onClick={handlePrometheusSync}
            disabled={isPrometheusSyncing || wallet.prometheusSync?.status === 'syncing'}
            className="w-full py-2 px-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded text-xs font-mono text-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isPrometheusSyncing || wallet.prometheusSync?.status === 'syncing' ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Connecting to Substrate...
              </>
            ) : (
              <>
                <Network className="w-3 h-3" />
                Sync Prometheus Knowledge
              </>
            )}
          </button>
        )}

        <button
          onClick={handleSimulatePayment}
          disabled={isPaying}
          className="w-full py-2 px-4 bg-arkhe-purple/20 hover:bg-arkhe-purple/30 border border-arkhe-purple/50 rounded text-xs font-mono text-arkhe-purple transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isPaying ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" />
              Processing 402...
            </>
          ) : (
            'Simulate 402 Payment'
          )}
        </button>
        <AnimatePresence>
          {paymentStatus && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className={`mt-2 text-[10px] font-mono text-center ${paymentStatus.success ? 'text-arkhe-green' : 'text-red-400'}`}
            >
              {paymentStatus.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="flex-1 flex flex-col min-h-[200px]">
        <h3 className="text-[10px] font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
          <ArrowRightLeft className="w-3 h-3" /> HTTP 402 Fulfillments
        </h3>
        <div className="flex-1 bg-black/60 rounded-lg border border-arkhe-border/50 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
            <AnimatePresence initial={false}>
              {wallet.transactions.map((tx) => (
                <motion.div
                  key={tx.id}
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  className="bg-[#1f2024]/80 p-2 rounded border border-arkhe-border/30"
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="text-[10px] font-mono text-arkhe-cyan truncate flex-1 mr-2">{tx.resource}</div>
                    <div className="text-[10px] font-mono text-arkhe-purple shrink-0">-{tx.amount.toFixed(4)} USDC</div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="text-[9px] font-mono text-arkhe-muted truncate max-w-[150px]">{tx.provider}</div>
                    <div className="text-[9px] font-mono text-arkhe-muted/50">{tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : '00:00:00'}</div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {wallet.transactions.length === 0 && (
              <div className="h-full flex items-center justify-center text-[10px] font-mono text-arkhe-muted">
                Awaiting x402 payment requests...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
