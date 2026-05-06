// tests/integration/polymath_parser.test.ts
import { PolymathParser } from '../../src/parser/polymath_parser';
import * as fs from 'fs';
import * as path from 'path';

describe('PolymathParser', () => {
  let parser: PolymathParser;

  beforeAll(() => {
    parser = new PolymathParser();
  });

  test('✅ Should detect Python file', () => {
    const lang = parser.detectLanguage('main.py');
    expect(lang).toBe('python');
  });

  test('✅ Should detect Solidity file', () => {
    const lang = parser.detectLanguage('token.sol');
    expect(lang).toBe('solidity');
  });

  test('✅ Should scan a multi-language directory', () => {
    const dir = __dirname;
    const graphs = parser.scanDirectory(dir);
    expect(Object.keys(graphs).length).toBeGreaterThan(0);
    const metrics = parser.computeMetrics(graphs);
    expect(metrics._global.global_coherence).toBeDefined();
  });

  test('✅ Coherence of a single parsed file should be consistent', () => {
    const filePath = __filename;
    const graph1 = parser.parseFile(filePath);
    const graph2 = parser.parseFile(filePath);
    expect(graph1.coherence()).toBe(graph2.coherence());
  });

  test('Should handle unknown language', () => {
    const lang = parser.detectLanguage('unknown.txt');
    expect(lang).toBe('unknown');
  });
});
