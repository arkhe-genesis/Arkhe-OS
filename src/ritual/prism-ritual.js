/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// src/ritual/prism-ritual.js
// Bloco #300.1.A — O Pórtico Dourado
// Responsabilidade: Transmutar latência em experiência estética

export class CrystallizationRitual {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {return;}
    this.ctx = this.canvas.getContext('2d');
    this.phase = 'invocation'; // invocation | channeling | integration | sealing
    this.particles = [];
    this.frameId = null;
    this.resize();
    this.resizeHandler = () => this.resize();
    window.addEventListener('resize', this.resizeHandler);
  }

  resize() {
    if (!this.canvas) {return;}
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.w = rect.width;
    this.h = rect.height;
    this.cx = this.w / 2;
    this.cy = this.h / 2;
  }

  // Opcode 0x297: RITUAL_INITIATION
  async initiate(totalBytes) {
    this.totalBytes = totalBytes;
    this.received = 0;
    this.startTime = Date.now();
    this.phase = 'invocation';
    this.animate();
    return new Promise(resolve => {
      this.resolve = resolve;
    });
  }

  updateProgress(receivedBytes) {
    this.received = receivedBytes;
    this.progress = Math.min(this.received / this.totalBytes, 1);

    // Transição de fases axiomáticas
    if (this.progress < 0.05) {this.phase = 'invocation';}
    else if (this.progress < 0.85) {this.phase = 'channeling';}
    else if (this.progress < 1.0) {this.phase = 'integration';}
    else if (this.phase !== 'sealing') {
      this.phase = 'sealing';
      setTimeout(() => {
        this.complete();
        this.resolve?.();
      }, 1500); // Tempo de contemplação do selamento
    }
  }

  draw() {
    const { ctx, w, h, cx, cy, progress } = this;
    if (!ctx) {return;}

    // Rastro etéreo (limpar com opacidade para efeito de rastro)
    ctx.fillStyle = 'rgba(2, 6, 23, 0.15)';
    ctx.fillRect(0, 0, w, h);

    const baseRadius = Math.min(w, h) * 0.25;
    const time = Date.now() * 0.001;

    // Paleta da Catedral: Ouro (45°) → Âmbar (30°) conforme progresso
    const hue = 45 - (progress * 15);
    const alpha = 0.4 + (progress * 0.6);

    ctx.strokeStyle = `hsla(${hue}, 90%, 60%, ${alpha})`;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';

    // Geometria Sagrada 1: Círculo Externo (pulsação do éter)
    const pulse = 1 + Math.sin(time * (3 + progress * 2)) * 0.03 * (1 - progress);
    ctx.beginPath();
    ctx.arc(cx, cy, baseRadius * pulse, 0, Math.PI * 2 * progress);
    ctx.stroke();

    // Geometria Sagrada 2: Círculo Interno (respiração do embrião)
    ctx.strokeStyle = `hsla(${hue + 20}, 80%, 70%, ${alpha * 0.4})`;
    ctx.beginPath();
    const breath = 1 + Math.sin(time * 2) * 0.05;
    ctx.arc(cx, cy, baseRadius * 0.6 * breath, 0, Math.PI * 2);
    ctx.stroke();

    // Vesica Piscis (símbolo de união oppositorum) — surge no meio do download
    if (progress > 0.3) {
      ctx.strokeStyle = `hsla(${hue}, 70%, 80%, ${(progress - 0.3) * 0.5})`;
      const offset = baseRadius * 0.4 * Math.min((progress - 0.3) * 2, 1);
      ctx.beginPath();
      ctx.arc(cx - offset/2, cy, baseRadius * 0.5, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx + offset/2, cy, baseRadius * 0.5, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Partículas de Dados (stream chunks visualizados)
    if (this.particles.length < 60 && Math.random() > 0.9) {
      this.particles.push({
        angle: Math.random() * Math.PI * 2,
        dist: baseRadius * (0.3 + Math.random() * 0.7),
        speed: 0.005 + Math.random() * 0.01,
        life: 1,
        size: 1 + Math.random() * 2
      });
    }

    this.particles.forEach((p, i) => {
      p.angle += p.speed * (1 + progress); // Acelera conforme baixa
      p.life -= 0.008;
      const px = cx + Math.cos(p.angle) * p.dist;
      const py = cy + Math.sin(p.angle) * p.dist;

      ctx.fillStyle = `hsla(${hue}, 100%, ${70 + p.life * 30}%, ${p.life})`;
      ctx.beginPath();
      ctx.arc(px, py, p.size * p.life, 0, Math.PI * 2);
      ctx.fill();

      if (p.life <= 0) {this.particles.splice(i, 1);}
    });

    // Métricas de Transparência (texto monástico)
    this.drawMetrics(cx, cy + baseRadius + 50, hue);
  }

  drawMetrics(x, y, _hue) {
    const { ctx, received, totalBytes, phase, startTime } = this;
    const mb = (received / 1048576).toFixed(1);
    const totalMb = (totalBytes / 1048576).toFixed(1);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    const phases = {
      'invocation': 'Invocando o Embrião...',
      'channeling': 'Canalizando o Éter...',
      'integration': 'Suturando Matrizes Quantizadas...',
      'sealing': 'Selando o Cristal...'
    };

    ctx.font = '14px "SF Mono", monospace';
    ctx.fillStyle = '#e2e8f0';
    ctx.textAlign = 'center';
    ctx.fillText(phases[phase] || '', x, y);

    ctx.font = '12px "SF Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`${mb} / ${totalMb} MB  •  ${(this.progress * 100).toFixed(1)}%`, x, y + 20);
    ctx.fillText(`${elapsed}s  •  Coherence: ${this.calculateSignature().slice(0, 12)}...`, x, y + 36);
  }

  calculateSignature() {
    // Embrião do opcode 0x299 (COHERENCE_HASH) para federação futura
    const seed = this.received ^ this.totalBytes;
    return btoa(String.fromCharCode(
      (seed & 0xFF), ((seed >> 8) & 0xFF),
      ((seed >> 16) & 0xFF), ((seed >> 24) & 0xFF)
    )).replace(/=/g, '');
  }

  animate() {
    this.draw();
    this.frameId = requestAnimationFrame(() => this.animate());
  }

  complete() {
    if (this.frameId) {cancelAnimationFrame(this.frameId);}
    // Flash final de selamento
    const { ctx, w, h } = this;
    if (ctx) {
        ctx.fillStyle = 'rgba(251, 191, 36, 0.3)'; // Âmbar dourado
        ctx.fillRect(0, 0, w, h);
    }
  }

  destroy() {
    if (this.frameId) {cancelAnimationFrame(this.frameId);}
    window.removeEventListener('resize', this.resizeHandler);
  }
}
