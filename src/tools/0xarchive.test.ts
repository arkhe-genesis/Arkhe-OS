// src/tools/0xarchive.test.ts
import {
  archiveHyperliquidOrderbook as fetchOrderbooks,
  archiveHyperliquidTrades as fetchTrades,
  archiveHyperliquidOpenInterestCurrent as fetchOpenInterest,
  archiveHyperliquidFundingCurrent as fetchFundingRate,
  archiveHyperliquidSummary as fetchSummary,
} from './0xarchive.js';

// Mock fetch to avoid hitting live APIs during tests
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ mock: 'data' }),
  })
) as any;

describe('0xarchive tools', () => {
  it('fetchOrderbooks returns expected shape', async () => {
    const data = await fetchOrderbooks({} as any);
    expect(data.name).toBe('0xarchive_hyperliquid_orderbook');
  });

  it('fetchTrades returns expected shape', async () => {
    const data = await fetchTrades({} as any);
    expect(data.name).toBe('0xarchive_hyperliquid_trades');
  });

  it('fetchOpenInterest returns expected shape', async () => {
    const data = await fetchOpenInterest({} as any);
    expect(data.name).toBe('0xarchive_hyperliquid_openinterest_current');
  });

  it('fetchFundingRate returns expected shape', async () => {
    const data = await fetchFundingRate({} as any);
    expect(data.name).toBe('0xarchive_hyperliquid_funding_current');
  });

  it('fetchSummary returns expected shape', async () => {
    const data = await fetchSummary({} as any);
    expect(data.name).toBe('0xarchive_hyperliquid_summary');
  });
});
