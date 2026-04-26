/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export enum ToolCategory {
  INPUT = 'input',
  NAVIGATION = 'navigation',
  EMULATION = 'emulation',
  PERFORMANCE = 'performance',
  NETWORK = 'network',
  DEBUGGING = 'debugging',
  EXTENSIONS = 'extensions',
  IN_PAGE = 'in-page',
  STORAGE = 'storage',
  ARKHE = 'arkhe',
  DECENTRALIZED = 'decentralized',
  FINANCE = 'finance',
  AGENT = 'agent',
  SANDBOX = 'sandbox',
  EVOSKILL = 'evoskill',
  MESHTASTIC = 'meshtastic',
  GNO = 'gno',
}

export const labels = {
  [ToolCategory.INPUT]: 'Input automation',
  [ToolCategory.NAVIGATION]: 'Navigation automation',
  [ToolCategory.EMULATION]: 'Emulation',
  [ToolCategory.PERFORMANCE]: 'Performance',
  [ToolCategory.NETWORK]: 'Network',
  [ToolCategory.DEBUGGING]: 'Debugging',
  [ToolCategory.EXTENSIONS]: 'Extensions',
  [ToolCategory.IN_PAGE]: 'In-page tools',
  [ToolCategory.STORAGE]: 'Storage',
  [ToolCategory.ARKHE]: 'Arkhe(n) Protocols',
  [ToolCategory.DECENTRALIZED]: 'Decentralized Protocols',
  [ToolCategory.FINANCE]: 'Finance Protocols',
  [ToolCategory.AGENT]: 'Mercury Agent Protocols',
  [ToolCategory.SANDBOX]: 'Microsandbox Protocols',
  [ToolCategory.EVOSKILL]: 'EvoSkill (Evolutionary Skill Induction)',
  [ToolCategory.MESHTASTIC]: 'Meshtastic Mesh Protocols',
  [ToolCategory.GNO]: 'Gno.land Execution Layer',
};
