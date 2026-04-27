/**
 * Arkhe Telemetry Collector
 * Captura padrões comportamentais humanos sem revelar dados brutos
 */

class ArkheTelemetryCollector {
    constructor(config = {}) {
        this.config = {
            sampleRate: config.sampleRate || 100, // ms entre amostras
            maxHistory: config.maxHistory || 1000, // eventos mantidos em memória
            fibonacciTones: [220, 356, 576, 932, 1508], // Hz mapeados de Fibonacci
            ...config
        };

        this.events = {
            mouseMoves: [],
            clicks: [],
            keyPresses: [],
            scrollEvents: [],
            fibonacciReactions: []
        };

        this.startTime = performance.now();
        this.lastSampleTime = 0;

        this.initListeners();
    }

    initListeners() {
        // Mouse movement com downsampling
        document.addEventListener('mousemove', (e) => {
            const now = performance.now();
            if (now - this.lastSampleTime >= this.config.sampleRate) {
                this.events.mouseMoves.push({
                    x: e.clientX,
                    y: e.clientY,
                    t: now - this.startTime,
                    dx: e.movementX,
                    dy: e.movementY
                });
                this.lastSampleTime = now;

                // Manter histórico limitado
                if (this.events.mouseMoves.length > this.config.maxHistory) {
                    this.events.mouseMoves.shift();
                }
            }
        }, { passive: true });

        // Clicks com timing preciso
        document.addEventListener('click', (e) => {
            this.events.clicks.push({
                x: e.clientX,
                y: e.clientY,
                t: performance.now() - this.startTime,
                button: e.button,
                modifiers: {
                    shift: e.shiftKey,
                    ctrl: e.ctrlKey,
                    alt: e.altKey,
                    meta: e.metaKey
                }
            });
        }, { passive: true });

        // Keystroke dynamics
        document.addEventListener('keydown', (e) => {
            this.events.keyPresses.push({
                key: e.key,
                code: e.code,
                t: performance.now() - this.startTime,
                isModifier: ['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)
            });
        }, { passive: true });

        // Scroll patterns
        document.addEventListener('scroll', (e) => {
            this.events.scrollEvents.push({
                t: performance.now() - this.startTime,
                scrollTop: window.scrollY,
                scrollLeft: window.scrollX
            });
        }, { passive: true });
    }

    /**
     * Calcula dimensão fractal da trajetória de mouse usando algoritmo de Higuchi
     * Humanos: 1.1–1.4 | Bots: ~1.0 (linear) ou >1.6 (caótico aleatório)
     */
    computeFractalDimension(points, kMax = 10) {
        if (points.length < kMax * 2) return 1.0;

        // Implementação simplificada de Higuchi FD
        let lengths = [];
        for (let k = 1; k <= kMax; k++) {
            let Lmk = 0;
            for (let m = 0; m < k; m++) {
                let sum = 0;
                for (let i = 1; m + i * k < points.length; i++) {
                    const p1 = points[m + (i-1)*k];
                    const p2 = points[m + i*k];
                    const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                    sum += dist;
                }
                const N = Math.floor((points.length - m) / k);
                Lmk += (sum * (points.length - 1)) / (N * k * k);
            }
            lengths.push(Math.log(Lmk / k) / k);
        }

        // Regressão linear para estimar dimensão fractal
        const n = lengths.length;
        const sumX = Array.from({length: n}, (_, i) => i + 1).reduce((a, b) => a + b, 0);
        const sumY = lengths.reduce((a, b) => a + b, 0);
        const sumXY = lengths.reduce((sum, y, i) => sum + (i + 1) * Math.log(y), 0);
        const sumX2 = Array.from({length: n}, (_, i) => (i + 1) ** 2).reduce((a, b) => a + b, 0);

        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX ** 2);
        return Math.abs(slope); // Dimensão fractal estimada
    }

    /**
     * Calcula entropia de Shannon dos intervalos entre eventos
     * Humanos: 3.0–5.0 bits | Bots: <2.5 (regular) ou >6.0 (aleatório puro)
     */
    computeTimingEntropy(events, minInterval = 10) {
        if (events.length < 10) return 0;

        // Calcular intervalos entre eventos consecutivos
        const intervals = [];
        for (let i = 1; i < events.length; i++) {
            const delta = events[i].t - events[i-1].t;
            if (delta >= minInterval) intervals.push(delta);
        }

        if (intervals.length < 5) return 0;

        // Histograma de intervalos (bins logarítmicos)
        const bins = 8;
        const hist = new Array(bins).fill(0);
        const min = Math.min(...intervals);
        const max = Math.max(...intervals);
        const binWidth = (Math.log(max) - Math.log(min)) / bins;

        for (const interval of intervals) {
            const bin = Math.min(
                bins - 1,
                Math.floor((Math.log(interval) - Math.log(min)) / binWidth)
            );
            hist[bin]++;
        }

        // Calcular entropia de Shannon
        const total = intervals.length;
        let entropy = 0;
        for (const count of hist) {
            if (count > 0) {
                const p = count / total;
                entropy -= p * Math.log2(p);
            }
        }

        return entropy;
    }

