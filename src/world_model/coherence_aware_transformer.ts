export class CoherenceAwareTransformer {
  static fromPretrainedMock() {
    return new CoherenceAwareTransformer();
  }
  async encodeForDiffusion(code: string, spec: string) {
    return { code, spec };
  }
  async predictCoherencePrior(code: string, spec: string) {
    return 0.8;
  }
}
