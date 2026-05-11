// substrates/v172_distributed_quantum/distributed_quantum_crystal.js
// Motor de cristalografia quântica distribuída: múltiplos observatórios sincronizados via emaranhamento interestelar

class DistributedQuantumCrystalEngine {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        this.config = {
            observatories: ['EARTH', 'MARS_ORBIT', 'PROXIMA_RELAY'], // IDs dos observatórios
            atomCountPerObs: 64000, // Total: 192k átomos distribuídos
            latticeParams: { a: 3.89, b: 3.89, c: 12.24 },
            quantumRange: { phase: [0, 2*Math.PI], amplitude: [0, 1], bell_S: [2, 2.828] },
            entanglementSyncInterval: 1000, // ms entre sincronizações de fase
            updateRate: 60,
            ...config
        };

        // Three.js setup
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            powerPreference: 'high-performance',
            premultipliedAlpha: false
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // Shader material com suporte a fase distribuída e emaranhamento inter-observatório
        this.quantumMaterial = new THREE.ShaderMaterial({
            uniforms: {
                uPhase: { value: new Float32Array(this.config.atomCountPerObs * this.config.observatories.length) },
                uAmplitude: { value: new Float32Array(this.config.atomCountPerObs * this.config.observatories.length) },
                uBellS: { value: new Float32Array(this.config.atomCountPerObs * this.config.observatories.length) },
                uObservatoryId: { value: new Float32Array(this.config.atomCountPerObs * this.config.observatories.length) },
                uEntanglementMap: { value: null },
                uInterObsEntanglement: { value: null }, // textura para pares entre observatórios
                uTime: { value: 0.0 },
                uPhaseCorrection: { value: new Float32Array(this.config.observatories.length) } // Δφ_m por observatório
            },
            vertexShader: `
                precision highp float;
                uniform float uTime;
                uniform sampler2D uEntanglementMap;
                uniform sampler2D uInterObsEntanglement;
                uniform float uPhaseCorrection[3]; // máximo 3 observatórios
                varying vec3 vPosition;
                varying float vPhase;
                varying float vAmplitude;
                varying float vBellS;
                varying float vObservatoryId;
                varying float vInterObsEntangled;

                void main() {
                    vPosition = position;
                    vObservatoryId = uObservatoryId[gl_InstanceID];

                    // Fase local + correção por observatório
                    float localPhase = mod(uPhase[gl_InstanceID] + uTime * 0.1, 6.283185);
                    float correction = uPhaseCorrection[int(vObservatoryId)];
                    vPhase = mod(localPhase + correction, 6.283185);

                    vAmplitude = uAmplitude[gl_InstanceID];
                    vBellS = uBellS[gl_InstanceID];

                    // Verificar emaranhamento inter-observatório
                    vec2 entKey = vec2(vObservatoryId, float(gl_InstanceID % 1000));
                    vInterObsEntangled = texture2D(uInterObsEntanglement, entKey / 1000.0).r;

                    // Deslocamento baseado em fase + emaranhamento
                    float displacement = sin(vPhase) * 0.1 * vAmplitude * (1.0 + vInterObsEntangled * 0.5);
                    vec3 displaced = position + normalize(position) * displacement;

                    // Parallaxe interestelar (efeito visual de distância entre observatórios)
                    if (vObservatoryId > 0.5) {
                        displaced.x += sin(uTime * 0.01) * 0.05;
                    }

                    gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
                }
            `,
            fragmentShader: `
                precision highp float;
                varying vec3 vPosition;
                varying float vPhase;
                varying float vAmplitude;
                varying float vBellS;
                varying float vObservatoryId;
                varying float vInterObsEntangled;

                vec3 hsv2rgb(vec3 c) {
                    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
                    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
                    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
                }

                void main() {
                    // Mapeamento quântico → cor com correção por observatório
                    float hue = vPhase / 6.283185;
                    float saturation = vAmplitude * (0.8 + 0.2 * vInterObsEntangled);
                    float value = (vBellS - 2.0) / (2.828 - 2.0);

                    // Cor base
                    vec3 color = hsv2rgb(vec3(hue, saturation, value));

                    // Overlay por observatório (para distinguir visualmente)
                    if (vObservatoryId < 0.5) {
                        color = mix(color, vec3(0.2, 0.6, 1.0), 0.1); // Terra: azul
                    } else if (vObservatoryId < 1.5) {
                        color = mix(color, vec3(1.0, 0.3, 0.2), 0.1); // Marte: vermelho
                    } else {
                        color = mix(color, vec3(0.3, 1.0, 0.3), 0.1); // Proxima: verde
                    }

                    // Brilho para emaranhamento forte intra/inter observatório
                    float entanglement_glow = smoothstep(2.4, 2.8, vBellS) + vInterObsEntangled * 0.3;
                    color += vec3(0.2, 0.1, 0.3) * entanglement_glow;

                    // Specular para profundidade
                    vec3 lightDir = normalize(vec3(1.0, 2.0, 1.0));
                    vec3 normal = normalize(vPosition);
                    float specular = pow(max(dot(normal, lightDir), 0.0), 32.0) * 0.3;

                    gl_FragColor = vec4(color + specular, 1.0);
                }
            `,
            transparent: false
        });

