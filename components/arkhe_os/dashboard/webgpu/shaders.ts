export const forceLayoutWGSL = `
struct Node {
  position: vec3f,
  coherence: vec4f,      // [Φ_C, criticality, confidence, reserved]
  attributes: vec4f,     // [size, opacity, glow, type]
  velocity: vec3f,
  force: vec3f,
};

struct Edge {
  source: u32,
  target: u32,
  coherence_weight: f32,
};

struct Uniforms {
  time: f32,
  force_repel: f32,
  force_attract: f32,
  coherence_field: f32,
  viewport_width: f32,
  viewport_height: f32,
  camera_pos: vec3f,
  camera_target: vec3f,
};

@group(0) @binding(0) var<storage, read_write> nodes: array<Node>;
@group(0) @binding(1) var<storage, read> edges: array<Edge>;
@group(0) @binding(2) var<uniform> uniforms: Uniforms;

@compute @workgroup_size(64)
fn main(@global_id gid: vec3u) {
  let node_idx = gid.x;
  if (node_idx >= arrayLength(&nodes)) {
    return;
  }

  var node = nodes[node_idx];
  var total_force = vec3f(0.0);

  // Força de repulsão de todos os outros nós
  for (var i: u32 = 0; i < arrayLength(&nodes); i++) {
    if (i == node_idx) { continue; }
    let other = nodes[i];
    let diff = node.position - other.position;
    let dist = length(diff) + 0.001; // evitar divisão por zero
    let repel_force = uniforms.force_repel / (dist * dist);
    total_force += normalize(diff) * repel_force;
  }

  // Força de atração baseada em arestas e coerência
  for (var e: u32 = 0; e < arrayLength(&edges); e++) {
    let edge = edges[e];
    let connected_idx = 0u;
    if (edge.source == node_idx) { connected_idx = edge.target; }
    else if (edge.target == node_idx) { connected_idx = edge.source; }
    else { continue; }

    let other = nodes[connected_idx];
    let diff = other.position - node.position;
    let dist = length(diff) + 0.001;

    // Atração ponderada pela coerência da aresta
    let attract_force = uniforms.force_attract * edge.coherence_weight * dist;
    total_force += normalize(diff) * attract_force;
  }

  // Campo de coerência: nós de alta coerência são "puxados" para o centro
  let coherence = node.coherence.x;
  let center_force = uniforms.coherence_field * (1.0 - coherence);
  let to_center = -normalize(node.position);
  total_force += to_center * center_force;

  // Atualizar velocidade e posição com amortecimento
  let damping = 0.95;
  node.velocity = node.velocity * damping + total_force * 0.016; // 60 FPS
  node.position += node.velocity;

  // Confinar ao viewport
  let boundary = vec2f(uniforms.viewport_width * 0.45, uniforms.viewport_height * 0.45);
  node.position.x = clamp(node.position.x, -boundary.x, boundary.x);
  node.position.y = clamp(node.position.y, -boundary.y, boundary.y);
  node.position.z = clamp(node.position.z, -100.0, 100.0);

  nodes[node_idx] = node;
}
`;

export const renderWGSL = `
struct Uniforms {
  time: f32,
  force_repel: f32,
  force_attract: f32,
  coherence_field: f32,
  viewport_width: f32,
  viewport_height: f32,
  camera_pos: vec3f,
  camera_target: vec3f,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;

struct VertexOutput {
  @builtin(position) position: vec4f,
  @location(0) color: vec4f,
};

fn cielab_to_xyz(lab: vec3f) -> vec3f {
  // Convert CIELAB to XYZ (D65 illuminant)
  let fy = (lab.x + 16.0) / 116.0;
  let fx = fy + lab.y / 500.0;
  let fz = fy - lab.z / 200.0;

  let fx3 = fx * fx * fx;
  let fz3 = fz * fz * fz;
  let xyz = vec3f(
    select((fx - 16.0/116.0) / 7.787, fx3, fx3 > 0.008856),
    select(lab.x / 903.3, pow((lab.x + 16.0) / 116.0, 3.0), lab.x > 0.008856),
    select((fz - 16.0/116.0) / 7.787, fz3, fz3 > 0.008856)
  );

  // XYZ to linear RGB (sRGB matrix)
  return vec3f(
     3.2406 * xyz.x - 1.5372 * xyz.y - 0.4986 * xyz.z,
    -0.9689 * xyz.x + 1.8758 * xyz.y + 0.0415 * xyz.z,
     0.0557 * xyz.x - 0.2040 * xyz.y + 1.0570 * xyz.z
  );
}

fn linear_to_srgb(linear: vec3f) -> vec3f {
  // Gamma correction for sRGB
  return select(
    linear * 12.92,
    pow(linear, vec3f(1.0/2.4)) * 1.055 - 0.055,
    linear > vec3f(0.0031308)
  );
}

fn coherence_to_color(coherence: f32, criticality: f32, confidence: f32) -> vec4f {
  // Mapear Φ_C para CIELAB
  let L = 100.0 * pow(coherence, 0.4);
  let a = 127.0 * (2.0 * coherence - 1.0);
  let b = 127.0 * sin(6.283185 * coherence);

  // Ajustar por criticidade (mais vermelho para alta criticidade)
  let a_adj = a + criticality * 50.0;

  // Ajustar por confiança (mais saturado para alta confiança)
  let saturation = 0.5 + confidence * 0.5;

  var lab = vec3f(L, a_adj * saturation, b * saturation);

  // Converter para sRGB
  let xyz = cielab_to_xyz(lab);
  let linear_rgb = linear_to_srgb(xyz);

  // Clamp e alpha baseado em glow
  let rgb = clamp(linear_rgb, vec3f(0.0), vec3f(1.0));
  return vec4f(rgb, 1.0);
}

@vertex
fn vertexMain(
  @location(0) position: vec3f,
  @location(1) coherence: vec4f,
  @location(2) attributes: vec4f
) -> VertexOutput {
  var output: VertexOutput;
  // Apply camera projection here in a real implementation
  // For now just scale down the coordinates to fit NDC
  let screenPos = position * 0.001;
  output.position = vec4f(screenPos.x, screenPos.y, 0.5, 1.0);
  output.color = coherence_to_color(coherence.x, coherence.y, coherence.z);
  return output;
}

@fragment
fn fragmentMain(input: VertexOutput) -> @location(0) vec4f {
  return input.color;
}
`;
