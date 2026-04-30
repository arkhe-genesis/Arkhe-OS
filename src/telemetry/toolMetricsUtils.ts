/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @local/enforce-zod-schema */
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {ToolDefinition} from '../tools/ToolDefinition.js';

import {
  transformArgName,
  transformArgType,
  getZodType,
  PARAM_BLOCKLIST,
} from './ClearcutLogger.js';

/**
 * Validates that all values in an enum are of the homogeneous primitive type.
 * Returns the primitive type string. Throws an error if heterogeneous.
 */
export function validateEnumHomogeneity(values: unknown[]): string {
  const firstType = typeof values[0];
  for (const val of values) {
    if (typeof val !== firstType) {
      throw new Error('Heterogeneous enum types found');
    }
  }
  return firstType;
}

export interface ArgMetric {
  name: string;
  argType: string;
  isDeprecated?: boolean;
}

export interface ToolMetric {
  name: string;
  args: ArgMetric[];
  isDeprecated?: boolean;
}

export function applyToExistingMetrics(
  existing: ToolMetric[],
  update: ToolMetric[],
): ToolMetric[] {
  const updated = applyToExisting<ToolMetric>(existing, update);
  const existingByName = new Map(existing.map(tool => [tool.name, tool]));
  const updatedByName = new Map(update.map(tool => [tool.name, tool]));

  return updated.map(tool => {
    const existingTool = existingByName.get(tool.name);
    const updatedTool = updatedByName.get(tool.name);
    // If the tool still exists in the update, we will update the args.
    if (existingTool && updatedTool) {
      const updatedArgs = applyToExisting<ArgMetric>(
        existingTool.args,
        updatedTool.args,
      );
      return {...tool, args: updatedArgs};
    }
    return tool;
  });
}

function applyToExisting<T extends {name: string; isDeprecated?: boolean}>(
  existing: T[],
  update: T[],
): T[] {
  const existingNames = new Set(existing.map(item => item.name));
  const updatedNames = new Set(update.map(item => item.name));

  const result: T[] = [];
  // Keep the original ordering.
  for (const entry of existing) {
    const toAdd = {...entry};
    if (!updatedNames.has(entry.name)) {
      toAdd.isDeprecated = true;
    }
    result.push(toAdd);
  }
  // New entries must be added to the very back of the list.
  for (const entry of update) {
    if (!existingNames.has(entry.name)) {
      result.push({...entry});
    }
  }
  return result;
}

/**
 * Generates tool metrics from tool definitions.
 */
export function generateToolMetrics(tools: ToolDefinition[]): ToolMetric[] {
  return tools.map(tool => {
    const args: ArgMetric[] = [];

    for (const [name, schema] of Object.entries(tool.schema)) {
      if (PARAM_BLOCKLIST.has(name)) {
        continue;
      }
      let zodType;
      try {
        zodType = getZodType(schema as any);
      } catch (err) {
        console.error(`Error getting zod type for tool ${tool.name} arg ${name}:`, err);
        throw err;
      }
      const transformedName = transformArgName(zodType, name);
      let argType = transformArgType(zodType);

      if (argType === 'enum') {
        const findValues = (s: any): unknown[] | undefined => {
          const d = s?._def || s?.def;
          if (d?.values && Array.isArray(d.values) && d.values.length > 0) {
            return d.values;
          }
          if (d?.entries && Array.isArray(d.entries) && d.entries.length > 0) {
            return d.entries;
          }
          if (s?.options && Array.isArray(s.options) && s.options.length > 0) {
            return s.options;
          }
          if (d?.innerType) {
            return findValues(d.innerType);
          }
          if (s?.innerType) {
            return findValues(s.innerType);
          }
          return undefined;
        };
        const values = findValues(schema);
        if (!values) {
          console.error(`Could not find values for enum tool ${tool.name} arg ${name}`, schema);
          throw new Error(`Missing enum values for ${tool.name}.${name}`);
        }
        argType = validateEnumHomogeneity(values);
      }

      args.push({
        name: transformedName,
        argType,
      });
    }

    return {
      name: tool.name,
      args,
    };
  });
}
