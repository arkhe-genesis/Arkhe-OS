/**
 * @license
 * Copyright 2026 Arkhe Network
 * SPDX-License-Identifier: Apache-2.0
 */

import { Controller, Get } from '@nestjs/common';

@Controller('health')
export class HealthController {
  @Get()
  getHealth() {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }
}
