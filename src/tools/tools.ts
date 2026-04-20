/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {ParsedArguments} from '../bin/chrome-devtools-mcp-cli-options.js';

import * as arkheTools from './arkhe.js';
import * as decentralizedTools from './decentralized.js';
import * as arkheGnuTools from './arkhe_gnu.js';
import * as arkheNetTools from './arkhe_net.js';
import * as lambdaTools from './lambda_tools.js';
import * as consoleTools from './console.js';
import * as emulationTools from './emulation.js';
import * as extensionTools from './extensions.js';
import * as inPageTools from './inPage.js';
import * as inputTools from './input.js';
import * as lighthouseTools from './lighthouse.js';
import * as memoryTools from './memory.js';
import * as logosLibraryTools from './logos_library.js';
import * as nekoTools from './neko.js';
import * as networkTools from './network.js';
import * as oasisTools from './oasis.js';
import * as osCathedralTools from './os_cathedral.js';
import * as spectraTools from './spectra.js';
import * as tauTools from './tau.js';
import * as pagesTools from './pages.js';
import * as performanceTools from './performance.js';
import * as screencastTools from './screencast.js';
import * as screenshotTools from './screenshot.js';
import * as scriptTools from './script.js';
import * as slimTools from './slim/tools.js';
import * as snapshotTools from './snapshot.js';
import * as storageTools from './storage.js';
import type {ToolDefinition} from './ToolDefinition.js';

export const createTools = (args: ParsedArguments) => {
  const rawTools = args.slim
    ? Object.values(slimTools)
    : [
        ...Object.values(consoleTools),
        ...Object.values(emulationTools),
        ...Object.values(extensionTools),
        ...Object.values(inPageTools),
        ...Object.values(inputTools),
        ...Object.values(lighthouseTools),
        ...Object.values(memoryTools),
        ...Object.values(networkTools),
        ...Object.values(pagesTools),
        ...Object.values(performanceTools),
        ...Object.values(screencastTools),
        ...Object.values(screenshotTools),
        ...Object.values(scriptTools),
        ...Object.values(snapshotTools),
        ...Object.values(storageTools),
        ...Object.values(arkheTools),
        ...Object.values(decentralizedTools),
        ...Object.values(arkheGnuTools),
        ...Object.values(arkheNetTools),
        ...Object.values(lambdaTools),
        ...Object.values(osCathedralTools),
        ...Object.values(spectraTools),
        ...Object.values(tauTools),
        ...Object.values(logosLibraryTools),
        ...Object.values(nekoTools),
        ...Object.values(oasisTools),
      ];

  const tools = [];
  for (const tool of rawTools) {
    if (typeof tool === 'function') {
      const toolDef = tool(args) as unknown as ToolDefinition;
      if (toolDef && toolDef.name) {
        tools.push(toolDef);
      }
    } else if (tool && (tool as ToolDefinition).name) {
      tools.push(tool as ToolDefinition);
    }
  }

  tools.sort((a, b) => {
    return a.name.localeCompare(b.name);
  });

  return tools;
};
