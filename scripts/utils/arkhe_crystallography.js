// arkhe_living_crystal.js — Substrato 170: Cristalografia Viva
// Conecta o motor BiCuSeO ao Orchestrator ARKHE via WebSocket

class LivingCrystalEngine {
  constructor(containerId, orchestratorWsUrl) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 5000);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    this.atomMeshes = {};
    this.gapBuffers = new Map(); // atomIndex → currentGap

    // Conectar ao Orchestrator
    this.connectToOrchestrator(orchestratorWsUrl);
  }

  connectToOrchestrator(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'coherence_burst') {
        this.animateCoherenceBurst(data.atoms, data.gaps);
      } else if (data.type === 'zonal_update') {
        this.updateZonalCoherence(data.zones);
      }
    };
    this.ws.onclose = () => setTimeout(() => this.connectToOrchestrator(wsUrl), 3000);
  }

  animateCoherenceBurst(atoms, gaps) {
    const duration = 2000; // ms
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const t = Math.min(elapsed / duration, 1.0);

      // Interpolação suave entre gap atual e novo gap
      for (let i = 0; i < atoms.length; i++) {
        const atomIdx = atoms[i];
        const targetGap = gaps[i];
        const currentGap = this.gapBuffers.get(atomIdx) || 0;
        const interpolatedGap = currentGap + (targetGap - currentGap) * t;

        this.gapBuffers.set(atomIdx, interpolatedGap);
        this.setAtomColor(atomIdx, this.gapToColor(interpolatedGap));
      }

      if (t < 1.0) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }

  updateZonalCoherence(zones) {
    // Mapear zonas para átomos baseado em coordenadas espaciais
    for (const [zoneId, zoneData] of Object.entries(zones)) {
      const gap = zoneData.coherence_gap;
      const affectedAtoms = this.findAtomsInZone(zoneId);
      affectedAtoms.forEach(atomIdx => {
        this.gapBuffers.set(atomIdx, gap);
        this.setAtomColor(atomIdx, this.gapToColor(gap));
      });
    }
  }

  setAtomColor(atomIdx, color) {
    // Atualizar cor no buffer da GPU via instanced attribute
    if (this.atomMeshes[atomIdx]) {
      this.atomMeshes[atomIdx].material.uniforms.uColor.value.set(color);
    }
  }

  gapToColor(gap) {
    // Mapa de calor da coerência: azul (0) → verde (25) → vermelho (50)
    const t = Math.min(gap / 50.0, 1.0);
    return new THREE.Color(t, 0.5 * (1 - Math.abs(t - 0.5) * 2), 1 - t);
  }

  findAtomsInZone(zoneId) {
    // Mapeia zonas ARKHE para regiões espaciais da estrutura cristalina
    // Bi₂O₂ sheets → zona 'Interior', Cu₂Se₂ layers → zona 'Marte', etc.
    const zoneMap = {
      'Interior': [0, 1, 2, 3],     // Bi e O atoms
      'Marte': [4, 5, 6, 7],        // Cu e Se atoms
      'Belt': [0, 1, 4, 5],         // Mixed layer
    };
    return zoneMap[zoneId] || [];
  }
}

// substrates/v169_crystallography/arkhe_crystallography.js
// Motor de cristalografia que conecta ao Orchestrator ARKHE via WebSocket
// Renderiza 192.000 átomos com gaps de coerência em tempo real

class ArkheCrystallographyEngine {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        this.config = {
            atomCount: 192000,
            latticeParams: { a: 3.89, b: 3.89, c: 12.24 }, // BiCuSeO em Å
            coherenceRange: [0, 50], // gap de coerência em unidades arbitrárias
            updateRate: 30, // FPS para animação
            ...config
        };

        // Three.js setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a1a);
        this.camera = new THREE.PerspectiveCamera(60,
            this.container ? this.container.clientWidth / this.container.clientHeight : 1,
            0.1, 10000);
        this.camera.position.set(200, 150, 200);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
        if (this.container) {
          this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
          this.container.appendChild(this.renderer.domElement);
        }

        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

        // Controls
        if (window.THREE && THREE.OrbitControls) {
          this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
          this.controls.enableDamping = true;
          this.controls.dampingFactor = 0.05;
        }

        // Atom storage
        this.atomMeshes = new Map(); // atomId -> { mesh, material, coherenceGap }
        this.bondLines = null;

        // WebSocket connection to Orchestrator
        this.ws = null;
        this.wsUrl = config.wsUrl || 'ws://localhost:8080/crystal-stream';

        // Animation state
        this.lastUpdate = 0;
        this.running = false;

