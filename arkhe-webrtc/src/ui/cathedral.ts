// ============================================================================
// ARKHE Ω-TEMP — Cathedral UI (Three.js Visualization)
// ============================================================================
// Visualização 3D do mesh em tempo real usando Three.js.
// Cada nó é representado como uma esfera luminosa, com conexões
// representando os DataChannels WebRTC ativos.
// ============================================================================

import * as THREE from 'three';
import { ArkheMesh } from '../p2p/mesh';
import { MeshMetrics } from '../core/types';
import { shortAddress } from '../core/address';
import { ArkhePeer } from '../p2p/peer';

export interface CathedralConfig {
  container: HTMLElement;
  mesh: ArkheMesh;
  showConnections: boolean;
  showConsensus: boolean;
  showLatency: boolean;
  colorScheme: 'dark' | 'light' | 'solar';
  autoRotate: boolean;
}

export class CathedralVisualizer {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private mesh: ArkheMesh;

  private nodeObjects: Map<string, THREE.Mesh> = new Map();
  private connectionLines: THREE.Group = new THREE.Group();
  private animationFrame: number | null = null;
  private raycaster: THREE.Raycaster = new THREE.Raycaster();
  private mouse: THREE.Vector2 = new THREE.Vector2();

  // Visual state
  private time: number = 0;
  private hoveredNode: string | null = null;

  constructor(config: CathedralConfig) {
    this.mesh = config.mesh;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000); // Dummy aspect ratio for now
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

