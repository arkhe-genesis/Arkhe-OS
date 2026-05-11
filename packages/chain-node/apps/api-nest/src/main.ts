/**
 * @license
 * Copyright 2026 Arkhe Network
 * SPDX-License-Identifier: Apache-2.0
 */

import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';

import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  const config = new DocumentBuilder()
    .setTitle('Arkhe-Chain API')
    .setDescription('Orquestração de Bio-Quantum Cathedral (Sovereign Stack)')
    .setVersion('1.0')
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api-docs', app, document);

  await app.listen(process.env.PORT || 3000);
}
void bootstrap();
