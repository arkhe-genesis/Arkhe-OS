/**
 * ARKHE CATHEDRAL — Substrate 773 Hook 773.1
 * Simulação da Dinâmica de Kuramoto com escala Tau reduzida
 *
 * Este script verifica a aceleração da convergência prevista pela Lei de Escala Tau
 * reduzindo o dt na simulação de Kuramoto e observando r(t).
 */

const { Arkhe, CONSTANTS } = require('./arkhe.js');

const arkhe = new Arkhe();
const N = 120; // 120 vertices of the 600-cell
const K = CONSTANTS.K_BASE_DEFAULT;
const T_total = 50;

console.log("==================================================");
console.log("ARKHE CATHEDRAL — Substrate 773 Hook 773.1");
console.log("Simulação de Kuramoto com escala Tau reduzida");
console.log(`N = ${N}, K = ${K}, T_total = ${T_total}`);
console.log("==================================================\n");

// 1. Simulação Padrão (dt normal)
console.log("1. Simulação Padrão (dt = 0.05)");
arkhe.initKuramoto(N, K);
const dt_standard = 0.05;
const history_standard = arkhe.kuramoto.simulate(T_total, dt_standard);
const final_r_standard = history_standard.length > 0 ? history_standard[history_standard.length - 1].r : 0;
console.log(`Convergência final: r(T) = ${final_r_standard.toFixed(6)}\n`);

// 2. Simulação com Lei Tau (dt reduzido)
console.log("2. Simulação Lei Tau - LogicFolding (dt = 0.005)");
arkhe.initKuramoto(N, K);
const dt_tau = 0.005;
const history_tau = arkhe.kuramoto.simulate(T_total, dt_tau);
const final_r_tau = history_tau.length > 0 ? history_tau[history_tau.length - 1].r : 0;
console.log(`Convergência final: r(T) = ${final_r_tau.toFixed(6)}\n`);

console.log("Conclusão: Simulação completa. (Aceleração observada se r(T)_tau > r(T)_padrao na implementação real)");
