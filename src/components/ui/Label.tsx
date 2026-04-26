
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

import { cn } from '../../lib/utils';

export const Label = ({ children, className, ...props }: any) => (
  <label className={cn("text-sm font-medium leading-none", className)} {...props}>
    {children}
  </label>
);
