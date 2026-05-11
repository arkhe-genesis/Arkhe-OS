// arkhe_os/dashboard/webgpu/color_mapping.wgsl
// Converte coerência Φ_C ∈ [0,1] para cor CIELAB→sRGB

fn cielab_to_xyz(lab: vec3f) -> vec3f {
  // Convert CIELAB to XYZ (D65 illuminant)
  let fy = (lab.x + 16.0) / 116.0;
  let fx = fy + lab.y / 500.0;
  let fz = fy - lab.z / 200.0;

  let xyz = vec3f(
    fx * fx * fx > 0.008856 ? fx * fx * fx : (fx - 16.0/116.0) / 7.787,
    lab.x > 0.008856 ? pow((lab.x + 16.0) / 116.0, 3.0) : lab.x / 903.3,
    fz * fz * fz > 0.008856 ? fz * fz * fz : (fz - 16.0/116.0) / 7.787
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
  let rgb = clamp(linear_rgb, 0.0, 1.0);
  return vec4f(rgb, 1.0);
}
