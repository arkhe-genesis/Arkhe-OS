// index.js
const axios = require('axios');

class ArchimedesClient {
  constructor(baseURL = 'http://localhost:8080') {
    this.client = axios.create({ baseURL });
  }

  async analyze(request) {
    const response = await this.client.post('/analyze', request);
    return response.data;
  }

  async simulateSU2(request) {
    const response = await this.client.post('/simulate/su2', request);
    return response.data;
  }

  async simulateSL3Z(request) {
    const response = await this.client.post('/simulate/sl3z', request);
    return response.data;
  }

  async simulateWState(request) {
    const response = await this.client.post('/simulate/wstate', request);
    return response.data;
  }

  async detectPeaks(request) {
    const response = await this.client.post('/detect/peaks', request);
    return response.data;
  }

  async checkTeleportationResource(phases, coherence, nodes = 3, lossProb = 0.2) {
    const payload = { phases, coherence, nodes, loss_probability: lossProb };
    const response = await this.client.post("/analyze/teleportation-resource", payload);
    return response.data;
  }
}

module.exports = { ArchimedesClient };
