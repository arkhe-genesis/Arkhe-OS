import { OpenAPIParser } from '../../src/parser/frontends/openapi_frontend';
import { LFIRGraph, LFIRNodeType } from '../../src/lfir';

const validSpec = {
  openapi: '3.0.0',
  info: { title: 'Test API', version: '1.0.0' },
  paths: {
    '/users': {
      get: {
        operationId: 'getUsers',
        responses: { '200': { description: 'Success' } }
      }
    }
  }
};

describe('OpenAPIParser', () => {
  test('✅ Should parse a valid specification', () => {
    const result = OpenAPIParser.parse(validSpec);
    expect(result.success).toBe(true);
    expect(result.graph).toBeInstanceOf(LFIRGraph);
    expect(result.graph!.nodes.length).toBeGreaterThan(0);
    expect(result.graph!.metadata.coherence).toBeDefined();
  });

  test('✅ Should extract endpoints', () => {
    const result = OpenAPIParser.parse(validSpec);
    const endpoints = result.graph!.nodes.filter(
      n => n.type === LFIRNodeType.ENDPOINT
    );
    expect(endpoints.length).toBe(1);
    expect(endpoints[0].attributes['path']).toBe('/users');
  });

  test('✅ Should generate valid edges', () => {
    const result = OpenAPIParser.parse(validSpec);
    const methodNodes = result.graph!.nodes.filter(
      n => n.type === LFIRNodeType.FUNCTION
    );
    expect(methodNodes.length).toBe(1);
    // Verificar arestas method_of
    const edges = result.graph!.edges.filter(e => e.relation === 'method_of');
    expect(edges.length).toBe(1);
  });

  test('❌ Should fail with invalid input', () => {
    const result = OpenAPIParser.parse({ invalid: true } as any);
    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  test('❌ Should fail with missing spec', () => {
    const result = OpenAPIParser.parse(null);
    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  test('📸 Snapshot of LFIR graph', () => {
    const result = OpenAPIParser.parse(validSpec);
    expect(result.graph).toMatchSnapshot({
      metadata: expect.objectContaining({
        parseTimestamp: expect.any(Date)
      })
    });
  });

  test('Should handle spec without paths', () => {
    const spec = { openapi: '3.0.0', info: { title: 'No Paths API', version: '1.0.0' } };
    const result = OpenAPIParser.parse(spec);
    expect(result.success).toBe(true);
    expect(result.graph!.nodes.length).toBe(0);
  });
});