    this.initScene(config.container);
    this.setupLighting();
    this.setupInteraction(config.container);
    this.animate();
  }

  private initScene(container: HTMLElement): void {
    // Renderer
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    container.appendChild(this.renderer.domElement);

    // Scene
    this.scene.fog = new THREE.FogExp2(0x000011, 0.015);

    // Camera
    this.camera.aspect = container.clientWidth / container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.camera.position.set(0, 15, 30);
    this.camera.lookAt(0, 0, 0);

    // Add connection lines group
    this.scene.add(this.connectionLines);
  }

  private setupLighting(): void {
    // Ambient light
    this.scene.add(new THREE.AmbientLight(0x111133, 0.5));

    // Main directional light (simulating sun)
    const sunLight = new THREE.DirectionalLight(0x4488FF, 1.5);
    sunLight.position.set(10, 20, 10);
    this.scene.add(sunLight);

    // Point lights at known positions
    const pointLight1 = new THREE.PointLight(0xFF4444, 2, 50);
    pointLight1.position.set(10, 5, 0);
    this.scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x44FF44, 2, 50);
    pointLight2.position.set(-10, -5, 0);
    this.scene.add(pointLight2);

    const pointLight3 = new THREE.PointLight(0x4444FF, 2, 50);
    pointLight3.position.set(0, 5, 15);
    this.scene.add(pointLight3);
  }

  private setupInteraction(container: HTMLElement): void {
    const canvas = this.renderer.domElement;

    // Mouse events
    canvas.addEventListener('mousemove', (event) => {
      this.mouse.x = (event.clientX / canvas.clientWidth) * 2 - 1;
      this.mouse.y = -(event.clientY / canvas.clientHeight) * 2 + 1;

      // Raycasting for node selection
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const intersects = this.raycaster.intersectObjects(
        Array.from(this.nodeObjects.values())
      );

      if (intersects.length > 0) {
        const node = intersects[0].object as THREE.Mesh;
        // Highlight hovered node
        const originalMat = node.userData.originalColor as THREE.Material;
        const highlightMat = node.userData.highlightColor as THREE.Material;

        if (!node.userData.isHovered && highlightMat) {
          node.material = highlightMat;
          node.userData.isHovered = true;
          this.hoveredNode = node.userData.address;
          this.showNodeInfo(node.userData.address);
        }
      } else if (this.hoveredNode) {
        // Restore previous node
        const prevNode = this.nodeObjects.get(this.hoveredNode);
        if (prevNode) {
          prevNode.material = prevNode.userData.originalColor;
          prevNode.userData.isHovered = false;
        }
        this.hoveredNode = null;
        this.hideNodeInfo();
      }
    });

    // Scroll zoom
    canvas.addEventListener('wheel', (event) => {
      event.preventDefault();
      const zoomFactor = event.deltaY > 0 ? 1.1 : 0.9;
      this.camera.position.multiplyScalar(zoomFactor);
      this.camera.position.clampLength(5, 200);
    });

    // Touch support
    let lastTouchDistance = 0;
    canvas.addEventListener('touchmove', (event) => {
      if (event.touches.length === 2) {
        const distance = Math.hypot(
          event.touches[0].clientX - event.touches[1].clientX,
          event.touches[0].clientY - event.touches[1].clientY
        );
        if (lastTouchDistance > 0) {
          const scale = lastTouchDistance / distance;
          this.camera.position.multiplyScalar(scale);
          this.camera.position.clampLength(5, 200);
        }
        lastTouchDistance = distance;
      }
    });

    canvas.addEventListener('touchend', () => {
      lastTouchDistance = 0;
    });

    // Resize
    window.addEventListener('resize', () => {
      this.renderer.setSize(container.clientWidth, container.clientHeight);
      this.camera.aspect = container.clientWidth / container.clientHeight;
      this.camera.updateProjectionMatrix();
    });
  }

  // Update visualization with current mesh state
  update(): void {
    const peers = this.mesh.getActivePeers();

    // Add/update nodes
    for (const peer of peers) {
      if (!this.nodeObjects.has(peer.address)) {
        this.addNodeVisual(peer);
      } else {
        this.updateNodeVisual(peer);
      }
    }

    // Remove disconnected nodes
    for (const [address] of this.nodeObjects) {
      if (!peers.find(p => p.address === address)) {
        this.removeNodeVisual(address);
      }
    }

    // Update connections
    this.updateConnections(peers);
  }

  private addNodeVisual(peer: ArkhePeer): void {
    // Position based on address hash (deterministic)
    const position = this.addressToPosition(peer.address);

    // Create sphere geometry
    const geometry = new THREE.SphereGeometry(0.8, 16, 16);

    // Color based on status/consensus
    const color = new THREE.Color();
    color.setHSL(
      (peer.info.consistencyScore ?? 0.5) * 0.3, // Hue: 0 (red) to 0.3 (green)
      0.8,
      0.5 + (peer.getLatency() ?? 0) / 500
    );

    const material = new THREE.MeshPhongMaterial({
      color,
      emissive: color.clone().multiplyScalar(0.3),
      shininess: 80,
      transparent: true,
      opacity: 0.9,
    });

    const highlightMaterial = material.clone();
    highlightMaterial.emissive.setHex(0xFFFF00);
    highlightMaterial.opacity = 1.0;

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(position);
    mesh.userData = {
      address: peer.address,
      originalColor: material,
      highlightColor: highlightMaterial,
      isHovered: false,
      metrics: { latency: peer.getLatency() },
    };

    // Add glow effect (halo)
    const haloGeometry = new THREE.SphereGeometry(1.0, 8, 8);
    const haloMaterial = new THREE.MeshBasicMaterial({
      color: color.clone().multiplyScalar(0.5),
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide,
    });
    const halo = new THREE.Mesh(haloGeometry, haloMaterial);
    mesh.add(halo);

    this.scene.add(mesh);
    this.nodeObjects.set(peer.address, mesh);
  }

  private updateNodeVisual(peer: ArkhePeer): void {
    const mesh = this.nodeObjects.get(peer.address);
    if (!mesh) return;

    mesh.userData.metrics = { latency: peer.getLatency() };
  }

  private removeNodeVisual(address: string): void {
    const mesh = this.nodeObjects.get(address);
    if (mesh) {
      this.scene.remove(mesh);
      if (mesh.geometry) mesh.geometry.dispose();
      if (mesh.material) (mesh.material as THREE.Material).dispose();
      this.nodeObjects.delete(address);
    }
  }

  private updateConnections(peers: ArkhePeer[]): void {
    // Clear existing lines
    while (this.connectionLines.children.length > 0) {
      const child = this.connectionLines.children[0] as THREE.Line;
      if (child.geometry) child.geometry.dispose();
      if (child.material) (child.material as THREE.Material).dispose();
      this.connectionLines.remove(child);
    }

    // Draw new connections
    for (let i = 0; i < peers.length; i++) {
      for (let j = i + 1; j < peers.length; j++) {
        const pos1 = this.addressToPosition(peers[i].address);
        const pos2 = this.addressToPosition(peers[j].address);
        const distance = pos1.distanceTo(pos2);

        // Only draw lines for close peers (within visual range)
        if (distance < 30) {
          const geometry = new THREE.BufferGeometry().setFromPoints([pos1, pos2]);
          const material = new THREE.LineBasicMaterial({
            color: 0x4466aa,
            transparent: true,
            opacity: 0.3 + (1 - distance / 30) * 0.5,
          });
          const line = new THREE.Line(geometry, material);
          this.connectionLines.add(line);
        }
      }
    }
  }

  private addressToPosition(address: string): THREE.Vector3 {
    // Deterministic position from address hash
    let hash = 0;
    for (let i = 0; i < address.length; i++) {
      hash = ((hash << 5) - hash) + address.charCodeAt(i);
      hash |= 0;
    }

    const angle = (hash & 0xFF) / 255 * Math.PI * 2;
    const radius = 10 + ((hash >> 8) & 0xF);
    const elevation = ((hash >> 12) & 0xF) - 5;

    return new THREE.Vector3(
      Math.cos(angle) * radius,
      elevation,
      Math.sin(angle) * radius
    );
  }

  private showNodeInfo(address: string): void {
    // Display info panel for the node
    const infoPanel = document.getElementById('node-info');
    if (infoPanel) {
      // Fetch and display node details
      infoPanel.innerHTML = `<div class="info-content">
        <h4>${shortAddress(address)}</h4>
        <p>Address: ${address}</p>
        <p>Status: Active</p>
        <p>Latency: Calculating...</p>
      </div>`;
      infoPanel.style.display = 'block';
    }
  }

  private hideNodeInfo(): void {
    const infoPanel = document.getElementById('node-info');
    if (infoPanel) {
      infoPanel.style.display = 'none';
    }
  }

  private animate(): void {
    this.animationFrame = requestAnimationFrame(() => this.animate());

    this.time += 0.01;

    // Animate nodes (gentle floating)
    this.nodeObjects.forEach((mesh) => {
      mesh.position.y += Math.sin(this.time * 2 + mesh.position.x) * 0.005;
    });

    this.renderer.render(this.scene, this.camera);
  }
}
