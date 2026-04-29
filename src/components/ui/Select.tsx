
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

export const Select = ({ children, value, onValueChange }: { children: React.ReactNode, value: string, onValueChange: (val: string) => void }) => {
  return (
    <select value={value} onChange={e => onValueChange(e.target.value)}>
      {children}
    </select>
  );
};

export const SelectTrigger = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const SelectValue = ({ placeholder }: { placeholder: string }) => <option value="" disabled>{placeholder}</option>;
export const SelectContent = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const SelectItem = ({ children, value }: { children: React.ReactNode, value: string }) => <option value={value}>{children}</option>;
