// arkhe_os/dashboard/webgpu/force_layout.wgsl
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
    let connected_idx = if edge.source == node_idx { edge.target }
                       else if edge.target == node_idx { edge.source }
                       else { continue };

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
