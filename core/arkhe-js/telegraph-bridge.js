// ═══════════════════════════════════════════════════════════════════
// ARKHE TELEGRAPH BRIDGE — Conector para o barramento externo
// ═══════════════════════════════════════════════════════════════════

const WebSocket = require('ws');
const { Telegraph } = require('./telegraph');

class TelegraphBridge {
  constructor(cathedralTelegraph, externalUrl = 'ws://telegraph.network:7474') {
    this.cathedral = cathedralTelegraph;
    this.externalUrl = externalUrl;
    this.externalWs = null;
    this.topicMap = {
      // Cathedral → External
      '/coherence/dsa': '/arkhe/coherence/dsa',
      '/coherence/interop': '/arkhe/coherence/interop',
      '/coherence/kuramoto': '/arkhe/sim/kuramoto',
      // External → Cathedral
      '/coherence/global': '/external/telegraph',
    };
  }

  connect() {
    this.externalWs = new WebSocket(this.externalUrl);
    this.externalWs.on('open', () => {
      console.log('[BRIDGE] Conectado ao barramento externo');
      // Inscrever nos tópicos de interesse
      this.externalWs.send(JSON.stringify({
        command: 'subscribe',
        topics: Object.keys(this.topicMap).filter(t => this.topicMap[t].startsWith('/external/')),
      }));
    });

    this.externalWs.on('message', (data) => {
      const msg = JSON.parse(data.toString());
      if (msg.type === 'signal' && this.topicMap[msg.topic]) {
        // Retransmitir para o barramento interno
        this.cathedral.publish(this.topicMap[msg.topic], msg.signal);
      }
    });

    this.externalWs.on('close', () => {
      console.log('[BRIDGE] Conexão perdida, reconectando em 5s...');
      setTimeout(() => this.connect(), 5000);
    });
  }

  // Publicar do barramento interno para o externo
  forwardToExternal(topic, signal) {
    if (this.externalWs && this.externalWs.readyState === WebSocket.OPEN) {
      const externalTopic = Object.keys(this.topicMap).find(k => this.topicMap[k] === topic);
      if (externalTopic) {
        this.externalWs.send(JSON.stringify({ type: 'signal', topic: externalTopic, signal }));
      }
    }
  }
}

module.exports = TelegraphBridge;
