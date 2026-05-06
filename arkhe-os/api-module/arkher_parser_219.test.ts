import {
  OpenAPIParser,
  GraphQLParser,
  GRPCParser,
  WebSocketParser,
  ArkherParserFactory,
  SourceType,
  LFIRGraph
} from './arkher_parser_219';

describe('Substrato 219: Arkher Parser', () => {

  // ─── TESTE 1: Parser OpenAPI ──────────────────────────
  test('T1: OpenAPIParser deve converter especificação válida', () => {
    const spec = {
      openapi: '3.0.0',
      info: {
        title: 'Test API',
        version: '1.0.0',
        description: 'API de teste'
      },
      paths: {
        '/users': {
          get: {
            operationId: 'getUsers',
            summary: 'Listar usuários',
            responses: {
              '200': {
                description: 'Sucesso',
                content: {
                  'application/json': {}
                }
              }
            }
          }
        }
      },
      components: {
        schemas: {
          User: {
            type: 'object',
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' }
            }
          }
        },
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer'
          }
        }
      }
    };

    const result = OpenAPIParser.parse(spec);

    expect(result.success).toBe(true);
    expect(result.graph).not.toBeNull();
    expect(result.graph!.metadata.sourceType).toBe(SourceType.OpenAPI);
    expect(result.graph!.nodes.length).toBeGreaterThan(0);
    expect(result.metrics.nodesCreated).toBeGreaterThan(0);
    expect(result.metrics.coherenceScore).toBeGreaterThan(0);
  });

  // ─── TESTE 2: Parser OpenAPI inválido ─────────────────
  test('T2: OpenAPIParser deve falhar com especificação inválida', () => {
    const spec = { invalid: true };
    const result = OpenAPIParser.parse(spec);

    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors[0].severity).toBe('fatal');
  });

  // ─── TESTE 3: Parser GraphQL ──────────────────────────
  test('T3: GraphQLParser deve converter schema válido', () => {
    const schema = `
      type Query {
        users: [User]
        user(id: ID!): User
      }

      type User {
        id: ID!
        name: String!
        email: String
      }

      type Mutation {
        createUser(name: String!, email: String): User
      }
    `;

    const result = GraphQLParser.parse(schema);

    expect(result.success).toBe(true);
    expect(result.graph).not.toBeNull();
    expect(result.graph!.metadata.sourceType).toBe(SourceType.GraphQL);
    expect(result.graph!.nodes.length).toBeGreaterThan(0);
  });

  // ─── TESTE 4: Parser gRPC ─────────────────────────────
  test('T4: GRPCParser deve converter proto válido', () => {
    const proto = `
      service UserService {
        rpc GetUser (UserRequest) returns (User);
        rpc CreateUser (User) returns (User);
      }

      message UserRequest {
        int32 id = 1;
      }

      message User {
        int32 id = 1;
        string name = 2;
        string email = 3;
      }
    `;

    const result = GRPCParser.parse(proto);

    expect(result.success).toBe(true);
    expect(result.graph).not.toBeNull();
    expect(result.graph!.metadata.sourceType).toBe(SourceType.gRPC);
  });

  // ─── TESTE 5: Parser WebSocket ────────────────────────
  test('T5: WebSocketParser deve converter especificação válida', () => {
    const spec = {
      name: 'Chat API',
      version: '1.0.0',
      url: 'wss://api.example.com/chat',
      protocols: ['chat-protocol'],
      events: [
        { name: 'message', direction: 'bidirectional', payload: { text: 'string' } },
        { name: 'join', direction: 'client_to_server', payload: { room: 'string' } }
      ]
    };

    const result = WebSocketParser.parse(spec);

    expect(result.success).toBe(true);
    expect(result.graph).not.toBeNull();
    expect(result.graph!.metadata.sourceType).toBe(SourceType.WebSocket);
  });

  // ─── TESTE 6: Fábrica com detecção automática ─────────
  test('T6: ArkherParserFactory deve detectar tipo OpenAPI', () => {
    const input = JSON.stringify({ openapi: '3.0.0' });
    const detected = ArkherParserFactory.detectSourceType(input);
    expect(detected).toBe(SourceType.OpenAPI);
  });

  test('T7: ArkherParserFactory deve detectar tipo GraphQL', () => {
    const input = 'type Query { users: [User] }';
    const detected = ArkherParserFactory.detectSourceType(input);
    expect(detected).toBe(SourceType.GraphQL);
  });

  test('T8: ArkherParserFactory deve detectar tipo gRPC', () => {
    const input = 'service UserService { rpc GetUser (UserRequest) returns (User); }';
    const detected = ArkherParserFactory.detectSourceType(input);
    expect(detected).toBe(SourceType.gRPC);
  });

  // ─── TESTE 7: Coerência do grafo ──────────────────────
  test('T9: Grafo LFIR deve ter coerência calculada', () => {
    const spec = {
      openapi: '3.0.0',
      info: { title: 'Test', version: '1.0' },
      paths: {
        '/test': {
          get: {
            operationId: 'testOp',
            responses: { '200': { description: 'OK' } }
          }
        }
      }
    };

    const result = OpenAPIParser.parse(spec);
    expect(result.graph!.metadata.coherence).toBeGreaterThan(0);
    expect(result.graph!.metadata.coherence).toBeLessThanOrEqual(1);
  });

  // ─── TESTE 8: Estrutura do grafo ──────────────────────
  test('T10: Grafo deve ter nós e arestas consistentes', () => {
    const spec = {
      openapi: '3.0.0',
      info: { title: 'Test', version: '1.0' },
      paths: {
        '/users': {
          get: {
            operationId: 'getUsers',
            parameters: [
              { name: 'limit', in: 'query', schema: { type: 'integer' } }
            ],
            responses: {
              '200': { description: 'OK' }
            }
          }
        }
      }
    };

    const result = OpenAPIParser.parse(spec);
    const graph = result.graph!;

    // Verificar consistência
    expect(graph.nodes.length).toBeGreaterThan(0);
    expect(graph.edges.length).toBeGreaterThan(0);

    // Todas as arestas devem referenciar nós existentes
    const nodeIds = new Set(graph.nodes.map(n => n.id));
    for (const edge of graph.edges) {
      expect(nodeIds.has(edge.from)).toBe(true);
      expect(nodeIds.has(edge.to)).toBe(true);
    }
  });
});
