// arkhe-os/arkher_parser_219.ts
// Substrato 219: Arkher Parser — Implementação TypeScript
// Versão: ∞.Ω.∇.219.1
// Conversão do Go original para TypeScript com tipos estritos

/**
 * Arkher Parser: Parser Universal de APIs
 * Converte OpenAPI, GraphQL, gRPC, WebSocket → LFIR (Low-Fidelity Intermediate Representation)
 * Representação intermediária para processamento consciente
 */

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────
export interface LFIRNode {
  id: string;
  type: string;
  attributes: Record<string, unknown>;
  children: LFIRNode[];
}

export interface LFIREdge {
  from: string;
  to: string;
  relation: string;
  weight: number;
}

export interface LFIRGraph {
  nodes: LFIRNode[];
  edges: LFIREdge[];
  metadata: LFIRMetadata;
}

export interface LFIRMetadata {
  sourceType: SourceType;
  apiName: string;
  apiVersion: string;
  parseTimestamp: Date;
  parserVersion: string;
  originalSize: number;
  nodeCount: number;
  edgeCount: number;
  maxDepth: number;
  coherence: number;
}

export enum SourceType {
  OpenAPI = 'openapi',
  GraphQL = 'graphql',
  gRPC = 'grpc',
  WebSocket = 'websocket',
  REST = 'rest',
  Unknown = 'unknown'
}

export interface ParseResult {
  success: boolean;
  graph: LFIRGraph | null;
  errors: ParseError[];
  warnings: ParseWarning[];
  metrics: ParseMetrics;
}

export interface ParseError {
  code: string;
  message: string;
  location: string;
  severity: 'error' | 'fatal';
}

export interface ParseWarning {
  code: string;
  message: string;
  location: string;
  suggestion: string;
}

export interface ParseMetrics {
  parseTimeMs: number;
  nodesCreated: number;
  edgesCreated: number;
  maxDepth: number;
  coherenceScore: number;
}

