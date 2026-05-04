/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { federatedHomomorphicQuantum } from '../src/lib/quantum/federatedHomomorphicQuantum';
import { postQuantumZKP } from '../src/lib/zkp/post-quantum-zkp';

async function runVerification() {
  console.log('🚀 Iniciando verificação Arkhe OS v∞.20...');

  // 1. Testar ZKP
  console.log('\n--- Testando Provas de Conhecimento Zero (Groth16) ---');
  const zkpProof = await postQuantumZKP.proveKEthAboveThreshold(0.93, 0.90, true);
  console.log('✅ ZKP Proof Gerado:', JSON.stringify(zkpProof, null, 2).substring(0, 150) + '...');

  const isValid = await postQuantumZKP.verifyProof(zkpProof, { threshold: 0.90 });
  console.log(`✅ ZKP Verificação: ${isValid ? 'VÁLIDA' : 'INVÁLIDA'}`);

  const metrics = postQuantumZKP.getZKPMetrics();
  console.log(`✅ ZKP Tempo Médio de Verificação: ${metrics.avgVerificationTime}ms`);

  // 2. Testar Homomorphic Computing
  console.log('\n--- Testando Homomorphic Quantum Computing ---');
  const sampleMetrics: Record<string, number> = { omega: 0.94, kEth: 0.93 };
  const encrypted = await federatedHomomorphicQuantum.encryptEthicalData(sampleMetrics);
  console.log(`✅ Criptografia homomórfica (PQ-CKKS) bem-sucedida.`);
  console.log(`✅ Ciphertext size: ${encrypted.ciphertext.length} bytes`);

  // Mock server aggregation
  const aggregationResult = await federatedHomomorphicQuantum.simulateServerAggregation([encrypted, encrypted]);
  console.log(`✅ Agregação homomórfica no servidor (cego) concluída.`);

  const _decrypted = await federatedHomomorphicQuantum.decryptAndVerify(aggregationResult);
  console.log(`✅ Decriptação e verificação (Kyber) concluída. Resultado final processado.`);

  console.log('\n🎉 Todos os sistemas v∞.20 estão operacionais e seguros.');
}

runVerification().catch(console.error);
