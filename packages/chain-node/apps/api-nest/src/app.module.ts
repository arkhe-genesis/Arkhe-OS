/**
 * @license
 * Copyright 2026 Arkhe Network
 * SPDX-License-Identifier: Apache-2.0
 */

import { join } from 'node:path';

import { ApolloDriver, type ApolloDriverConfig } from '@nestjs/apollo';
import { BullModule } from '@nestjs/bullmq';
import { Module } from '@nestjs/common';
import { GraphQLModule } from '@nestjs/graphql';
import { MongooseModule } from '@nestjs/mongoose';
import { ScheduleModule } from '@nestjs/schedule';

import { HealthController } from './health.controller';
import { LambdaController } from './lambda/lambda.controller';
import { PuppeteerService } from './puppeteer.service';

@Module({
  imports: [
    GraphQLModule.forRoot<ApolloDriverConfig>({
      driver: ApolloDriver,
      autoSchemaFile: join(process.cwd(), 'src/schema.gql'),
    }),
    MongooseModule.forRoot(process.env.MONGODB_URI || 'mongodb://localhost/arkhe'),
    BullModule.forRoot({
      connection: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379'),
      },
    }),
    ScheduleModule.forRoot(),
  ],
  controllers: [HealthController, LambdaController],
  providers: [PuppeteerService],
})
export class AppModule {}
