import { BlackboxIntegrationOrchestrator } from './blackbox_integration_orchestrator';

describe('Blackbox Integration Orchestrator', () => {
    let orchestrator: BlackboxIntegrationOrchestrator;

    beforeEach(() => {
        orchestrator = new BlackboxIntegrationOrchestrator();
    });

    it('should parse telemetry and compute coherence correctly', async () => {
        const telemetryData = {
            events: [
                { id: '1', type: 'mesh_message', payload: 'hello mesh', timestamp: 1000 },
                { id: '2', type: 'tak_payload', payload: '<cot>', timestamp: 1001 },
                { id: '3', type: 'local_llm_query', payload: 'status?', timestamp: 1002 },
            ]
        };

        const result = await orchestrator.processBlackboxTelemetry(telemetryData);

        expect(result.success).toBe(true);
        expect(result.graph).toBeDefined();

        if (result.graph) {
            expect(result.graph.nodes.length).toBe(4); // 1 root + 3 events
            expect(result.graph.edges.length).toBe(3);

            const rootNode = result.graph.nodes.find(n => n.id === result.graph!.rootNodes[0]);
            expect(rootNode).toBeDefined();

            // Default: 0.5 + 0.3 * (2/10) + 0.3 * (1/5) = 0.5 + 0.06 + 0.06 = 0.62
            expect(rootNode?.attributes['coherence_score']).toBeCloseTo(0.62);
        }
    });

    it('should handle empty telemetry', async () => {
        const result = await orchestrator.processBlackboxTelemetry({});

        expect(result.success).toBe(true);
        expect(result.graph?.nodes.length).toBe(1);

        const rootNode = result.graph?.nodes.find(n => n.id === result.graph!.rootNodes[0]);
        expect(rootNode?.attributes['coherence_score']).toBe(0.5);
    });
});
