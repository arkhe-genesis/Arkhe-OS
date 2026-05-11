// tests/setup.ts
import './matchers/coherence';
import { CoherenceGradientChannel } from '@/ai/coherence_channel';

// Mock global para canal de coerência em todos os testes
jest.mock('@/ai/coherence_channel', () => ({
  CoherenceGradientChannel: jest.fn().mockImplementation(() => ({
    submitLocalGradient: jest.fn().mockResolvedValue({ success: true }),
    getChannelMetrics: jest.fn().mockReturnValue({ gradientsSubmitted: 0 }),
  })),
}));

// Setup de timezone consistente para snapshots
beforeAll(() => {
  process.env.TZ = 'UTC';
  jest.useFakeTimers().setSystemTime(new Date('2026-05-06T00:00:00Z'));
});

afterAll(() => {
  jest.useRealTimers();
});

// Helper para criar fixtures de grafo LFIR
export function createMockLFIRGraph(language: string, filename: string) {
  return {
    language,
    filename,
    nodes: [],
    edges: [],
    metrics: {},
    coherence: () => 0.5,
    addNode: jest.fn(),
    addEdge: jest.fn(),
  };
}
