
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
export const Progress = ({ value, className }: { value: number, className?: string }) => (
  <div className={className}><div style={{ width: `${value}%` }} /></div>
);
