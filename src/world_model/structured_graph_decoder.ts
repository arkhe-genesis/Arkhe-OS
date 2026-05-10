export class StructuredGraphDecoder {
  constructor(options: any) {}
  async decode(z0: any) {
    return {
      nodes: [{ type: 'ENDPOINT', attributes: { path: '/users' } }],
      edges: [],
      coherence: 0.86
    };
  }
}
