
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import React from 'react';

export const Tabs = ({ children, defaultValue, className }: any) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue);
  return (
    <div className={className}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<any>, { activeTab, setActiveTab });
        }
        return child;
      })}
    </div>
  );
};

export const TabsList = ({ children, className, activeTab, setActiveTab }: any) => (
  <div className={className}>
    {React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<any>, { activeTab, setActiveTab });
      }
      return child;
    })}
  </div>
);

export const TabsTrigger = ({ children, value, activeTab, setActiveTab }: any) => (
  <button onClick={() => setActiveTab(value)} data-active={activeTab === value}>
    {children}
  </button>
);

export const TabsContent = ({ children, value, activeTab }: any) => {
  if (activeTab !== value) {return null;}
  return <div>{children}</div>;
};
