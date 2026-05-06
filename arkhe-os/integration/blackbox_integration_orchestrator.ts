// arkhe-os/integration/blackbox_integration_orchestrator.ts
import { BlackboxFrontend, BlackboxFrontendConfig } from '../parser/frontends/blackbox_frontend';
import { BlackboxCoherenceMapper, BlackboxCoherenceMapperConfig } from './blackbox_coherence_mapper';
import { ParseResult } from '../parser/lfir';

export interface BlackboxOrchestratorConfig {
    frontendConfig: Partial<BlackboxFrontendConfig>;
    mapperConfig: Partial<BlackboxCoherenceMapperConfig>;
}

export class BlackboxIntegrationOrchestrator {
    private frontend: BlackboxFrontend;
    private mapper: BlackboxCoherenceMapper;

    constructor(config?: Partial<BlackboxOrchestratorConfig>) {
        this.frontend = new BlackboxFrontend(config?.frontendConfig);
        this.mapper = new BlackboxCoherenceMapper(config?.mapperConfig);
    }

    public async processBlackboxTelemetry(telemetryData: any): Promise<ParseResult> {
        // Step 1: Parse telemetry into LFIR graph
        const result = await this.frontend.parse(telemetryData);

        // Step 2: Map coherence scores based on LFIR operations
        if (result.graph) {
            await this.mapper.processLFIRGraph(result.graph);

            // Update coherence score in metrics from root node
            if (result.graph.rootNodes.length > 0) {
                const rootId = result.graph.rootNodes[0];
                const rootNode = result.graph.nodes.find(n => n.id === rootId);
                if (rootNode && rootNode.attributes['coherence_score']) {
                    result.metrics.coherenceScore = rootNode.attributes['coherence_score'] as number;
                }
            }
        }

        return result;
    }
}
