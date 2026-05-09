
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { finalizeEvent, generateSecretKey, getPublicKey, Relay } from 'nostr-tools';

import { logger } from './logger';

// Arkhe Constellation Relays (using public relays for the simulation)
const RELAYS = ['wss://relay.damus.io', 'wss://nos.lol'];

// Generate a server key for the Arkhe Node
const sk = generateSecretKey();
export const NOSTR_PUBKEY = getPublicKey(sk);

export async function publishToNostr(content: string, tags: string[][] = []) {
    try {
        const event = {
            kind: 1,
            created_at: Math.floor(Date.now() / 1000),
            tags: [['t', 'arkhe'], ...tags],
            content: content,
        };
        
        const signedEvent = finalizeEvent(event, sk);

        const publishPromises = RELAYS.map(async (url) => {
            try {
                const relay = await Relay.connect(url);
                await relay.publish(signedEvent);
                relay.close();
            } catch (e) {
                logger.error(`🜏 [NOSTR] Falha ao publicar no relay ${url}`);
            }
        });

        await Promise.allSettled(publishPromises);
        logger.info(`🜏 [NOSTR] Evento publicado. ID: ${signedEvent.id}`);
        return signedEvent.id;
    } catch (error: any) {
        logger.error("🜏 [NOSTR] Erro na publicação: " + error);
        return null;
    }
}