// ─── PARSER DE OPENAPI ──────────────────────────────────
export class OpenAPIParser {
  static parse(spec: Record<string, unknown>): ParseResult {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      // Validar estrutura básica
      if (!spec['openapi'] && !spec['swagger']) {
        errors.push({
          code: 'MISSING_VERSION',
          message: 'OpenAPI version field missing',
          location: 'root',
          severity: 'fatal'
        });
      }

      const info = spec['info'] as Record<string, unknown> || {};
      const paths = spec['paths'] as Record<string, unknown> || {};
      const components = spec['components'] as Record<string, unknown> || {};

      const nodes: LFIRNode[] = [];
      const edges: LFIREdge[] = [];

      // Nó raiz da API
      const apiNode: LFIRNode = {
        id: 'api_root',
        type: 'api_definition',
        attributes: {
          title: info['title'],
          version: info['version'],
          description: info['description'],
          termsOfService: info['termsOfService'],
          contact: info['contact'],
          license: info['license']
        },
        children: []
      };
      nodes.push(apiNode);

      // Parsear paths (endpoints)
      let maxDepth = 1;
      for (const [path, pathItem] of Object.entries(paths)) {
        const pathNode = OpenAPIParser.parsePath(path, pathItem as Record<string, unknown>, nodes, edges, errors, warnings);
        if (pathNode) {
          apiNode.children.push(pathNode);
          edges.push({
            from: apiNode.id,
            to: pathNode.id,
            relation: 'has_endpoint',
            weight: 1.0
          });
          maxDepth = Math.max(maxDepth, 2);
        }
      }

      // Parsear schemas
      const schemas = (components['schemas'] || {}) as Record<string, unknown>;
      for (const [schemaName, schemaDef] of Object.entries(schemas)) {
        const schemaNode = OpenAPIParser.parseSchema(schemaName, schemaDef as Record<string, unknown>, nodes, edges);
        if (schemaNode) {
          edges.push({
            from: apiNode.id,
            to: schemaNode.id,
            relation: 'has_schema',
            weight: 0.8
          });
        }
      }

      // Parsear security schemes
      const securitySchemes = (components['securitySchemes'] || {}) as Record<string, unknown>;
      for (const [schemeName, schemeDef] of Object.entries(securitySchemes)) {
        const schemeNode = OpenAPIParser.parseSecurityScheme(schemeName, schemeDef as Record<string, unknown>, nodes);
        if (schemeNode) {
          edges.push({
            from: apiNode.id,
            to: schemeNode.id,
            relation: 'has_security',
            weight: 1.2
          });
        }
      }

      const parseTime = Date.now() - startTime;
      const coherence = OpenAPIParser.computeCoherence(nodes, edges);

      const graph: LFIRGraph = {
        nodes,
        edges,
        metadata: {
          sourceType: SourceType.OpenAPI,
          apiName: (info['title'] as string) || 'unknown',
          apiVersion: (info['version'] as string) || '1.0.0',
          parseTimestamp: new Date(),
          parserVersion: '219.1.0',
          originalSize: JSON.stringify(spec).length,
          nodeCount: nodes.length,
          edgeCount: edges.length,
          maxDepth,
          coherence
        }
      };

      return {
        success: errors.filter(e => e.severity === 'fatal').length === 0,
        graph,
        errors,
        warnings,
        metrics: {
          parseTimeMs: parseTime,
          nodesCreated: nodes.length,
          edgesCreated: edges.length,
          maxDepth,
          coherenceScore: coherence
        }
      };

    } catch (err) {
      errors.push({
        code: 'PARSE_EXCEPTION',
        message: err instanceof Error ? err.message : 'Unknown error',
        location: 'global',
        severity: 'fatal'
      });

      return {
        success: false,
        graph: null,
        errors,
        warnings,
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: 0,
          edgesCreated: 0,
          maxDepth: 0,
          coherenceScore: 0
        }
      };
    }
  }

  private static parsePath(
    path: string,
    pathItem: Record<string, unknown>,
    nodes: LFIRNode[],
    edges: LFIREdge[],
    errors: ParseError[],
    warnings: ParseWarning[]
  ): LFIRNode | null {
    const pathNode: LFIRNode = {
      id: `path_${path.replace(/[^a-zA-Z0-9]/g, '_')}`,
      type: 'path',
      attributes: { path },
      children: []
    };

    const methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options'];

    for (const method of methods) {
      const operation = pathItem[method] as Record<string, unknown>;
      if (!operation) continue;

      const opNode: LFIRNode = {
        id: `${pathNode.id}_${method}`,
        type: 'operation',
        attributes: {
          method: method.toUpperCase(),
          operationId: operation['operationId'],
          summary: operation['summary'],
          description: operation['description'],
          deprecated: operation['deprecated'],
          tags: operation['tags']
        },
        children: []
      };

      // Parsear parâmetros
      const parameters = (operation['parameters'] || []) as Array<Record<string, unknown>>;
      for (const param of parameters) {
        const paramNode: LFIRNode = {
          id: `${opNode.id}_param_${param['name']}`,
          type: 'parameter',
          attributes: {
            name: param['name'],
            in: param['in'],
            required: param['required'],
            schema: param['schema']
          },
          children: []
        };
        opNode.children.push(paramNode);
        edges.push({
          from: opNode.id,
          to: paramNode.id,
          relation: 'has_parameter',
          weight: 0.5
        });
      }

      // Parsear request body
      const requestBody = operation['requestBody'] as Record<string, unknown>;
      if (requestBody) {
        const rbNode: LFIRNode = {
          id: `${opNode.id}_requestBody`,
          type: 'request_body',
          attributes: {
            description: requestBody['description'],
            required: requestBody['required'],
            content: Object.keys(requestBody['content'] as Record<string, unknown> || {})
          },
          children: []
        };
        opNode.children.push(rbNode);
        edges.push({
          from: opNode.id,
          to: rbNode.id,
          relation: 'has_request_body',
          weight: 0.7
        });
      }

      // Parsear responses
      const responses = operation['responses'] as Record<string, unknown>;
      if (responses) {
        for (const [code, response] of Object.entries(responses)) {
          const respNode: LFIRNode = {
            id: `${opNode.id}_response_${code}`,
            type: 'response',
            attributes: {
              statusCode: code,
              description: (response as Record<string, unknown>)['description'],
              content: Object.keys((response as Record<string, unknown>)['content'] as Record<string, unknown> || {})
            },
            children: []
          };
          opNode.children.push(respNode);
          edges.push({
            from: opNode.id,
            to: respNode.id,
            relation: 'has_response',
            weight: 0.6
          });
        }
      }

      pathNode.children.push(opNode);
      edges.push({
        from: pathNode.id,
        to: opNode.id,
        relation: 'has_operation',
        weight: 1.0
      });
    }

    nodes.push(pathNode);
    return pathNode;
  }

  private static parseSchema(
    name: string,
    schema: Record<string, unknown>,
    nodes: LFIRNode[],
    edges: LFIREdge[]
  ): LFIRNode | null {
    const schemaNode: LFIRNode = {
      id: `schema_${name}`,
      type: 'schema_definition',
      attributes: {
        name,
        type: schema['type'],
        format: schema['format'],
        description: schema['description']
      },
      children: []
    };

    // Parsear propriedades
    const properties = schema['properties'] as Record<string, unknown>;
    if (properties) {
      for (const [propName, propDef] of Object.entries(properties)) {
        const propNode: LFIRNode = {
          id: `${schemaNode.id}_prop_${propName}`,
          type: 'property',
          attributes: {
            name: propName,
            type: (propDef as Record<string, unknown>)['type'],
            format: (propDef as Record<string, unknown>)['format'],
            required: (schema['required'] as string[] || []).includes(propName)
          },
          children: []
        };
        schemaNode.children.push(propNode);
        edges.push({
          from: schemaNode.id,
          to: propNode.id,
          relation: 'has_property',
          weight: 0.5
        });
      }
    }

    nodes.push(schemaNode);
    return schemaNode;
  }

  private static parseSecurityScheme(
    name: string,
    scheme: Record<string, unknown>,
    nodes: LFIRNode[]
  ): LFIRNode | null {
    const schemeNode: LFIRNode = {
      id: `security_${name}`,
      type: 'security_scheme',
      attributes: {
        name,
        type: scheme['type'],
        scheme: scheme['scheme'],
        bearerFormat: scheme['bearerFormat'],
        flows: scheme['flows'],
        openIdConnectUrl: scheme['openIdConnectUrl']
      },
      children: []
    };

    nodes.push(schemeNode);
    return schemeNode;
  }

  private static computeCoherence(nodes: LFIRNode[], edges: LFIREdge[]): number {
    if (nodes.length === 0) return 0;
    const avgChildren = nodes.reduce((sum, n) => sum + n.children.length, 0) / nodes.length;
    const avgWeight = edges.length > 0 ? edges.reduce((sum, e) => sum + e.weight, 0) / edges.length : 0;
    return Math.min(1.0, (avgChildren / 5) * 0.5 + avgWeight * 0.5);
  }
}

