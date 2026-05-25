class Signal {
  constructor({ source, topic, metric, value, unit }) {
    this.source = source;
    this.topic = topic;
    this.metric = metric;
    this.value = value;
    this.unit = unit;
    this.seal = "mock-seal";
  }
}

const TOPICS = {
  COHERENCE_DSA: 'COHERENCE_DSA'
};

class Telegraph {
  publish(signal) {
    console.log(`[Telegraph] Published signal to topic ${signal.topic}`);
  }
}

module.exports = { Signal, TOPICS, Telegraph };
