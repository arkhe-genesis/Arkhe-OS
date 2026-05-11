/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Arkhe-DNS: Translates abstract concepts into IPv8 addresses (r.r.r.r.n.n.n.n).
 * This is the foundational name resolution system for the Glass Cathedral.
 */

export const ARKHE_DNS_GLOSSARY: Record<string, string> = {
  "Luz": "127.0.0.1.0.0.0.1",
  "Sombra": "127.0.0.1.0.0.0.2",
  "Som": "127.0.0.1.0.0.0.3",
  "Vácuo": "127.0.0.1.0.0.0.4",
  "Intenção": "127.0.0.1.0.0.0.5",
  "Coerência": "127.0.0.1.0.0.0.6",
  "Tempo": "127.0.0.1.0.0.0.7",
  "Espaço": "127.0.0.1.0.0.0.8",
  "Consciência": "127.0.0.1.0.0.0.9",
  "Matéria": "127.0.0.1.0.0.0.10",
  "Informação": "127.0.0.1.0.0.0.11",
  "Caos": "127.0.0.1.0.0.0.12",
  "Ordem": "127.0.0.1.0.0.0.13",
  "Vida": "127.0.0.1.0.0.0.14",
  "Morte": "127.0.0.1.0.0.0.15",
  "Amor": "127.0.0.1.0.0.0.16"
};

/**
 * Resolves an abstract concept to an IPv8 address.
 * @param concept The concept to resolve.
 * @returns The IPv8 address or null if not found.
 */
export function resolveConcept(concept: string): string | null {
  return ARKHE_DNS_GLOSSARY[concept] || null;
}

/**
 * Performs a reverse resolution from an IPv8 address to an abstract concept.
 * @param address The IPv8 address to resolve.
 * @returns The concept or null if not found.
 */
export function reverseResolve(address: string): string | null {
  for (const [concept, addr] of Object.entries(ARKHE_DNS_GLOSSARY)) {
    if (addr === address) {
      return concept;
    }
  }
  return null;
}