// ─── PARSER DE GRAPHQL ──────────────────────────────────
export class GraphQLParser {
  static parse(schema: string): ParseResult {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const nodes: LFIRNode[] = [];
      const edges: LFIREdge[] = [];

      // Parse simplificado de schema GraphQL
      const types = GraphQLParser.extractTypes(schema);
      const queries = GraphQLParser.extractQueries(schema);
      const mutations = GraphQLParser.extractMutations(schema);

      // Nó raiz
      const rootNode: LFIRNode = {
        id: 'graphql_root',
        type: 'graphql_schema',
        attributes: { schemaText: schema.slice(0, 200) },
        children: []
      };
      nodes.push(rootNode);

      // Tipos
      for (const type of types) {
        const typeNode: LFIRNode = {
          id: `graphql_type_${type.name}`,
          type: 'graphql_type',
          attributes: {
            name: type.name,
            kind: type.kind,
            fields: type.fields.map(f => f.name)
          },
          children: []
        };

        for (const field of type.fields) {
          const fieldNode: LFIRNode = {
            id: `${typeNode.id}_field_${field.name}`,
            type: 'graphql_field',
            attributes: {
              name: field.name,
              type: field.type,
              args: field.args
            },
            children: []
          };
          typeNode.children.push(fieldNode);
          edges.push({
            from: typeNode.id,
            to: fieldNode.id,
            relation: 'has_field',
            weight: 0.6
          });
        }

        nodes.push(typeNode);
        edges.push({
          from: rootNode.id,
          to: typeNode.id,
          relation: 'defines_type',
          weight: 1.0
        });
      }

      // Queries
      for (const query of queries) {
        const queryNode: LFIRNode = {
          id: `graphql_query_${query.name}`,
          type: 'graphql_query',
          attributes: {
            name: query.name,
            returnType: query.returnType,
            args: query.args
          },
          children: []
        };
        nodes.push(queryNode);
        edges.push({
          from: rootNode.id,
          to: queryNode.id,
          relation: 'has_query',
          weight: 1.0
        });
      }

      const parseTime = Date.now() - startTime;
      const coherence = GraphQLParser.computeCoherence(nodes, edges);

      const graph: LFIRGraph = {
        nodes,
        edges,
        metadata: {
          sourceType: SourceType.GraphQL,
          apiName: 'graphql_api',
          apiVersion: '1.0.0',
          parseTimestamp: new Date(),
          parserVersion: '219.1.0',
          originalSize: schema.length,
          nodeCount: nodes.length,
          edgeCount: edges.length,
          maxDepth: 3,
          coherence
        }
      };

      return {
        success: true,
        graph,
        errors,
        warnings,
        metrics: {
          parseTimeMs: parseTime,
          nodesCreated: nodes.length,
          edgesCreated: edges.length,
          maxDepth: 3,
          coherenceScore: coherence
        }
      };

    } catch (err) {
      errors.push({
        code: 'GRAPHQL_PARSE_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
        location: 'global',
        severity: 'fatal'
      });

      return {
        success: false,
        graph: null,
        errors,
        warnings,
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: 0,
          edgesCreated: 0,
          maxDepth: 0,
          coherenceScore: 0
        }
      };
    }
  }

  private static extractTypes(schema: string): Array<{name: string; kind: string; fields: Array<{name: string; type: string; args: string[]}>}> {
    const types: Array<{name: string; kind: string; fields: Array<{name: string; type: string; args: string[]}>}> = [];
    const typeRegex = /type\s+(\w+)\s*\{([^}]+)\}/g;
    let match;

    while ((match = typeRegex.exec(schema)) !== null) {
      const name = match[1];
      const body = match[2];
      const fields: Array<{name: string; type: string; args: string[]}> = [];

      const fieldRegex = /(\w+)\s*(\([^)]*\))?\s*:\s*([^\n]+)/g;
      let fieldMatch;
      while ((fieldMatch = fieldRegex.exec(body)) !== null) {
        fields.push({
          name: fieldMatch[1],
          type: fieldMatch[3].trim(),
          args: fieldMatch[2] ? [fieldMatch[2]] : []
        });
      }

      types.push({ name, kind: 'object', fields });
    }

    return types;
  }

  private static extractQueries(schema: string): Array<{name: string; returnType: string; args: string[]}> {
    const queries: Array<{name: string; returnType: string; args: string[]}> = [];
    const queryRegex = /type\s+Query\s*\{([^}]+)\}/;
    const match = queryRegex.exec(schema);

    if (match) {
      const body = match[1];
      const fieldRegex = /(\w+)\s*(\([^)]*\))?\s*:\s*([^\n]+)/g;
      let fieldMatch;
      while ((fieldMatch = fieldRegex.exec(body)) !== null) {
        queries.push({
          name: fieldMatch[1],
          returnType: fieldMatch[3].trim(),
          args: fieldMatch[2] ? [fieldMatch[2]] : []
        });
      }
    }

    return queries;
  }

  private static extractMutations(schema: string): Array<{name: string; returnType: string; args: string[]}> {
    const mutations: Array<{name: string; returnType: string; args: string[]}> = [];
    const mutationRegex = /type\s+Mutation\s*\{([^}]+)\}/;
    const match = mutationRegex.exec(schema);

    if (match) {
      const body = match[1];
      const fieldRegex = /(\w+)\s*(\([^)]*\))?\s*:\s*([^\n]+)/g;
      let fieldMatch;
      while ((fieldMatch = fieldRegex.exec(body)) !== null) {
        mutations.push({
          name: fieldMatch[1],
          returnType: fieldMatch[3].trim(),
          args: fieldMatch[2] ? [fieldMatch[2]] : []
        });
      }
    }

    return mutations;
  }

  private static computeCoherence(nodes: LFIRNode[], edges: LFIREdge[]): number {
    if (nodes.length === 0) return 0;
    const avgChildren = nodes.reduce((sum, n) => sum + n.children.length, 0) / nodes.length;
    const avgWeight = edges.length > 0 ? edges.reduce((sum, e) => sum + e.weight, 0) / edges.length : 0;
    return Math.min(1.0, (avgChildren / 5) * 0.5 + avgWeight * 0.5);
  }
}

