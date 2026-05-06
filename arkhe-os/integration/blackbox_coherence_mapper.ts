// arkhe-os/integration/blackbox_coherence_mapper.ts
import { LFIRGraph, LFIRNode } from '../parser/lfir';

export interface BlackboxCoherenceMapperConfig {
    offlineAutonomyWeight: number;
    meshReliabilityWeight: number;
    localAIEffectivenessWeight: number;
    baseCoherence: number;
}

export class BlackboxCoherenceMapper {
    private config: BlackboxCoherenceMapperConfig;

    constructor(config?: Partial<BlackboxCoherenceMapperConfig>) {
        this.config = {
            offlineAutonomyWeight: 0.4,
            meshReliabilityWeight: 0.3,
            localAIEffectivenessWeight: 0.3,
            baseCoherence: 0.5,
            ...config
        };
    }

    public async processLFIRGraph(graph: LFIRGraph): Promise<void> {
        for (const rootId of graph.rootNodes) {
            const rootNode = graph.nodes.find(n => n.id === rootId);
            if (rootNode) {
                let coherence = this.config.baseCoherence;
                let meshEvents = 0;
                let aiEvents = 0;

                // Scan operations connected to root
                for (const edge of graph.edges) {
                    if (edge.from === rootId) {
                        const targetNode = graph.nodes.find(n => n.id === edge.to);
                        if (targetNode) {
                            const eventType = targetNode.attributes['event_type'];
                            if (eventType === 'mesh_message' || eventType === 'tak_payload') {
                                meshEvents++;
                            } else if (eventType === 'local_llm_query') {
                                aiEvents++;
                            }
                        }
                    }
                }

                // Increase coherence based on interactions
                if (meshEvents > 0) {
                    coherence += this.config.meshReliabilityWeight * Math.min(1.0, meshEvents / 10);
                }
                if (aiEvents > 0) {
                    coherence += this.config.localAIEffectivenessWeight * Math.min(1.0, aiEvents / 5);
                }

                // Ensure coherence stays within [0, 1]
                rootNode.attributes['coherence_score'] = Math.min(1.0, Math.max(0.0, coherence));
                rootNode.attributes['coherence_components'] = {
                    meshEvents,
                    aiEvents
                };
            }
        }
    }
}
