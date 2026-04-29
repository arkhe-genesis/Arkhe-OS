
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

export const Switch = ({ checked, onCheckedChange, ...props }: { checked: boolean, onCheckedChange: (checked: boolean) => void, [key: string]: unknown }) => (
  <input
    type="checkbox"
    checked={checked}
    onChange={e => onCheckedChange(e.target.checked)}
    {...props}
  />
);
