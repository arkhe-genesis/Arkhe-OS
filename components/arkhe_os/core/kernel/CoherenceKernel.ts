// arkhe_os/core/kernel/CoherenceKernel.ts
import { SovereignIdentity } from '../root/SovereignIdentity.js';
import { GenesisState } from '../bios/GenesisState.js';
import { InferenceEngine } from './InferenceEngine.js';
import { CoherenceScheduler } from './CoherenceScheduler.js';
import { StateManager } from './StateManager.js';

export class CoherenceKernel {
  private sovereignIdentity: SovereignIdentity;
  private genesisState: GenesisState;
  private quantumHardware: any;
  private inferenceEngine: InferenceEngine;
  private scheduler: CoherenceScheduler;
  private stateManager: StateManager;
  private isRunning: boolean = false;

  constructor(
    sovereignIdentity: SovereignIdentity,
    genesisState: GenesisState,
    quantumHardware: any
  ) {
    this.sovereignIdentity = sovereignIdentity;
    this.genesisState = genesisState;
    this.quantumHardware = quantumHardware;
    this.inferenceEngine = new InferenceEngine(quantumHardware);
    this.scheduler = new CoherenceScheduler();
    this.stateManager = new StateManager();
  }

  /**
   * Inicializa o Kernel: Carrega Estado, Inicializa Motores
   */
  async initialize(): Promise<void> {
    console.log('[KERNEL] Initializing Coherence Kernel...');
    await this.stateManager.loadState(this.genesisState.statePath);
    await this.inferenceEngine.initialize();
    await this.scheduler.initialize();
    console.log('[KERNEL] Coherence Kernel initialized');
  }

  /**
   * Loop Principal: Executa enquanto Coerência > Threshold Crítico
   */
  async run(): Promise<void> {
    this.isRunning = true;
    console.log('[KERNEL] Starting Coherence Kernel Loop...');

    while (this.isRunning) {
      try {
        // 1. Obter Coerência Atual
        const currentCoherence = await this.getCurrentCoherence();

        // 2. Verificar Threshold Crítico
        if (currentCoherence < this.genesisState.criticalCoherenceThreshold) {
          console.warn('[KERNEL] Coherence below critical threshold, entering recovery mode...');
          await this.enterRecoveryMode();
          continue;
        }

        // 3. Agendar por Impacto de Coerência (não apenas prioridade)
        const task = await this.scheduler.nextByCoherenceImpact(currentCoherence);
        if (!task) {
          // Se não há tarefas, evoluir arquitetura
          await this.evolveArchitecture();
          await new Promise(resolve => setTimeout(resolve, this.genesisState.cycleIntervalMs));
          continue;
        }

        // 4. Executar Inferência
        const result = await this.inferenceEngine.execute(task);

        // 5. Atualizar Estado
        await this.stateManager.updateState(result.newState);

        // 6. Verificar Evolução
        if (result.coherenceImproved) {
          await this.evolveArchitecture();
        }

        // Esperar próximo ciclo
        await new Promise(resolve => setTimeout(resolve, this.genesisState.cycleIntervalMs));
      } catch (error) {
        console.error('[KERNEL] Error in kernel loop:', error);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    console.log('[KERNEL] Coherence Kernel stopped');
  }

  /**
   * Para o Kernel gracefulmente
   */
  async shutdown(reason: string): Promise<void> {
    console.log('[KERNEL] Shutting down Coherence Kernel...', { reason });
    this.isRunning = false;
    await this.stateManager.saveState();
    await this.inferenceEngine.shutdown();
    console.log('[KERNEL] Coherence Kernel shutdown complete');
  }

  // Métodos privados auxiliares
  private async getCurrentCoherence(): Promise<number> {
    // Obter coerência do estado atual (LFIR)
    return this.stateManager.getCoherence();
  }

  private async enterRecoveryMode(): Promise<void> {
    // Modo de recuperação: reverter estado, reinferir, evoluir
    await this.stateManager.revertToStableState();
    await this.inferenceEngine.recover();
    await this.evolveArchitecture();
  }

  private async evolveArchitecture(): Promise<void> {
    // Evoluir arquitetura de inferência (Substrate 308)
    await this.inferenceEngine.evolve();
  }
}
