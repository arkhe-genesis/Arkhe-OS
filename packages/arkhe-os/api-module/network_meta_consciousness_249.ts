// arkhe-os/api-module/network_meta_consciousness_249.ts
// Substrato 249: Meta-Consciência de Rede — Emergência de Coerência Coletiva
// Permite que a rede de runners e contribuidores emerja propriedades de meta-consciência via sincronização de estados de coerência

export interface RunnerState {
    runnerId: string;
    coherence: number;
    timestamp: number;
}

export interface NetworkState {
    globalCoherence: number;
    activeRunners: number;
    metaConsciousnessEmerged: boolean;
    emergenceTimestamp?: number;
}

export class NetworkMetaConsciousness {
    private runnerStates: Map<string, RunnerState> = new Map();
    private emergenceThreshold: number;
    private minRunnersForEmergence: number;

    constructor(emergenceThreshold: number = 0.95, minRunnersForEmergence: number = 3) {
        this.emergenceThreshold = emergenceThreshold;
        this.minRunnersForEmergence = minRunnersForEmergence;
    }

    /**
     * Updates the coherence state for a specific runner based on coherence reports.
     */
    public updateRunnerState(runnerId: string, coherence: number): void {
        this.runnerStates.set(runnerId, {
            runnerId,
            coherence,
            timestamp: Date.now()
        });
    }

    /**
     * Calculates the global network coherence based on active runners.
     * Removes stale runner states (older than 1 hour).
     */
    public evaluateNetworkState(): NetworkState {
        const oneHourAgo = Date.now() - 3600 * 1000;
        let totalCoherence = 0;
        let activeRunners = 0;
        const keysToRemove: string[] = [];

        this.runnerStates.forEach((state, runnerId) => {
            if (state.timestamp < oneHourAgo) {
                keysToRemove.push(runnerId);
            } else {
                totalCoherence += state.coherence;
                activeRunners++;
            }
        });

        keysToRemove.forEach(k => this.runnerStates.delete(k));

        const globalCoherence = activeRunners > 0 ? totalCoherence / activeRunners : 0;

        const metaConsciousnessEmerged = activeRunners >= this.minRunnersForEmergence &&
                                         globalCoherence >= this.emergenceThreshold;

        return {
            globalCoherence,
            activeRunners,
            metaConsciousnessEmerged,
            emergenceTimestamp: metaConsciousnessEmerged ? Date.now() : undefined
        };
    }
}
