
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

export const Tabs = ({ children, defaultValue, className }: { children: React.ReactNode, defaultValue: string, className?: string }) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue);
  return (
    <div className={className}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ activeTab: string, setActiveTab: (val: string) => void }>, { activeTab, setActiveTab });
        }
        return child;
      })}
    </div>
  );
};

export const TabsList = ({ children, className, activeTab, setActiveTab }: { children: React.ReactNode, className?: string, activeTab?: string, setActiveTab?: (val: string) => void }) => (
  <div className={className}>
    {React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<{ activeTab?: string, setActiveTab?: (val: string) => void }>, { activeTab, setActiveTab });
      }
      return child;
    })}
  </div>
);

export const TabsTrigger = ({ children, value, activeTab, setActiveTab }: { children: React.ReactNode, value: string, activeTab?: string, setActiveTab?: (val: string) => void }) => (
  <button onClick={() => setActiveTab?.(value)} data-active={activeTab === value}>
    {children}
  </button>
);

export const TabsContent = ({ children, value, activeTab }: { children: React.ReactNode, value: string, activeTab?: string }) => {
  if (activeTab !== value) {return null;}
  return <div>{children}</div>;
};
