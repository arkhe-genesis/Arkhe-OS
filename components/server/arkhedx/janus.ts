
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

const BASE_TAKER_FEE = 0.003; // 0.3%
const BASE_MAKER_FEE = 0.001; // 0.1%

const JANUS_DISCOUNT = 0.5; // 50% discount if Janus locked

export function calculateFee(notional: number, hasJanusLock: boolean, isMaker: boolean): number {
  let feeRate = isMaker ? BASE_MAKER_FEE : BASE_TAKER_FEE;
  
  if (hasJanusLock) {
    feeRate *= JANUS_DISCOUNT;
  }
  
  return notional * feeRate;
}
