
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';


import { logger } from './logger';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROTO_PATH = path.join(__dirname, 'deploy', 'grpc', 'agent_management.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
const agentProto = protoDescriptor.arkhe.agents;

// In-memory state for agents and tasks
export const agentsState = new Map<string, any>();
export const tasksState = new Map<string, any>();

export function startAgentGrpcServer() {
  const server = new grpc.Server();

  server.addService(agentProto.AgentManagement.service, {
    RegisterAgent: (call: any, callback: any) => {
      const req = call.request;
      logger.info(`[gRPC] RegisterAgent called for ${req.agent_id} (${req.agent_type})`);
      
      const sessionToken = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      
      agentsState.set(req.agent_id, {
        id: req.agent_id,
        type: req.agent_type,
        capabilities: req.capabilities,
        pubkey: req.pubkey,
        sessionToken,
        coherence: 0.95,
        status: 'IDLE',
        lastSeen: Date.now()
      });

      callback(null, {
        success: true,
        session_token: sessionToken,
        initial_coherence: 0.95,
        message: "Agent registered successfully in Arkhe(n) network."
      });
    },

    TaskStream: (call: any) => {
      let agentId: string | null = null;

      call.on('data', (report: any) => {
        agentId = report.agent_id;
        const agent = agentsState.get(report.agent_id);
        
        if (!agent || agent.sessionToken !== report.session_token) {
          logger.warn(`[gRPC] Unauthorized TaskStream from ${report.agent_id}`);
          return;
        }

        // Update agent state
        agent.coherence = report.coherence;
        agent.status = report.status;
        agent.lastSeen = Date.now();
        agent.currentTaskId = report.current_task_id;

        logger.info(`[gRPC] Status report from ${agentId}: ${report.status}, Coherence: ${report.coherence}`);

        if (report.logs) {
          logger.info(`[gRPC] Agent ${agentId} logs: ${report.logs}`);
        }

        // If task completed or failed, update task state
        if (report.current_task_id && (report.status === 'TASK_COMPLETED' || report.status === 'TASK_FAILED')) {
          const task = tasksState.get(report.current_task_id);
          if (task) {
            task.status = report.status;
            task.result = report.result_payload;
          }
        }
      });

      call.on('end', () => {
        if (agentId) {
          const agent = agentsState.get(agentId);
          if (agent) {agent.status = 'OFFLINE';}
        }
        call.end();
      });

      // Periodically send tasks to the agent
      const interval = setInterval(() => {
        if (!agentId) {return;}
        const agent = agentsState.get(agentId);
        if (!agent || agent.status !== 'TASK_IDLE') {return;}

        // Find a pending task for this agent
        for (const [taskId, task] of tasksState.entries()) {
          if (task.status === 'PENDING' && (!task.assignedTo || task.assignedTo === agentId)) {
            task.status = 'ASSIGNED';
            task.assignedTo = agentId;
            
            call.write({
              task_id: taskId,
              task_type: task.type,
              payload: task.payload || Buffer.from(''),
              required_coherence: task.requiredCoherence || 0.8,
              deadline_ns: task.deadlineNs || 0
            });
            break;
          }
        }
      }, 2000);

      call.on('cancelled', () => {
        clearInterval(interval);
      });
    }
  });

  const port = '0.0.0.0:50052';
  server.bindAsync(port, grpc.ServerCredentials.createInsecure(), (err, boundPort) => {
    if (err) {
      logger.error(`[gRPC] Failed to bind server: ${err}`);
      return;
    }
    server.start();
    logger.info(`[gRPC] Agent Management Server running on ${port}`);
  });
}

// Helper to create a task
export function createTask(type: string, payload: any, requiredCoherence = 0.8) {
  const taskId = `task_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  tasksState.set(taskId, {
    id: taskId,
    type,
    payload: Buffer.from(JSON.stringify(payload)),
    requiredCoherence,
    status: 'PENDING',
    createdAt: Date.now()
  });
  return taskId;
}
