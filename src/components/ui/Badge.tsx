
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
export const Badge = ({ children, className, variant: _variant }: { children: React.ReactNode, className?: string, variant?: string }) => (
  <span className={className}>{children}</span>
);
