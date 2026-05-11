use tch::{nn, Device, Tensor};
use anyhow::Result;

/// Carrega modelo CLIP ViT-L/14 e calcula embedding de imagem.
pub fn clip_image_embedding(image_path: &str) -> Result<Vec<f32>> {
    let vs = nn::VarStore::new(Device::Cpu);
    let model = tch::vision::clip::clip_vit_l14(&vs.root(), "path/to/clip_model.pt")?;

    let img = tch::vision::imagenet::load_image(image_path)?
        .unsqueeze(0)
        .to_device(Device::Cpu);

    let features = model.forward_image(&img)?;
    let embedding: Vec<f32> = features.flatten(0, -1).to_kind(tch::Kind::Float).into();
    Ok(embedding)
}