
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { EventEmitter } from 'node:events';

import { logger } from './logger';
import { state } from './state';

class MessageBroker extends EventEmitter {
  constructor() {
    super();
    logger.info("🜏 [BROKER] Message Broker Initialized.");
  }

  publish(topic: string, message: any) {
    logger.info(`🜏 [BROKER] Publishing to ${topic}`);
    this.emit(topic, message);

    // Update state metrics
    if (state.networkInfra) {
      state.networkInfra.broker.messagesProcessed += 1;
      if (!state.networkInfra.broker.activeTopics.includes(topic)) {
        state.networkInfra.broker.activeTopics.push(topic);
      }
    }
  }

  subscribe(topic: string, callback: (message: any) => void) {
    logger.info(`🜏 [BROKER] New subscriber for topic: ${topic}`);
    this.on(topic, callback);
  }
}

export const broker = new MessageBroker();
