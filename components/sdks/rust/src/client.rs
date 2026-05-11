use reqwest::{Client, header};
use serde::{Deserialize, Serialize};
use std::error::Error;

pub struct ArkhenClient {
    base_url: String,
    client: Client,
}

#[derive(Serialize)]
pub struct ThreatPayload {
    pub r#type: String,
}

#[derive(Serialize, Default)]
pub struct ParameterPayload {
    #[serde(rename = "couplingStrength", skip_serializing_if = "Option::is_none")]
    pub coupling_strength: Option<f64>,
    #[serde(rename = "lambdaThreshold", skip_serializing_if = "Option::is_none")]
    pub lambda_threshold: Option<f64>,
    #[serde(rename = "autoMitigate", skip_serializing_if = "Option::is_none")]
    pub auto_mitigate: Option<bool>,
}

impl ArkhenClient {
    pub fn new(base_url: &str, api_key: Option<&str>) -> Result<Self, Box<dyn Error>> {
        let mut headers = header::HeaderMap::new();
        headers.insert("X-Arkhen-Client", header::HeaderValue::from_static("rust-sdk/1.0.0"));
        
        if let Some(key) = api_key {
            let auth_value = format!("Bearer {}", key);
            headers.insert(header::AUTHORIZATION, header::HeaderValue::from_str(&auth_value)?);
        }

        let client = Client::builder()
            .default_headers(headers)
            .build()?;

        Ok(ArkhenClient {
            base_url: base_url.trim_end_matches('/').to_string(),
            client,
        })
    }

    pub async fn get_health(&self) -> Result<String, Box<dyn Error>> {
        let res = self.client.get(&format!("{}/api/health", self.base_url))
            .send()
            .await?
            .text()
            .await?;
        Ok(res)
    }

    pub async fn inject_threat(&self, threat_type: &str) -> Result<String, Box<dyn Error>> {
        let payload = ThreatPayload { r#type: threat_type.to_string() };
        let res = self.client.post(&format!("{}/api/trigger-attack", self.base_url))
            .json(&payload)
            .send()
            .await?
            .text()
            .await?;
        Ok(res)
    }

    pub async fn update_parameters(&self, params: ParameterPayload) -> Result<String, Box<dyn Error>> {
        let res = self.client.post(&format!("{}/api/parameters", self.base_url))
            .json(&params)
            .send()
            .await?
            .text()
            .await?;
        Ok(res)
    }
}
