// arkhe_os/dashboard/webgpu/interactive_viewport.ts
import { CoherenceGraphRenderer } from './coherence_graph_renderer';
import { clamp, vec2, Vec2, distancePointToRay } from './math_utils';
import { Camera3D } from './camera';

export interface ViewportState {
  camera: Camera3D;
  selection: Set<string>;
  hoverNode: string | null;
  zoomLevel: number;
  panOffset: Vec2;
}

export class InteractiveViewport {
  private canvas: HTMLCanvasElement;
  private renderer: CoherenceGraphRenderer;
  private state: ViewportState;

  // Event handlers
  private onNodeSelect: (nodeId: string) => void;
  private onCoherenceDrillDown: (nodeId: string, domain: string) => void;

  constructor(
    canvas: HTMLCanvasElement,
    renderer: CoherenceGraphRenderer,
    callbacks: {
      onSelect: (id: string) => void;
      onDrillDown: (id: string, domain: string) => void;
    }
  ) {
    this.canvas = canvas;
    this.renderer = renderer;
    this.state = {
      camera: new Camera3D(),
      selection: new Set(),
      hoverNode: null,
      zoomLevel: 1.0,
      panOffset: vec2(0, 0),
    };

    this.onNodeSelect = callbacks.onSelect;
    this.onCoherenceDrillDown = callbacks.onDrillDown;

    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Zoom com wheel
    this.canvas.addEventListener('wheel', (e: WheelEvent) => {
      e.preventDefault();
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      this.state.zoomLevel = clamp(this.state.zoomLevel * zoomFactor, 0.1, 10.0);
      this.state.camera.zoom = this.state.zoomLevel;
    });

    // Pan com drag
    let isDragging = false;
    let lastPos: Vec2;

    this.canvas.addEventListener('mousedown', (e: MouseEvent) => {
      if (e.button === 1 || e.button === 2) { // middle or right click
        isDragging = true;
        lastPos = vec2(e.clientX, e.clientY);
      }
    });

    this.canvas.addEventListener('mousemove', (e: MouseEvent) => {
      if (isDragging) {
        const dx = e.clientX - lastPos.x;
        const dy = e.clientY - lastPos.y;
        this.state.panOffset = vec2(
          this.state.panOffset.x + dx * 0.01,
          this.state.panOffset.y + dy * 0.01
        );
        lastPos = vec2(e.clientX, e.clientY);
      }

      // Hover detection via raycasting simplificado
      const hoverNode = this.raycastNode(e.clientX, e.clientY);
      if (hoverNode !== this.state.hoverNode) {
        this.state.hoverNode = hoverNode;
        this.updateHoverTooltip(hoverNode);
      }
    });

    this.canvas.addEventListener('mouseup', () => { isDragging = false; });

    // Clique para seleção
    this.canvas.addEventListener('click', (e: MouseEvent) => {
      const nodeId = this.raycastNode(e.clientX, e.clientY);
      if (nodeId) {
        if (e.ctrlKey || e.metaKey) {
          // Toggle selection
          if (this.state.selection.has(nodeId)) {
            this.state.selection.delete(nodeId);
          } else {
            this.state.selection.add(nodeId);
          }
        } else {
          // Single select
          this.state.selection.clear();
          this.state.selection.add(nodeId);
          this.onNodeSelect(nodeId);
        }
      }
    });

    // Double-click para drill-down
    this.canvas.addEventListener('dblclick', (e: MouseEvent) => {
      const nodeId = this.raycastNode(e.clientX, e.clientY);
      if (nodeId) {
        const node = this.getNodeData(nodeId);
        this.onCoherenceDrillDown(nodeId, node.domain);
      }
    });
  }

  private raycastNode(screenX: number, screenY: number): string | null {
    // Raycasting simplificado: projetar posição da tela para espaço 3D
    // e encontrar nó mais próximo dentro de um raio de tolerância
    const ray = this.state.camera.screenToWorldRay(screenX, screenY, this.canvas);

    let closestNode: string | null = null;
    let closestDist = Infinity;

    // Iterar sobre nós visíveis (otimizar com spatial partitioning em produção)
    for (const node of this.renderer.getVisibleNodes()) {
      const worldPos = this.renderer.getNodeWorldPosition(node.id);
      const dist = distancePointToRay(worldPos, ray);

      if (dist < 2.0 && dist < closestDist) { // 2.0 unidades de tolerância
        closestDist = dist;
        closestNode = node.id;
      }
    }

    return closestNode;
  }

  private getNodeData(nodeId: string): any {
      return {domain: 'unknown', name: 'Unknown', coherence: 0, dependencies: []};
  }

  private updateHoverTooltip(nodeId: string | null): void {
    // Atualizar tooltip HTML com dados do nó
    const tooltip = document.getElementById('coherence-tooltip');
    if (!tooltip) return;

    if (nodeId) {
      const node = this.getNodeData(nodeId);
      tooltip.innerHTML = `
        <strong>${node.name}</strong><br/>
        Φ_C: ${node.coherence.toFixed(3)}<br/>
        Domínio: ${node.domain}<br/>
        Dependências: ${node.dependencies.length}
      `;
      tooltip.style.display = 'block';
    } else {
      tooltip.style.display = 'none';
    }
  }

  public update(deltaTime: number): void {
    // Atualizar câmera com easing para suavidade
    this.state.camera.update(deltaTime);

    // Passar estado de viewport para renderer
    this.renderer.setViewportState({
      camera: this.state.camera,
      selection: this.state.selection,
      hoverNode: this.state.hoverNode,
    });
  }
}
