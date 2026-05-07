class WebGPUDashboard {
    public canvas: HTMLCanvasElement;

    constructor(canvasId: string) {
        this.canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    }

    public renderCoherence() {
        console.log("Rendering coherence locally on WebGPU");
    }
}

export { WebGPUDashboard };
