
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

import { cn } from '../../lib/utils';

export const Button = ({ children, className, variant: _variant, size: _size, ...props }: any) => (
  <button className={cn("px-4 py-2 bg-blue-500 text-white rounded", className)} {...props}>
    {children}
  </button>
);
