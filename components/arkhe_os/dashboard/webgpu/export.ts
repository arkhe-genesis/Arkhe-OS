// arkhe_os/dashboard/webgpu/export.ts
export class VisualizationExporter {
  public async exportPNG(canvas: HTMLCanvasElement): Promise<string> {
    return canvas.toDataURL('image/png');
  }

  public exportJSON(state: any): string {
    return JSON.stringify(state, null, 2);
  }
}
