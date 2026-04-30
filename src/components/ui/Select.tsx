
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import React from 'react';

export const Select = ({ children, value, onValueChange }: any) => {
  return (
    <select value={value} onChange={e => onValueChange(e.target.value)}>
      {children}
    </select>
  );
};

export const SelectTrigger = ({ children }: any) => <>{children}</>;
export const SelectValue = ({ placeholder }: any) => <option value="" disabled>{placeholder}</option>;
export const SelectContent = ({ children }: any) => <>{children}</>;
export const SelectItem = ({ children, value }: any) => <option value={value}>{children}</option>;
