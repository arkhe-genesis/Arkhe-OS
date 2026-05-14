export const PluginBuilder = {
    fromTemplate: async (name: string, domain: string, template: string) => ({
        writeToDisk: async (path: string) => {},
        build: async () => ({}),
        getCode: async () => ''
    }),
    loadFromPath: async (path: string) => ({ code: '', metadata: {} }),
    loadPlugin: async (path: string) => ({}),
    loadMetadata: async (path: string) => ({}),
    generateDocs: async (plugin: any, format: string) => ''
};