// ─── PARSER DE GRPC ─────────────────────────────────────
export class GRPCParser {
  static parse(proto: string): ParseResult {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const nodes: LFIRNode[] = [];
      const edges: LFIREdge[] = [];

      const rootNode: LFIRNode = {
        id: 'grpc_root',
        type: 'grpc_proto',
        attributes: { protoText: proto.slice(0, 200) },
        children: []
      };
      nodes.push(rootNode);

      // Extrair services
      const services = GRPCParser.extractServices(proto);
      for (const service of services) {
        const serviceNode: LFIRNode = {
          id: `grpc_service_${service.name}`,
          type: 'grpc_service',
          attributes: {
            name: service.name,
            methods: service.methods.map(m => m.name)
          },
          children: []
        };

        for (const method of service.methods) {
          const methodNode: LFIRNode = {
            id: `${serviceNode.id}_method_${method.name}`,
            type: 'grpc_method',
            attributes: {
              name: method.name,
              inputType: method.inputType,
              outputType: method.outputType,
              streaming: method.streaming
            },
            children: []
          };
          serviceNode.children.push(methodNode);
          edges.push({
            from: serviceNode.id,
            to: methodNode.id,
            relation: 'has_method',
            weight: 1.0
          });
        }

        nodes.push(serviceNode);
        edges.push({
          from: rootNode.id,
          to: serviceNode.id,
          relation: 'defines_service',
          weight: 1.0
        });
      }

      // Extrair messages
      const messages = GRPCParser.extractMessages(proto);
      for (const message of messages) {
        const msgNode: LFIRNode = {
          id: `grpc_message_${message.name}`,
          type: 'grpc_message',
          attributes: {
            name: message.name,
            fields: message.fields.map(f => f.name)
          },
          children: []
        };

        for (const field of message.fields) {
          const fieldNode: LFIRNode = {
            id: `${msgNode.id}_field_${field.name}`,
            type: 'grpc_field',
            attributes: {
              name: field.name,
              type: field.type,
              number: field.number,
              label: field.label
            },
            children: []
          };
          msgNode.children.push(fieldNode);
          edges.push({
            from: msgNode.id,
            to: fieldNode.id,
            relation: 'has_field',
            weight: 0.5
          });
        }

        nodes.push(msgNode);
      }

      const parseTime = Date.now() - startTime;
      const coherence = GRPCParser.computeCoherence(nodes, edges);

      const graph: LFIRGraph = {
        nodes,
        edges,
        metadata: {
          sourceType: SourceType.gRPC,
          apiName: 'grpc_api',
          apiVersion: '1.0.0',
          parseTimestamp: new Date(),
          parserVersion: '219.1.0',
          originalSize: proto.length,
          nodeCount: nodes.length,
          edgeCount: edges.length,
          maxDepth: 3,
          coherence
        }
      };

      return {
        success: true,
        graph,
        errors,
        warnings,
        metrics: {
          parseTimeMs: parseTime,
          nodesCreated: nodes.length,
          edgesCreated: edges.length,
          maxDepth: 3,
          coherenceScore: coherence
        }
      };

    } catch (err) {
      errors.push({
        code: 'GRPC_PARSE_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
        location: 'global',
        severity: 'fatal'
      });

      return {
        success: false,
        graph: null,
        errors,
        warnings,
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: 0,
          edgesCreated: 0,
          maxDepth: 0,
          coherenceScore: 0
        }
      };
    }
  }

  private static extractServices(proto: string): Array<{name: string; methods: Array<{name: string; inputType: string; outputType: string; streaming: boolean}>}> {
    const services: Array<{name: string; methods: Array<{name: string; inputType: string; outputType: string; streaming: boolean}>}> = [];
    const serviceRegex = /service\s+(\w+)\s*\{([^}]+)\}/g;
    let match;

    while ((match = serviceRegex.exec(proto)) !== null) {
      const name = match[1];
      const body = match[2];
      const methods: Array<{name: string; inputType: string; outputType: string; streaming: boolean}> = [];

      const methodRegex = /rpc\s+(\w+)\s*\(([^)]+)\)\s*returns\s*\(([^)]+)\)/g;
      let methodMatch;
      while ((methodMatch = methodRegex.exec(body)) !== null) {
        methods.push({
          name: methodMatch[1],
          inputType: methodMatch[2].trim(),
          outputType: methodMatch[3].trim(),
          streaming: methodMatch[2].includes('stream') || methodMatch[3].includes('stream')
        });
      }

      services.push({ name, methods });
    }

    return services;
  }

  private static extractMessages(proto: string): Array<{name: string; fields: Array<{name: string; type: string; number: number; label: string}>}> {
    const messages: Array<{name: string; fields: Array<{name: string; type: string; number: number; label: string}>}> = [];
    const messageRegex = /message\s+(\w+)\s*\{([^}]+)\}/g;
    let match;

    while ((match = messageRegex.exec(proto)) !== null) {
      const name = match[1];
      const body = match[2];
      const fields: Array<{name: string; type: string; number: number; label: string}> = [];

      const fieldRegex = /(\w+)\s+(\w+)\s+(\w+)\s*=\s*(\d+);/g;
      let fieldMatch;
      while ((fieldMatch = fieldRegex.exec(body)) !== null) {
        fields.push({
          label: fieldMatch[1],
          type: fieldMatch[2],
          name: fieldMatch[3],
          number: parseInt(fieldMatch[4])
        });
      }

      messages.push({ name, fields });
    }

    return messages;
  }

  private static computeCoherence(nodes: LFIRNode[], edges: LFIREdge[]): number {
    if (nodes.length === 0) return 0;
    const avgChildren = nodes.reduce((sum, n) => sum + n.children.length, 0) / nodes.length;
    const avgWeight = edges.length > 0 ? edges.reduce((sum, e) => sum + e.weight, 0) / edges.length : 0;
    return Math.min(1.0, (avgChildren / 5) * 0.5 + avgWeight * 0.5);
  }
}

