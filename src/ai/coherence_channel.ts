export class CoherenceGradientChannel {
  async submitLocalGradient() {
    return { success: true };
  }
  getChannelMetrics() {
    return { gradientsSubmitted: 0 };
  }
}