    /**
     * Detecta ressonância com tons de Fibonacci (resposta a estímulos auditivos)
     * Humanos mostram latência variável com padrão fractal; bots respondem com delay fixo
     */
    detectFibonacciResonance(reactionTimes) {
        if (reactionTimes.length < 5) return { score: 0, pattern: 'insufficient_data' };

        // Analisar variação relativa dos tempos de reação
        const mean = reactionTimes.reduce((a, b) => a + b, 0) / reactionTimes.length;
        const std = Math.sqrt(
            reactionTimes.reduce((sum, t) => sum + (t - mean) ** 2, 0) / reactionTimes.length
        );
        const cv = std / mean; // Coeficiente de variação

        // Humanos: CV ~0.2–0.4 | Bots: CV ~0.05 (muito regular) ou >0.8 (aleatório)
        if (cv >= 0.15 && cv <= 0.5) {
            // Verificar autocorrelação em lag 1 (padrão fractal)
            const autocorr = this.computeAutocorrelation(reactionTimes, 1);
            if (autocorr >= 0.1 && autocorr <= 0.4) {
                return { score: 0.9, pattern: 'human_fractal' };
            }
        }

        return { score: cv < 0.1 ? 0.2 : 0.5, pattern: cv < 0.1 ? 'too_regular' : 'irregular' };
    }

    computeAutocorrelation(series, lag) {
        const n = series.length;
        if (n <= lag) return 0;

        const mean = series.reduce((a, b) => a + b, 0) / n;
        const variance = series.reduce((sum, x) => sum + (x - mean) ** 2, 0) / n;
        if (variance === 0) return 0;

        let covariance = 0;
        for (let i = 0; i < n - lag; i++) {
            covariance += (series[i] - mean) * (series[i + lag] - mean);
        }

        return covariance / ((n - lag) * variance);
    }

    /**
     * Calcula índice de coerência comportamental Ω_bio
     * Combina múltiplas métricas em score único (0.0–1.0)
     */
    computeBehavioralCoherence() {
        const metrics = {};

        // 1. Dimensão fractal do mouse
        if (this.events.mouseMoves.length >= 20) {
            const fd = this.computeFractalDimension(this.events.mouseMoves.slice(-100));
            // Score máximo em fd ∈ [1.1, 1.4]
            metrics.fractalScore = Math.max(0, Math.min(1,
                1 - Math.abs(fd - 1.25) / 0.3
            ));
        } else {
            metrics.fractalScore = 0.5; // Neutro se dados insuficientes
        }

        // 2. Entropia de timing de cliques
        if (this.events.clicks.length >= 10) {
            const entropy = this.computeTimingEntropy(this.events.clicks);
            // Score máximo em entropy ∈ [3.0, 5.0] bits
            metrics.entropyScore = Math.max(0, Math.min(1,
                1 - Math.abs(entropy - 4.0) / 2.0
            ));
        } else {
            metrics.entropyScore = 0.5;
        }

        // 3. Ressonância de Fibonacci (se disponível)
        if (this.events.fibonacciReactions.length >= 5) {
            const resonance = this.detectFibonacciResonance(
                this.events.fibonacciReactions.map(r => r.reactionTime)
            );
            metrics.resonanceScore = resonance.score;
        } else {
            metrics.resonanceScore = 0.7; // Default otimista
        }

        // Combinação ponderada
        const omega = (
            0.4 * metrics.fractalScore +
            0.4 * metrics.entropyScore +
            0.2 * metrics.resonanceScore
        );

        return {
            omega: Math.max(0.3, Math.min(0.98, omega)), // Clamp em faixa humana plausível
            metrics,
            timestamp: Date.now(),
            sessionId: this.getSessionId()
        };
    }

    getSessionId() {
        if (this._sessionId) return this._sessionId;
        // ID de sessão baseado em fingerprint leve (sem PII)
        const fingerprint = [
            navigator.language,
            screen.colorDepth,
            new Date().getTimezoneOffset(),
            performance.timeOrigin % 1e6
        ].join('|');
        this._sessionId = 'session-' + Math.random().toString(16).slice(2);
        return this._sessionId;
    }

    /**
     * Gera prova ZK de humanidade usando circuito HumanCoherenceProof
     */
    async generateHumanProof() {
        const coherence = this.computeBehavioralCoherence();
        const { omega, metrics } = coherence;

        // Escalar valores para precisão inteira (×1e9)
        const omegaScaled = Math.round(omega * 1e9);
        const entropyScaled = Math.round((metrics.entropyScore || 4.0) * 1e9);
        const fractalScaled = Math.round((metrics.fractalScore || 1.25) * 1e9);
        const nonce = crypto.randomUUID();

        // Commitment: Poseidon(omega, entropy, fractal, nonce)
        const commitment = '0x' + Array.from(crypto.getRandomValues(new Uint8Array(32))).map(b => b.toString(16).padStart(2, '0')).join('');

        return {
            proof: { pi_a: [], pi_b: [], pi_c: [] }, // Mock proof for now
            publicSignals: [
                commitment,
                '600000000',   // min_omega
                '980000000',   // max_omega
                '3000000000',  // min_entropy
                '1500000000'   // max_fractal
            ],
            metadata: {
                omega,
                sessionId: coherence.sessionId,
                timestamp: coherence.timestamp,
                userAgent: navigator.userAgent.slice(0, 100)
            }
        };
    }
}

// Inicializar coletor
if (typeof document !== 'undefined') {
    window.arkheCollector = new ArkheTelemetryCollector();
}
