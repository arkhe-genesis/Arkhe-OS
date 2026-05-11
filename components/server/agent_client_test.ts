
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROTO_PATH = path.join(__dirname, 'deploy', 'grpc', 'agent_management.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const protoDescriptor = grpc.loadPackageDefinition(packageDefinition) as any;
const agentManagement = protoDescriptor.arkhe.agents.AgentManagement;

const client = new agentManagement('localhost:50052', grpc.credentials.createInsecure());

async function run() {
  console.log('Registering agent...');
  client.RegisterAgent({
    type: 'TEST_AGENT',
    capabilities: ['DATA_ANALYSIS', 'LOGGING'],
    pubkey: 'test_pubkey_123',
    coherence: 0.95
  }, (err: any, response: any) => {
    if (err) {
      console.error('Registration failed:', err);
      return;
    }
    console.log('Registration successful:', response);

    const sessionToken = response.session_token;

    console.log('Opening task stream...');
    const call = client.TaskStream();

    call.on('data', (task: any) => {
      console.log('Received task:', task);
      
      // Simulate task execution
      setTimeout(() => {
        console.log('Reporting task completion...');
        call.write({
          session_token: sessionToken,
          task_id: task.id,
          status: 'COMPLETED',
          result_payload: JSON.stringify({ success: true, data: 'Test result' }),
          coherence_delta: 0.01
        });
      }, 2000);
    });

    call.on('end', () => {
      console.log('Server ended the stream');
    });

    call.on('error', (e: any) => {
      console.error('Stream error:', e);
    });

    // Send initial status report
    call.write({
      session_token: sessionToken,
      task_id: '',
      status: 'IDLE',
      result_payload: '',
      coherence_delta: 0
    });

    // Keep alive
    setInterval(() => {
      call.write({
        session_token: sessionToken,
        task_id: '',
        status: 'IDLE',
        result_payload: '',
        coherence_delta: 0
      });
    }, 5000);
  });
}

run();
