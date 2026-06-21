use crate::tensor::{Tensor, TensorDtype};
pub fn sigmoid(x: &Tensor) -> Tensor { x.sigmoid() }
pub fn rms_norm(x: &Tensor, eps: TensorDtype) -> Tensor { x.rms_norm(eps) }
pub fn layer_norm(x: &Tensor, eps: TensorDtype) -> Tensor { x.layer_norm(eps) }
pub fn softmax(x: &Tensor, axis: usize) -> Tensor { x.softmax(axis) }
pub fn gelu(x: &Tensor) -> Tensor { x.gelu() }
pub fn relu(x: &Tensor) -> Tensor { x.relu() }
pub fn swiglu_clamp(gate: &Tensor, up: &Tensor, clamp_limit: TensorDtype) -> Tensor { gate.swiglu_clamp(gate, up, clamp_limit) }
pub fn compute_rope_frequencies(dim: usize, theta: f32, max_seq_len: usize) -> (Vec<f32>, Vec<f32>) { let inv_freq: Vec<f32> = (0..dim / 2).map(|i| 1.0 / theta.powf(2.0 * i as f32 / dim as f32)).collect(); let mut cos_cache = Vec::with_capacity(max_seq_len * dim / 2); let mut sin_cache = Vec::with_capacity(max_seq_len * dim / 2); for pos in 0..max_seq_len { for freq in &inv_freq { let angle = pos as f32 * freq; cos_cache.push(angle.cos()); sin_cache.push(angle.sin()); } } (cos_cache, sin_cache) }
pub fn apply_rope(x: &Tensor, cos_cache: &[f32], sin_cache: &[f32], pos: usize, head_dim: usize) -> Tensor { let mut result = x.clone(); let half_dim = head_dim / 2; for i in 0..half_dim { let cos = cos_cache[pos * half_dim + i]; let sin = sin_cache[pos * half_dim + i]; let x0 = result.get(&[i]); let x1 = result.get(&[i + half_dim]); result.set(&[i], x0 * cos - x1 * sin); result.set(&[i + half_dim], x0 * sin + x1 * cos); } result }
pub fn clip_gradients(grads: &mut [Tensor], max_norm: TensorDtype) { let mut total_norm = 0.0f32; for grad in grads.iter() { total_norm += grad.mapv(|v| v * v).sum_all(); } total_norm = total_norm.sqrt(); if total_norm > max_norm { let scale = max_norm / total_norm; for grad in grads.iter_mut() { *grad = grad.scale(scale); } } }
pub fn cosine_lr_schedule(step: u64, warmup_steps: u64, total_steps: u64, max_lr: f64, min_lr: f64,) -> f64 { if step < warmup_steps { max_lr * (step as f64 / warmup_steps as f64) } else { let progress = (step - warmup_steps) as f64 / (total_steps - warmup_steps) as f64; min_lr + (max_lr - min_lr) * 0.5 * (1.0 + (std::f64::consts::PI * progress).cos()) } }
