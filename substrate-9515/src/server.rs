use crate::types::{Tool, Resource, Transport};
use std::collections::HashMap;

pub struct McpServer {
    tools: HashMap<String, Tool>,
    resources: HashMap<String, Resource>,
    pub transport: Transport,
}

impl McpServer {
    pub fn new(transport: Transport) -> Self {
        Self {
            tools: HashMap::new(),
            resources: HashMap::new(),
            transport,
        }
    }

    pub fn register_tool(&mut self, tool: Tool) {
        self.tools.insert(tool.name.clone(), tool);
    }

    pub fn register_resource(&mut self, resource: Resource) {
        self.resources.insert(resource.name.clone(), resource);
    }

    pub fn start(&self) {
        // Start server based on transport configuration
    }
}
