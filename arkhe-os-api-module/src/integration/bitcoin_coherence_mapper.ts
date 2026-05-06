import { LFIRGraph, LFIRNodeType } from '../lfir';

export class CoherenceGradientChannel {
    constructor(public id: string, public nodeId: string, public type: string) {}

    submitGradient() {}
}

export class BitcoinCoherenceMapper {
    private channel: CoherenceGradientChannel;
    private metrics = { gradientsSubmitted: 0 };

    constructor(channel: CoherenceGradientChannel, config: any) {
        this.channel = channel;
    }

    processLFIRGraph(graph: LFIRGraph) {
        for (const node of graph.nodes) {
            if (node.type === LFIRNodeType.BLOCK) {
                const diff = node.attributes['difficulty'] || 0;
                const valid = node.attributes['pow_valid'];

                if (valid) {
                    this.channel.submitGradient();
                    this.metrics.gradientsSubmitted++;
                } else if (!valid && diff === 1) {
                    this.channel.submitGradient(); // submit negative
                    this.metrics.gradientsSubmitted++;
                }
            }
        }
    }

    getMapperMetrics() {
        return this.metrics;
    }
}
