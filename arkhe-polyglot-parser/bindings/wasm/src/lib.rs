// ============================================================================
// ARKHE P³ — WebAssembly Bindings
// ============================================================================

#![cfg_attr(feature = "wasm", no_std)]

#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

#[cfg(feature = "wasm")]
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub struct PolyglotParserWasm {
    inner: parser_core::PolyglotParser,
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
impl PolyglotParserWasm {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self {
            inner: parser_core::PolyglotParser::new(None),
        }
    }

    /// Detectar linguagem
    pub fn detect_language(&self, source: &str, filename: Option<String>) -> JsValue {
        let detection = self.inner.detect_language(source, filename.as_deref());
        serde_wasm_bindgen::to_value(&detection).unwrap()
    }

    /// Parse
    pub fn parse(&mut self, source: &str, filename: Option<String>) -> Result<JsValue, JsValue> {
        let result = self.inner.parse(source, filename.as_deref())
            .map_err(|e| JsValue::from_str(&e))?;
        serde_wasm_bindgen::to_value(&result).map_err(|e| e.into())
    }

    /// Transpilar
    pub fn transpile(
        &mut self,
        source: &str,
        from: Option<String>,
        to: String,
    ) -> Result<JsValue, JsValue> {
        let result = self.inner.transpile(source, from.as_deref(), &to)
            .map_err(|e| JsValue::from_str(&e))?;
        serde_wasm_bindgen::to_value(&result).map_err(|e| e.into())
    }

    /// Análise semântica
    pub fn analyze(&self, source: &str, language: &str) -> JsValue {
        let analysis = self.inner.analyze_cross_language(source, language);
        serde_wasm_bindgen::to_value(&analysis).unwrap()
    }

    /// Registrar linguagem
    pub fn register_language(&mut self, name: &str, grammar_data: &[u8]) -> Result<(), JsValue> {
        self.inner.register_language(name, grammar_data, None)
            .map_err(|e| JsValue::from_str(&e))
    }

    /// Listar linguagens
    pub fn list_languages(&self) -> JsValue {
        let langs: Vec<(String, f64)> = vec![]; // fallback placeholder // self.inner.get_language_registry().list_all();
        serde_wasm_bindgen::to_value(&langs).unwrap()
    }
}
// wasm bindings
