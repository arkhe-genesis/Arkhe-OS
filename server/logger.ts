
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { logs, SeverityNumber } from '@opentelemetry/api-logs';
import type { AnyValueMap } from '@opentelemetry/api-logs';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { LoggerProvider, BatchLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';

const parseableUrl = (typeof process !== 'undefined' && process.env.PARSEABLE_URL) || 'https://ingestor.parseable.com/v1/logs';
const parseableToken = (typeof process !== 'undefined' && process.env.PARSEABLE_AUTH_TOKEN) || '';
const parseableTenant = (typeof process !== 'undefined' && process.env.PARSEABLE_TENANT) || '';
const chainId = (typeof process !== 'undefined' && process.env.CHAIN_ID) || '2147483647'; // 0xCAFEBABE

const exporter = new OTLPLogExporter({
  url: parseableUrl,
  headers: {
    'Authorization': parseableToken,
    'X-P-Stream': 'arkhen-security-logs',
    'X-P-Tenant': parseableTenant
  }
});

const loggerProvider = new LoggerProvider({
  resource: resourceFromAttributes({
    [SEMRESATTRS_SERVICE_NAME]: 'arkhe-node',
    'chain.id': chainId,
  }),
  processors: [
    new BatchLogRecordProcessor(exporter)
  ]
});

logs.setGlobalLoggerProvider(loggerProvider);

const otelLogger = logs.getLogger('arkhe-logger');

export const logger = {
  info: (message: string, attributes?: AnyValueMap) => {
    console.log(`[INFO] ${message}`, attributes || '');
    otelLogger.emit({
      severityNumber: SeverityNumber.INFO,
      severityText: 'INFO',
      body: message,
      attributes,
    });
  },
  warn: (message: string, attributes?: AnyValueMap) => {
    console.warn(`[WARN] ${message}`, attributes || '');
    otelLogger.emit({
      severityNumber: SeverityNumber.WARN,
      severityText: 'WARN',
      body: message,
      attributes,
    });
  },
  error: (message: string, attributes?: AnyValueMap) => {
    console.error(`[ERROR] ${message}`, attributes || '');
    otelLogger.emit({
      severityNumber: SeverityNumber.ERROR,
      severityText: 'ERROR',
      body: message,
      attributes,
    });
  },
  debug: (message: string, attributes?: AnyValueMap) => {
    console.debug(`[DEBUG] ${message}`, attributes || '');
    otelLogger.emit({
      severityNumber: SeverityNumber.DEBUG,
      severityText: 'DEBUG',
      body: message,
      attributes,
    });
  }
};
