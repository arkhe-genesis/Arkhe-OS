#[cfg(feature = "tch")]
use tch::{CModule, Tensor, Kind, Device, vision::image};
#[cfg(feature = "tch")]
use std::path::Path;

#[cfg(feature = "tch")]
pub struct PerceptualHash {
    model: CModule,
    device: Device,
}

#[cfg(feature = "tch")]
impl PerceptualHash {
    pub fn new(model_path: &str) -> Result<Self, tch::TchError> {
        let device = Device::cuda_if_available();
        let model = CModule::load_on_device(model_path, device)?;
        Ok(PerceptualHash { model, device })
    }

    pub fn compute_hash<P: AsRef<Path>>(&self, image_path: P) -> Result<Tensor, anyhow::Error> {
        let img = image::load(image_path)?;
        let img = img.to_device(self.device);

        let img = image::resize_preserve_aspect_ratio(&img, 224, 224)?;
        let img = img.to_kind(Kind::Float) / 255.0;

        let mean = Tensor::from_slice(&[0.48145466f32, 0.4578275f32, 0.40821073f32]).view([3, 1, 1]).to_device(self.device);
        let std = Tensor::from_slice(&[0.26862954f32, 0.26130258f32, 0.27577711f32]).view([3, 1, 1]).to_device(self.device);
        let img = (img - mean) / std;

        let img = img.unsqueeze(0);

        let output = self.model.forward_ts(&[img])?;
        Ok(output)
    }
}
