/**
 * @license
 * Copyright 2026 Arkhe Network
 * SPDX-License-Identifier: Apache-2.0
 */

import { logger } from '@arkhe/shared';
import { Controller, Post, Body } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';

@ApiTags('lambda')
@Controller('api/v1/lambda')
export class LambdaController {
  @Post('tick')
  @ApiOperation({ summary: 'Solicita um pulso de reconciliação' })
  async tick(@Body() payload: { dreamAlignment: number }) {
    logger.info({ msg: 'Reconciliation tick requested', payload });
    // Mocking reconciliation result
    return {
      lambdaK: 0.9992,
      status: 'stable',
      timestamp: new Date().toISOString()
    };
  }
}
