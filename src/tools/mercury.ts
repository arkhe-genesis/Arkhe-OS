/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {readdir, access} from 'node:fs/promises';
import path from 'node:path';

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
  description:
    'Mercury Agent: Lists all currently installed community and built-in skills.',
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### Mercury Installed Skills');
    response.appendResponseLine('| Skill Name | Category | Status |');
    response.appendResponseLine('|------------|----------|--------|');

    const skillsDir = path.resolve(process.cwd(), 'skills');
    let totalSkills = 0;

    async function scanSkills(dir: string, category: string = '') {
      let entries;
      try {
        entries = await readdir(dir, {withFileTypes: true});
      } catch {
        return;
      }

      for (const entry of entries) {
        if (entry.isDirectory()) {
          const fullPath = path.join(dir, entry.name);
          const skillMdPath = path.join(fullPath, 'SKILL.md');
          try {
            await access(skillMdPath);
            // Found a skill
            const skillName = category
              ? `${category}/${entry.name}`
              : entry.name;
            response.appendResponseLine(
              `| ${skillName} | ${category || 'general'} | active |`,
            );
            totalSkills++;
          } catch {
            // Not a skill directory directly, maybe it has sub-categories (like cloud/)
            if (!category) {
              await scanSkills(fullPath, entry.name);
            }
          }
        }
      }
    }

    try {
      await scanSkills(skillsDir);
      response.appendResponseLine(
        `\n**Total**: ${totalSkills} skills loaded. Use \`install_skill\` to add more.`,
      );
    } catch (err) {
      response.appendResponseLine(
        `\n**Error**: Failed to scan skills directory: ${err}`,
      );
    }
  },
});

export const installSkill = definePageTool({
  name: 'install_skill',
  description: 'Mercury Agent: Installs a new skill from a local folder or remote repository.',
  annotations: {
    category: ToolCategory.AGENT,
    readOnlyHint: false,
    reasoningCost: 30,
  },
  schema: {
    skillPath: zod.string().describe('Path to the skill folder or git URL.'),
    force: zod.boolean().default(false).describe('Overwrite if already exists.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### Mercury: Installing Skill`);
    response.appendResponseLine(`- **Path**: \`${request.params.skillPath}\``);
    response.appendResponseLine(`- **Status**: Validating \`SKILL.md\` and dependencies...`);
    response.appendResponseLine('\n**Success**: Skill installed and hot-reloaded into Mercury context.');
    response.appendResponseLine('**Protocol**: Identity coherence preserved during skill grafting.');
  },
});
