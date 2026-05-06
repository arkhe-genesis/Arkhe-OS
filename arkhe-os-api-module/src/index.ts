export const complex = (re: number, im: number) => ({ re, im });

export function normalizeStateVector(vec: {re: number, im: number}[]) {
  let normSq = vec.reduce((s, c) => s + c.re**2 + c.im**2, 0);
  let norm = Math.sqrt(normSq);
  for (let i = 0; i < vec.length; i++) {
    vec[i].re /= norm;
    vec[i].im /= norm;
  }
}

export function computeStateCoherence(vec: {re: number, im: number}[]): number {
  if (vec.length === 0) return 0.0;

  let maxAmpSq = 0;
  let totalAmpSq = 0;
  for (const c of vec) {
    let ampSq = c.re**2 + c.im**2;
    if (ampSq > maxAmpSq) maxAmpSq = ampSq;
    totalAmpSq += ampSq;
  }

  if (totalAmpSq < 1e-10) return 0.0;

  let concentration = maxAmpSq / totalAmpSq;
  return Math.min(1.0, concentration * vec.length);
}
