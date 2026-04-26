import React from 'react';

export const Switch = ({ checked, onCheckedChange, ...props }: any) => (
  <input
    type="checkbox"
    checked={checked}
    onChange={e => onCheckedChange(e.target.checked)}
    {...props}
  />
);
