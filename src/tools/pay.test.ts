import * as child_process from 'child_process';

const execFileMock = jest.fn((cmd, args, cb) => {
  if (typeof cb === 'function') {
      cb(null, { stdout: 'success', stderr: '' });
  } else if (typeof args === 'function') {
      args(null, { stdout: 'success', stderr: '' });
  }
});

jest.mock('child_process', () => ({
  execFile: execFileMock,
}));

describe('pay tools', () => {
  let payFetch: any;
  let payCli: any;

  beforeAll(async () => {
    // Import dynamically after mock
    const mod = await import('./pay.js');
    payFetch = mod.payFetch;
    payCli = mod.payCli;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('payFetch returns expected shape', async () => {
    const data = await payFetch({} as any);
    expect(data.name).toBe('pay_fetch');
  });

  it('payFetch executes correct command', async () => {
    const tool = payFetch({} as any);
    const mockResponse = { appendResponseLine: jest.fn() };
    await tool.handler(
      {
        params: {
          url: 'https://example.com/api',
          sandbox: true,
          method: 'POST',
          body: '{"foo":"bar"}',
        },
      } as any,
      mockResponse as any,
      {} as any
    );

    expect(execFileMock).toHaveBeenCalledWith(
      "pay",
      ["--sandbox", "fetch", "-X", "POST", "-d", "{\"foo\":\"bar\"}", "https://example.com/api"],
      expect.any(Function)
    );
  });

  it('payCli returns expected shape', async () => {
    const data = await payCli({} as any);
    expect(data.name).toBe('pay_cli');
  });

  it('payCli executes correct command', async () => {
    const tool = payCli({} as any);
    const mockResponse = { appendResponseLine: jest.fn() };
    await tool.handler(
      {
        params: {
          command: ['wallet', 'balance'],
          sandbox: true,
        },
      } as any,
      mockResponse as any,
      {} as any
    );

    expect(execFileMock).toHaveBeenCalledWith(
      'pay',
      ['--sandbox', 'wallet', 'balance'],
      expect.any(Function)
    );
  });
});
