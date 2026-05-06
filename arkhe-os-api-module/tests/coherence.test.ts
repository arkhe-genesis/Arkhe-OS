import { computeStateCoherence, normalizeStateVector, complex } from '../src/index';

describe('Coherence Computation', () => {
  test('✅ State vector should normalize correctly', () => {
    const vec = [complex(1,0), complex(2,1), complex(0,3)];
    normalizeStateVector(vec);
    let normSq = vec.reduce((s, c) => s + c.re**2 + c.im**2, 0);
    expect(Math.abs(normSq - 1.0)).toBeLessThan(1e-10);
  });

  test('✅ Coherence should be in [0, 1]', () => {
    const vec = Array.from({length: 256}, () => complex(Math.random(), Math.random()));
    normalizeStateVector(vec);
    const coherence = computeStateCoherence(vec);
    expect(coherence).toBeGreaterThanOrEqual(0);
    expect(coherence).toBeLessThanOrEqual(1);
  });

  test('✅ Coherence of uniform state should be maximal', () => {
    const dim = 256;
    const uniform = Array.from({length: dim}, () => complex(1/Math.sqrt(dim), 0));
    const coherence = computeStateCoherence(uniform);
    expect(coherence).toBeCloseTo(1.0, 2);
  });
});

  test('✅ Should return 0.0 coherence for empty vector', () => {
    const coherence = computeStateCoherence([]);
    expect(coherence).toBe(0.0);
  });

  test('✅ Should return 0.0 coherence for near-zero total amplitude', () => {
    const vec = [complex(1e-12, 1e-12)];
    const coherence = computeStateCoherence(vec);
    expect(coherence).toBe(0.0);
  });
