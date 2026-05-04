/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { logger } from '@arkhe/shared';
import { initTRPC } from '@trpc/server';
import { fastifyTRPCPlugin } from '@trpc/server/adapters/fastify';
import Fastify from 'fastify';
import Redis from 'ioredis';
import { z } from 'zod';

const t = initTRPC.create();

const appRouter = t.router({
  getCoherence: t.procedure.query(async () => {
    return { lambda: 0.998, status: 'stable' };
  }),
  submitTelemetry: t.procedure
    .input(z.object({ nodeId: z.string(), phase: z.number() }))
    .mutation(async ({ input }) => {
      logger.info({ msg: 'Telemetry received', ...input });
      return { success: true };
    }),
});

export type AppRouter = typeof appRouter;

const fastify = Fastify({ logger: true });

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

fastify.register(fastifyTRPCPlugin, {
  prefix: '/trpc',
  trpcOptions: { router: appRouter },
});

fastify.get('/health', async () => {
  return { status: 'ok', redis: await redis.ping() };
});

const start = async () => {
  try {
    await fastify.listen({ port: 3000, host: '0.0.0.0' });
    logger.info('Fastify Telemetry Service running on port 3000');
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

void start();