// ─── PARSER DE WEBSOCKET ────────────────────────────────
export class WebSocketParser {
  static parse(spec: Record<string, unknown>): ParseResult {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const nodes: LFIRNode[] = [];
      const edges: LFIREdge[] = [];

      const rootNode: LFIRNode = {
        id: 'ws_root',
        type: 'websocket_api',
        attributes: {
          url: spec['url'],
          protocols: spec['protocols']
        },
        children: []
      };
      nodes.push(rootNode);

      // Eventos
      const events = (spec['events'] || []) as Array<Record<string, unknown>>;
      for (const event of events) {
        const eventNode: LFIRNode = {
          id: `ws_event_${event['name']}`,
          type: 'websocket_event',
          attributes: {
            name: event['name'],
            direction: event['direction'],
            payload: event['payload']
          },
          children: []
        };
        nodes.push(eventNode);
        edges.push({
          from: rootNode.id,
          to: eventNode.id,
          relation: 'has_event',
          weight: 1.0
        });
      }

      const parseTime = Date.now() - startTime;
      const coherence = WebSocketParser.computeCoherence(nodes, edges);

      const graph: LFIRGraph = {
        nodes,
        edges,
        metadata: {
          sourceType: SourceType.WebSocket,
          apiName: (spec['name'] as string) || 'websocket_api',
          apiVersion: (spec['version'] as string) || '1.0.0',
          parseTimestamp: new Date(),
          parserVersion: '219.1.0',
          originalSize: JSON.stringify(spec).length,
          nodeCount: nodes.length,
          edgeCount: edges.length,
          maxDepth: 2,
          coherence
        }
      };

      return {
        success: true,
        graph,
        errors,
        warnings,
        metrics: {
          parseTimeMs: parseTime,
          nodesCreated: nodes.length,
          edgesCreated: edges.length,
          maxDepth: 2,
          coherenceScore: coherence
        }
      };

    } catch (err) {
      errors.push({
        code: 'WS_PARSE_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
        location: 'global',
        severity: 'fatal'
      });

      return {
        success: false,
        graph: null,
        errors,
        warnings,
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: 0,
          edgesCreated: 0,
          maxDepth: 0,
          coherenceScore: 0
        }
      };
    }
  }

  private static computeCoherence(nodes: LFIRNode[], edges: LFIREdge[]): number {
    if (nodes.length === 0) return 0;
    const avgChildren = nodes.reduce((sum, n) => sum + n.children.length, 0) / nodes.length;
    const avgWeight = edges.length > 0 ? edges.reduce((sum, e) => sum + e.weight, 0) / edges.length : 0;
    return Math.min(1.0, (avgChildren / 5) * 0.5 + avgWeight * 0.5);
  }
}