        // Instanced mesh para performance (átomos de todos os observatórios)
        const totalAtoms = this.config.atomCountPerObs * this.config.observatories.length;
        this.instancedAtoms = new THREE.InstancedMesh(
            new THREE.SphereGeometry(1, 16, 16),
            this.quantumMaterial,
            totalAtoms
        );
        this.instancedAtoms.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

        // Inicializar posições por observatório
        this._initDistributedLattice();

        // WebSockets para cada observatório
        this.wsConnections = {};
        this._connectToObservatories(config.observatoryWsUrls || {
            'EARTH': 'ws://earth.arkhe.local:8081/quantum-stream',
            'MARS_ORBIT': 'ws://mars.arkhe.local:8081/quantum-stream',
            'PROXIMA_RELAY': 'ws://proxima.arkhe.local:8081/quantum-stream'
        });

        // Sincronização de fase distribuída
        this.phaseCorrections = new Float32Array(this.config.observatories.length).fill(0);
        this._startPhaseSynchronization();
    }

    _initDistributedLattice() {
        const { a, b, c } = this.config.latticeParams;
        const scale = 10;
        const dummy = new THREE.Object3D();
        let globalIdx = 0;

        // Para cada observatório, gerar lattice local com offset espacial
        this.config.observatories.forEach((obsId, obsIdx) => {
            const obsOffset = {
                'EARTH': { x: 0, y: 0, z: 0 },
                'MARS_ORBIT': { x: 200, y: 0, z: 0 }, // offset visual para Marte
                'PROXIMA_RELAY': { x: 0, y: 200, z: 100 } // offset para Proxima
            }[obsId] || { x: 0, y: 0, z: 0 };

            for (let layer = 0; layer < 4; layer++) {
                const z = (layer * c / 4) * scale + obsOffset.z;
                for (let i = 0; i < 23 && globalIdx % this.config.atomCountPerObs < this.config.atomCountPerObs; i++) {
                    for (let j = 0; j < 23 && globalIdx % this.config.atomCountPerObs < this.config.atomCountPerObs; j++) {
                        const x = (i + (layer % 2) * 0.5) * a * scale + obsOffset.x;
                        const y = (j + (layer % 2) * 0.5) * b * scale + obsOffset.y;

                        dummy.position.set(x, y, z);
                        dummy.updateMatrix();
                        this.instancedAtoms.setMatrixAt(globalIdx, dummy.matrix);

                        // Armazenar metadados do átomo
                        this.instancedAtoms.setAttribute('uObservatoryId', new Float32Array([obsIdx]), globalIdx);

                        globalIdx++;
                        if (globalIdx >= this.instancedAtoms.count) break;
                    }
                    if (globalIdx >= this.instancedAtoms.count) break;
                }
                if (globalIdx >= this.instancedAtoms.count) break;
            }
        });
        this.instancedAtoms.instanceMatrix.needsUpdate = true;
    }

    _connectToObservatories(urls) {
        Object.entries(urls).forEach(([obsId, url]) => {
            const ws = new WebSocket(url);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'quantum_state_update') {
                    this._updateQuantumBuffers(obsId, data.atoms);
                } else if (data.type === 'entanglement_sync') {
                    this._updatePhaseCorrection(obsId, data.phaseCorrection);
                }
            };
            ws.onclose = () => {
                console.log(`🔌 Reconectando a ${obsId}...`);
                setTimeout(() => this._connectToObservatories({ [obsId]: url }), 3000);
            };
            this.wsConnections[obsId] = ws;
        });
    }

    _updateQuantumBuffers(observatoryId, atoms) {
        const obsIdx = this.config.observatories.indexOf(observatoryId);
        if (obsIdx === -1) return;

        const baseIdx = obsIdx * this.config.atomCountPerObs;
        const phaseBuffer = this.quantumMaterial.uniforms.uPhase.value;
        const ampBuffer = this.quantumMaterial.uniforms.uAmplitude.value;
        const bellBuffer = this.quantumMaterial.uniforms.uBellS.value;

        for (const atom of atoms) {
            const idx = baseIdx + atom.localIdx;
            if (idx < phaseBuffer.length) {
                phaseBuffer[idx] = atom.phase;
                ampBuffer[idx] = atom.amplitude;
                bellBuffer[idx] = atom.bell_S;
            }
        }

        this.quantumMaterial.uniforms.uPhase.needsUpdate = true;
        this.quantumMaterial.uniforms.uAmplitude.needsUpdate = true;
        this.quantumMaterial.uniforms.uBellS.needsUpdate = true;
    }

    _updatePhaseCorrection(observatoryId, correction) {
        const obsIdx = this.config.observatories.indexOf(observatoryId);
        if (obsIdx !== -1) {
            this.phaseCorrections[obsIdx] = correction;
            this.quantumMaterial.uniforms.uPhaseCorrection.value = this.phaseCorrections;
            this.quantumMaterial.uniforms.uPhaseCorrection.needsUpdate = true;
        }
    }

    _startPhaseSynchronization() {
        // Protocolo simplificado de sincronização de fase via emaranhamento
        setInterval(() => {
            // Em produção: trocar mensagens de sincronização via canais quânticos
            // Aqui: simular correção de fase baseada em delay de propagação
            this.config.observatories.forEach((obsId, idx) => {
                if (obsId !== 'EARTH') {
                    // Simular delay de propagação: correção de fase proporcional à distância
                    const delayMs = { 'MARS_ORBIT': 200, 'PROXIMA_RELAY': 4.24 * 365.25 * 24 * 3600 * 1000 }[obsId] || 100;
                    const phaseCorrection = (delayMs / 1000) * 0.01; // rad/s simplificado
                    this._updatePhaseCorrection(obsId, phaseCorrection);
                }
            });
        }, this.config.entanglementSyncInterval);
    }

    // Loop de animação
    start() {
        if (this._animating) return;
        this._animating = true;
        this._animate();
    }

    _animate(time = 0) {
        if (!this._animating) return;
        requestAnimationFrame(this._animate.bind(this));

        this.quantumMaterial.uniforms.uTime.value = time * 0.001;

        this.renderer.render(
            new THREE.Scene().add(this.instancedAtoms),
            this.camera || new THREE.PerspectiveCamera(60,
                this.container.clientWidth / this.container.clientHeight, 0.1, 20000)
        );
    }

    stop() { this._animating = false; }

    // Utilitários
    exportDistributedState(filename = 'distributed_quantum_state.json') {
        const state = {
            timestamp: Date.now(),
            observatories: this.config.observatories,
            phaseCorrections: Array.from(this.phaseCorrections),
            atoms: Array.from({ length: this.instancedAtoms.count }, (_, i) => ({
                observatory: this.config.observatories[Math.floor(i / this.config.atomCountPerObs)],
                localIdx: i % this.config.atomCountPerObs,
                phase: this.quantumMaterial.uniforms.uPhase.value[i],
                amplitude: this.quantumMaterial.uniforms.uAmplitude.value[i],
                bell_S: this.quantumMaterial.uniforms.uBellS.value[i]
            }))
        };
        const blob = new Blob([JSON.stringify(state)], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DistributedQuantumCrystalEngine };
}
