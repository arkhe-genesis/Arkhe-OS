
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { state } from '../state';

export function getCoherenceMultiplier(): number {
  // If coherence (lambda) is high, fees are discounted.
  // If coherence is low, fees are higher.
  // Base multiplier is 1.0.
  // Lambda ranges from 0 to 1.
  return Math.max(0.5, 2.0 - state.currentLambda);
}
