import {
  HomomorphicCryptoEngine,
  PrivacyBudgetManager,
  SecurityLevel,
  OperationType
} from './homo_privacy_221';

describe('Substrato 221: Privacidade Homomórfica', () => {

  // ─── TESTE 1: Geração de chaves ───────────────────────
  test('T1: Deve gerar par de chaves homomórficas', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    const keys = engine.generateKeys();

    expect(keys.publicKey).toBeDefined();
    expect(keys.secretKey).toBeDefined();
    expect(keys.publicKey.length).toBeGreaterThan(0);
    expect(keys.secretKey.length).toBeGreaterThan(0);
  });

  // ─── TESTE 2: Criptografia e decriptografia ────────────
  test('T2: Deve criptografar e decriptografar dados', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    const data = [1.5, 2.5, 3.5, 4.5];
    const encrypted = engine.encrypt(data);

    expect(encrypted.data).toBeDefined();
    expect(encrypted.noiseBudget).toBeGreaterThan(0);

    const decrypted = engine.decrypt(encrypted);
    expect(decrypted.length).toBe(data.length);
  });

  // ─── TESTE 3: Adição homomórfica ──────────────────────
  test('T3: Deve realizar adição sobre dados cifrados', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    const a = engine.encrypt([1.0, 2.0]);
    const b = engine.encrypt([3.0, 4.0]);

    const result = engine.add(a, b);

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
    expect(result.noiseBudgetConsumed).toBeGreaterThan(0);
  });

  // ─── TESTE 4: Multiplicação homomórfica ───────────────
  test('T4: Deve realizar multiplicação sobre dados cifrados', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    const a = engine.encrypt([2.0, 3.0]);
    const b = engine.encrypt([4.0, 5.0]);

    const result = engine.multiply(a, b);

    expect(result.success).toBe(true);
    expect(result.output).toBeDefined();
    expect(result.noiseBudgetConsumed).toBe(4);
  });

  // ─── TESTE 5: Orçamento de ruído ──────────────────────
  test('T5: Orçamento de ruído deve diminuir após operações', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    const initialBudget = engine.noiseBudget;

    const a = engine.encrypt([1.0]);
    const b = engine.encrypt([2.0]);
    engine.add(a, b);

    expect(engine.noiseBudget).toBeLessThan(initialBudget);
  });

  // ─── TESTE 6: Falha por orçamento insuficiente ────────
  test('T6: Deve falhar quando orçamento de ruído é insuficiente', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    // Consumir todo o orçamento
    engine.noiseBudget = 1;

    const a = engine.encrypt([1.0]);
    const b = engine.encrypt([2.0]);
    const result = engine.multiply(a, b); // Custa 4

    expect(result.success).toBe(false);
    expect(result.error).toContain('Insufficient noise budget');
  });

  // ─── TESTE 7: Gerenciador de orçamento ────────────────
  test('T7: Deve alocar e consumir orçamento de privacidade', () => {
    const manager = new PrivacyBudgetManager('test_manager', 100.0);

    const allocated = manager.allocateBudget('api_1', 10.0);
    expect(allocated).toBe(true);

    const consumed = manager.consumeBudget('api_1', 2.0);
    expect(consumed).toBe(true);

    const budget = manager.getBudgetStatus('api_1');
    expect(budget).not.toBeNull();
    expect(budget!.epsilon).toBe(8.0);
  });

  // ─── TESTE 8: Níveis de segurança ─────────────────────
  test('T8: Deve suportar diferentes níveis de segurança', () => {
    const engine128 = new HomomorphicCryptoEngine('eng128', SecurityLevel.TC128);
    const engine192 = new HomomorphicCryptoEngine('eng192', SecurityLevel.TC192);
    const engine256 = new HomomorphicCryptoEngine('eng256', SecurityLevel.TC256);

    expect(engine128.schemeParams.polyModulusDegree).toBe(4096);
    expect(engine192.schemeParams.polyModulusDegree).toBe(8192);
    expect(engine256.schemeParams.polyModulusDegree).toBe(16384);
  });

  // ─── TESTE 9: Auditoria ───────────────────────────────
  test('T9: Deve registrar operações no log de auditoria', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    const a = engine.encrypt([1.0]);
    const b = engine.encrypt([2.0]);
    engine.add(a, b);

    const log = engine.getAuditLog();
    expect(log.length).toBeGreaterThan(0);
    expect(log[0].operation).toBe(OperationType.ADD);
  });

  // ─── TESTE 10: Verificação de capacidade ──────────────
  test('T10: Deve verificar se operação pode ser realizada', () => {
    const engine = new HomomorphicCryptoEngine('test_engine', SecurityLevel.TC128);
    engine.generateKeys();

    expect(engine.canPerformOperation(2)).toBe(true);

    engine.noiseBudget = 1;
    expect(engine.canPerformOperation(2)).toBe(false);
  });
});
