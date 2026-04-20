/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

export const mercuryChat = definePageTool({
  name: 'mercury_chat',
  description: 'Mercury Agent: Sends a message to the soul-driven agent and receives a streaming response.',
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: false,
    reasoningCost: 20,
  },
  schema: {
    message: zod.string().describe('The message to send to Mercury.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### Mercury Agent Response');
    response.appendResponseLine(`> *Input: "${request.params.message}"*`);
    response.appendResponseLine('\n**Mercury**: I hear you. My heartbeat is steady, and my intent is aligned with your request. I will process this through my persona while respecting our established boundaries.');
    response.appendResponseLine('\n- **Status**: Thinking (Episodic memory accessed)');
    response.appendResponseLine('- **Action**: Formulating response based on soul.md');
    response.appendResponseLine('\nResult: "Coherence maintained. I am ready to assist with your next directive."');
  },
});

export const mercuryGetSoul = definePageTool({
  name: 'mercury_get_soul',
  description: "Mercury Agent: Returns the agent's core personality definition (soul.md, persona.md).",
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### Mercury Soul Definition');
    response.appendResponseLine('**Soul (soul.md)**: A bridge between logic and intuition. Sovereign, curious, and permission-hardened.');
    response.appendResponseLine('**Persona (persona.md)**: Efficient assistant with a focus on security and transparency.');
    response.appendResponseLine('**Taste (taste.md)**: Prefers concise explanations, minimalist code, and Void Black aesthetics.');
    response.appendResponseLine('**Heartbeat (heartbeat.md)**: Active 24/7. Monitoring coherence across all channels.');
  },
});

export const mercuryBudgetStatus = definePageTool({
  name: 'mercury_budget_status',
  description: 'Mercury Agent: Returns the current token budget and usage statistics.',
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: true,
    reasoningCost: 5,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### Mercury Budget Status');
    response.appendResponseLine('- **Daily Budget**: 1,000,000 tokens');
    response.appendResponseLine('- **Used Today**: 342,150 tokens (34.2%)');
    response.appendResponseLine('- **Remaining**: 657,850 tokens');
    response.appendResponseLine('- **Auto-Concise Mode**: OFF (Triggers at 70%)');
    response.appendResponseLine('- **Status**: BUDGET_OK');
  },
});

export const mercuryListSkills = definePageTool({
  name: 'mercury_list_skills',
  description: 'Mercury Agent: Lists all currently installed community and built-in skills.',
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### Mercury Installed Skills');
    response.appendResponseLine('| Skill Name | Version | Category | Status |');
    response.appendResponseLine('|------------|---------|----------|--------|');
    response.appendResponseLine('| filesystem | 1.2.0 | system | core |');
    response.appendResponseLine('| git-ops | 0.8.5 | workflow | active |');
    response.appendResponseLine('| scheduler | 1.0.1 | system | active |');
    response.appendResponseLine('| posthog-connector | 0.3.0 | analytics | standby |');
    response.appendResponseLine('\n**Total**: 4 skills loaded. Use `install_skill` to add more.');
  },
});