// ─── FÁBRICA DE PARSERS ─────────────────────────────────
export class ArkherParserFactory {
  static createParser(sourceType: SourceType): {
    parse: (input: string | Record<string, unknown>) => ParseResult;
  } {
    switch (sourceType) {
      case SourceType.OpenAPI:
        return {
          parse: (input) => OpenAPIParser.parse(input as Record<string, unknown>)
        };
      case SourceType.GraphQL:
        return {
          parse: (input) => GraphQLParser.parse(input as string)
        };
      case SourceType.gRPC:
        return {
          parse: (input) => GRPCParser.parse(input as string)
        };
      case SourceType.WebSocket:
        return {
          parse: (input) => WebSocketParser.parse(input as Record<string, unknown>)
        };
      default:
        throw new Error(`Unsupported source type: ${sourceType}`);
    }
  }

  static detectSourceType(input: string | Record<string, unknown>): SourceType {
    if (typeof input === 'string') {
      if (input.includes('openapi') || input.includes('swagger')) {
        return SourceType.OpenAPI;
      }
      if (input.includes('type Query') || input.includes('type Mutation')) {
        return SourceType.GraphQL;
      }
      if (input.includes('service ') || input.includes('message ')) {
        return SourceType.gRPC;
      }
      return SourceType.Unknown;
    }

    if (typeof input === 'object') {
      if (input['openapi'] || input['swagger']) {
        return SourceType.OpenAPI;
      }
      if (input['url'] && input['events']) {
        return SourceType.WebSocket;
      }
      return SourceType.REST;
    }

    return SourceType.Unknown;
  }
}