        // Initialize
        this._initLights();
        this._initAtoms();
        this._initBonds();
        this._setupResizeHandler();
    }

    _initLights() {
        // Ambient + directional for PBR-like shading
        const ambient = new THREE.AmbientLight(0x404060, 0.3);
        this.scene.add(ambient);

        const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
        keyLight.position.set(100, 200, 100);
        this.scene.add(keyLight);

        const fillLight = new THREE.DirectionalLight(0x8080ff, 0.3);
        fillLight.position.set(-100, -100, -100);
        this.scene.add(fillLight);
    }

    _initAtoms() {
        // Generate BiCuSeO crystal lattice
        // Bi₂O₂ layers at z=0, c/2; Cu₂Se₂ layers at z=c/4, 3c/4
        const { a, b, c } = this.config.latticeParams;
        const scale = 10; // Visual scaling

        const atomTypes = {
            'Bi': { color: 0x9b59b6, radius: 0.8, sublattice: 'Bi2O2' },
            'Cu': { color: 0xe67e22, radius: 0.6, sublattice: 'Cu2Se2' },
            'Se': { color: 0x2ecc71, radius: 0.7, sublattice: 'Cu2Se2' },
            'O':  { color: 0xecf0f1, radius: 0.5, sublattice: 'Bi2O2' }
        };

        // Geometry for instanced rendering (performance for 192k atoms)
        const sphereGeo = new THREE.SphereGeometry(1, 16, 16);
        const material = new THREE.ShaderMaterial({
            uniforms: {
                uColor: { value: new THREE.Color(0x3498db) },
                uCoherenceGap: { value: 0.0 },
                uCoherenceMin: { value: this.config.coherenceRange[0] },
                uCoherenceMax: { value: this.config.coherenceRange[1] }
            },
            vertexShader: `
                varying vec3 vNormal;
                varying vec3 vPosition;
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    vPosition = (modelMatrix * vec4(position, 1.0)).xyz;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 uColor;
                uniform float uCoherenceGap;
                uniform float uCoherenceMin;
                uniform float uCoherenceMax;
                varying vec3 vNormal;
                varying vec3 vPosition;

                vec3 gapToColor(float gap) {
                    // Blue (coherent) -> Green -> Red (alucination)
                    float t = clamp((gap - uCoherenceMin) / (uCoherenceMax - uCoherenceMin), 0.0, 1.0);
                    if (t < 0.5) {
                        return mix(vec3(0.0, 0.3, 1.0), vec3(0.0, 1.0, 0.3), t * 2.0);
                    } else {
                        return mix(vec3(0.0, 1.0, 0.3), vec3(1.0, 0.1, 0.1), (t - 0.5) * 2.0);
                    }
                }

                void main() {
                    vec3 color = gapToColor(uCoherenceGap);
                    // Simple PBR-like specular
                    vec3 lightDir = normalize(vec3(100.0, 200.0, 100.0));
                    float specular = pow(max(dot(vNormal, lightDir), 0.0), 32.0) * 0.3;
                    gl_FragColor = vec4(color + specular, 1.0);
                }
            `,
            transparent: false
        });

        // Instanced mesh for performance
        this.instancedAtoms = new THREE.InstancedMesh(sphereGeo, material, this.config.atomCount);
        this.instancedAtoms.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
        this.scene.add(this.instancedAtoms);

        // Generate lattice positions
        let atomIdx = 0;
        const positions = [];

        // Bi₂O₂ layer at z=0
        for (let i = 0; i < 40; i++) {
            for (let j = 0; j < 40; j++) {
                if (atomIdx >= this.config.atomCount) break;

                // Bi positions
                const x = (i + 0.25) * a * scale;
                const y = (j + 0.25) * b * scale;
                const z = 0;
                positions.push({ type: 'Bi', x, y, z, idx: atomIdx++ });

                // O positions (offset)
                if (atomIdx < this.config.atomCount) {
                    positions.push({
                        type: 'O',
                        x: (i + 0.75) * a * scale,
                        y: (j + 0.75) * b * scale,
                        z: 0,
                        idx: atomIdx++
                    });
                }
            }
        }

        // Cu₂Se₂ layer at z=c/4
        for (let i = 0; i < 40 && atomIdx < this.config.atomCount; i++) {
            for (let j = 0; j < 40 && atomIdx < this.config.atomCount; j++) {
                const x = (i + 0.5) * a * scale;
                const y = (j + 0.5) * b * scale;
                const z = (c / 4) * scale;

                positions.push({ type: 'Cu', x, y, z, idx: atomIdx++ });
                if (atomIdx < this.config.atomCount) {
                    positions.push({ type: 'Se', x: x + a*scale*0.3, y: y + b*scale*0.3, z, idx: atomIdx++ });
                }
            }
        }

        // Set initial positions and colors
        const dummy = new THREE.Object3D();
        positions.forEach((pos, i) => {
            dummy.position.set(pos.x, pos.y, pos.z);
            dummy.updateMatrix();
            this.instancedAtoms.setMatrixAt(i, dummy.matrix);

            // Store atom metadata
            this.atomMeshes.set(pos.idx, {
                type: pos.type,
                position: new THREE.Vector3(pos.x, pos.y, pos.z),
                coherenceGap: 0,
                sublattice: atomTypes[pos.type].sublattice
            });
        });
        this.instancedAtoms.instanceMatrix.needsUpdate = true;

        // Sublattice filter UI
        this.sublatticeFilter = 'all'; // 'all', 'Bi2O2', 'Cu2Se2'
    }

    _initBonds() {
        // Optional: render bonds between neighboring atoms
        // Simplified: only show bonds within cutoff distance
        const bonds = [];
        const cutoff = 50; // Visual cutoff in scaled units

        const positions = Array.from(this.atomMeshes.values()).map(a => a.position);

        for (let i = 0; i < positions.length && i < 10000; i++) { // Limit for performance
            for (let j = i + 1; j < positions.length && j < i + 100; j++) {
                const d = positions[i].distanceTo(positions[j]);
                if (d < cutoff) {
                    bonds.push(positions[i], positions[j]);
                }
            }
        }

        if (bonds.length > 0) {
            const bondGeo = new THREE.BufferGeometry().setFromPoints(bonds);
            const bondMat = new THREE.LineBasicMaterial({ color: 0x444466, transparent: true, opacity: 0.2 });
            this.bondLines = new THREE.LineSegments(bondGeo, bondMat);
            this.scene.add(this.bondLines);
        }
    }

    _setupResizeHandler() {
        window.addEventListener('resize', () => {
            if (this.container) {
                this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
                this.camera.updateProjectionMatrix();
                this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            }
        });
    }

    // Connect to Orchestrator WebSocket for real-time coherence updates
    connectToOrchestrator(url = this.wsUrl) {
        if (this.ws?.readyState === WebSocket.OPEN) return;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('🔗 Crystallography engine connected to Orchestrator');
            // Request initial state
            this.ws.send(JSON.stringify({ type: 'subscribe', channel: 'coherence_updates' }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'coherence_update') {
                this.updateCoherenceVisualization(data.zones);
            } else if (data.type === 'lattice_reconfigure') {
                this._reconfigureLattice(data.newParams);
            }
        };

        this.ws.onclose = () => {
            console.log('🔌 Orchestrator connection closed, reconnecting in 5s...');
            setTimeout(() => this.connectToOrchestrator(url), 5000);
        };
    }

    // Update atom colors based on coherence gaps from Orchestrator
    updateCoherenceVisualization(zones) {
        // zones: { zoneId: { atomIndices: [idx], coherenceGap: float, timestamp: float } }
        const dummy = new THREE.Object3D();

        for (const [zoneId, zoneData] of Object.entries(zones)) {
            const gap = zoneData.coherenceGap;
            const atomIndices = zoneData.atomIndices || [];

            atomIndices.forEach(atomIdx => {
                const atom = this.atomMeshes.get(atomIdx);
                if (!atom) return;

                // Update coherence gap with smoothing
                atom.coherenceGap = THREE.MathUtils.lerp(atom.coherenceGap, gap, 0.1);

                // Update shader uniform via instance matrix trick
                // (In production: use custom shader with instance attributes)
                dummy.position.copy(atom.position);
                dummy.updateMatrix();
                this.instancedAtoms.setMatrixAt(atomIdx, dummy.matrix);

                // Store gap for color interpolation in shader
                // Note: For 192k atoms, use texture lookup or instanced attributes in production
            });
        }

        this.instancedAtoms.instanceMatrix.needsUpdate = true;
    }

    // Filter visualization by sublattice (projection to nucleus analog)
    setSublatticeFilter(sublattice) {
        this.sublatticeFilter = sublattice;
        const dummy = new THREE.Object3D();

        this.atomMeshes.forEach((atom, idx) => {
            const visible = sublattice === 'all' || atom.sublattice === sublattice;

            // Hide/show via scale trick (production: use frustum culling or layers)
            dummy.position.copy(atom.position);
            dummy.scale.setScalar(visible ? 1.0 : 0.001);
            dummy.updateMatrix();
            this.instancedAtoms.setMatrixAt(idx, dummy.matrix);
        });

        this.instancedAtoms.instanceMatrix.needsUpdate = true;
    }

    // Animation loop
    start() {
        if (this.running) return;
        this.running = true;
        this._animate();
    }

    stop() {
        this.running = false;
    }

    _animate(time = 0) {
        if (!this.running) return;

        requestAnimationFrame(this._animate.bind(this));

        // Throttle coherence updates to config.updateRate FPS
        if (time - this.lastUpdate > 1000 / this.config.updateRate) {
            this.lastUpdate = time;
            // Could trigger periodic coherence query here
        }

        // Auto-rotate if no user interaction
        if (this.controls && !this.controls.isDragging) {
            this.scene.rotation.y += 0.001;
        }

        if (this.controls) this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    // Utility: export current view as image
    exportScreenshot(filename = 'arkhe-crystal.png') {
        this.renderer.render(this.scene, this.camera);
        const link = document.createElement('a');
        link.download = filename;
        link.href = this.renderer.domElement.toDataURL('image/png');
        link.click();
    }

    // Cleanup
    dispose() {
        this.stop();
        this.ws?.close();
        this.renderer.dispose();
        this.instancedAtoms?.geometry?.dispose();
        this.instancedAtoms?.material?.dispose();
        this.bondLines?.geometry?.dispose();
        this.bondLines?.material?.dispose();
        if (this.container) this.container.removeChild(this.renderer.domElement);
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ArkheCrystallographyEngine, LivingCrystalEngine };
}
