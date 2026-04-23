
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Network, Server, Activity, Shield, Cpu } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useEffect, useState } from 'react';

interface Agent {
  id: string;
  type: string;
  capabilities: string[];
  pubkey: string;
  coherence: number;
  status: string;
  lastSeen: number;
  currentTaskId?: string;
}

interface Task {
  id: string;
  type: string;
  requiredCoherence: number;
  status: string;
  assignedTo?: string;
  createdAt: number;
}

export default function AgentManagementPanel() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskType, setNewTaskType] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      const [agentsRes, tasksRes] = await Promise.all([
        fetch('/api/agents'),
        fetch('/api/tasks')
      ]);
      const agentsData = await agentsRes.json();
      const tasksData = await tasksRes.json();
      setAgents(agentsData);
      setTasks(tasksData);
    } catch (error) {
      console.error('Failed to fetch agent data:', error);
    }
  };

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => {
      void fetchData();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateTask = async () => {
    if (!newTaskType) {return;}
    setLoading(true);
    try {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: newTaskType,
          payload: { instruction: 'Execute standard protocol' },
          requiredCoherence: 0.85
        })
      });
      setNewTaskType('');
      void fetchData();
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE': return 'text-amber-400';
      case 'TASK_IN_PROGRESS': return 'text-cyan-400';
      case 'TASK_COMPLETED': return 'text-emerald-400';
      case 'TASK_FAILED': return 'text-red-400';
      case 'OFFLINE': return 'text-gray-500';
      default: return 'text-arkhe-muted';
    }
  };

  return (
    <div className="bg-[#0a0a0c] border border-cyan-500/20 rounded-lg p-4 flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-cyan-500/20 pb-2">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-cyan-400" />
          <h2 className="font-mono text-sm uppercase tracking-widest text-cyan-400">
            Arkhe(n) Agent Management
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-arkhe-muted">
          <Server className="w-3 h-3" />
          <span>gRPC Sync Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Agents List */}
        <div className="space-y-3">
          <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
            <Cpu className="w-3 h-3" />
            Registered Agents ({agents.length})
          </h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
            {agents.length === 0 ? (
              <div className="text-center p-4 border border-dashed border-arkhe-border rounded text-arkhe-muted font-mono text-xs">
                No agents registered. Waiting for gRPC connections...
              </div>
            ) : (
              agents.map(agent => (
                <motion.div 
                  key={agent.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-[#111214] border border-arkhe-border rounded p-3"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-mono text-xs text-arkhe-text">{agent.id}</div>
                      <div className="font-mono text-[10px] text-cyan-500/70">{agent.type}</div>
                    </div>
                    <div className={`font-mono text-[10px] px-2 py-0.5 rounded border border-current ${getStatusColor(agent.status)}`}>
                      {agent.status}
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-3 pt-2 border-t border-arkhe-border/50">
                    <div className="flex items-center gap-1">
                      <Activity className="w-3 h-3 text-emerald-400" />
                      <span className="font-mono text-[10px] text-emerald-400">λΩ: {agent.coherence.toFixed(3)}</span>
                    </div>
                    <div className="font-mono text-[10px] text-arkhe-muted">
                      Last seen: {Math.floor((Date.now() - agent.lastSeen) / 1000)}s ago
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Tasks List */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="font-mono text-[10px] uppercase tracking-widest text-arkhe-muted flex items-center gap-2">
              <Shield className="w-3 h-3" />
              Task Queue ({tasks.length})
            </h3>
          </div>
          
          <div className="flex gap-2 mb-2">
            <input 
              type="text" 
              value={newTaskType}
              onChange={(e) => setNewTaskType(e.target.value)}
              placeholder="Task Type (e.g., 'DATA_ANALYSIS')"
              className="flex-1 bg-[#111214] border border-arkhe-border rounded px-2 py-1 font-mono text-xs text-arkhe-text focus:outline-none focus:border-cyan-500/50"
            />
            <button 
              onClick={handleCreateTask}
              disabled={!newTaskType || loading}
              className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded px-3 py-1 font-mono text-xs transition-colors disabled:opacity-50"
            >
              Dispatch
            </button>
          </div>

          <div className="space-y-2 max-h-[250px] overflow-y-auto custom-scrollbar pr-2">
            {tasks.length === 0 ? (
              <div className="text-center p-4 border border-dashed border-arkhe-border rounded text-arkhe-muted font-mono text-xs">
                Task queue empty.
              </div>
            ) : (
              tasks.slice().reverse().map(task => (
                <motion.div 
                  key={task.id}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-[#111214] border border-arkhe-border rounded p-2 flex items-center justify-between"
                >
                  <div className="flex flex-col">
                    <span className="font-mono text-xs text-arkhe-text">{task.type}</span>
                    <span className="font-mono text-[9px] text-arkhe-muted">{task.id}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className={`font-mono text-[10px] ${
                      task.status === 'COMPLETED' ? 'text-emerald-400' :
                      task.status === 'FAILED' ? 'text-red-400' :
                      task.status === 'ASSIGNED' ? 'text-cyan-400' : 'text-amber-400'
                    }`}>
                      {task.status}
                    </span>
                    {task.assignedTo && (
                      <span className="font-mono text-[9px] text-cyan-500/70">
                        Agent: {task.assignedTo.substring(0, 8)}...
                      </span>
                    )}
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
