pub struct PluginManager {}

impl PluginManager {
    pub fn new() -> Self { Self {} }

    pub fn load_plugin(&mut self, _name: &str, _path: &str) -> Result<(), String> {
        Ok(())
    }
}
