
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { calculateFee } from './janus';
import { getCoherenceMultiplier } from './oracle';
import type { Order, Trade } from './types';
import { Side } from './types';

export class OrderBook {
  symbol: string;
  bids: Order[]; // Sorted by price DESC, then timestamp ASC
  asks: Order[]; // Sorted by price ASC, then timestamp ASC
  orders: Map<string, Order>;
  trades: Trade[];

  constructor(symbol: string) {
    this.symbol = symbol;
    this.bids = [];
    this.asks = [];
    this.orders = new Map();
    this.trades = [];
  }

  addOrder(order: Order): Trade[] {
    this.orders.set(order.id, order);
    const newTrades = this.matchOrder(order);
    
    if (order.filled < order.size && order.type === 'limit') {
      this.insertOrder(order);
    }
    
    return newTrades;
  }

  private insertOrder(order: Order) {
    const list = order.side === 'buy' ? this.bids : this.asks;
    list.push(order);
    
    // Sort
    list.sort((a, b) => {
      if (a.price !== b.price) {
        return order.side === 'buy' ? b.price - a.price : a.price - b.price;
      }
      return a.timestamp - b.timestamp;
    });
  }

  private matchOrder(takerOrder: Order): Trade[] {
    const newTrades: Trade[] = [];
    const book = takerOrder.side === 'buy' ? this.asks : this.bids;
    
    while (book.length > 0 && takerOrder.filled < takerOrder.size) {
      const makerOrder = book[0];
      
      // Check price matching
      if (takerOrder.type === 'limit') {
        if (takerOrder.side === 'buy' && takerOrder.price < makerOrder.price) {break;}
        if (takerOrder.side === 'sell' && takerOrder.price > makerOrder.price) {break;}
      }
      
      const tradeSize = Math.min(takerOrder.size - takerOrder.filled, makerOrder.size - makerOrder.filled);
      const tradePrice = makerOrder.price;
      
      takerOrder.filled += tradeSize;
      makerOrder.filled += tradeSize;
      
      // Calculate fees with Janus and Coherence
      const coherenceMult = getCoherenceMultiplier();
      const takerFee = calculateFee(tradeSize * tradePrice, takerOrder.janusLocked, false) * coherenceMult;
      const makerFee = calculateFee(tradeSize * tradePrice, makerOrder.janusLocked, true) * coherenceMult;
      
      const trade: Trade = {
        id: `trd_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        makerOrderId: makerOrder.id,
        takerOrderId: takerOrder.id,
        price: tradePrice,
        size: tradeSize,
        timestamp: Date.now(),
        makerFee,
        takerFee
      };
      
      newTrades.push(trade);
      this.trades.push(trade);
      
      if (makerOrder.filled === makerOrder.size) {
        book.shift(); // Remove filled maker order
      }
    }
    
    return newTrades;
  }
}
