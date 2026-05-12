const { SophonSDK } = require('arkhe-sophon');
const sdk = new SophonSDK('https://oracle.arkhe-os.org');
async function deployAgent(name) {
    const agent = await sdk.createAgent(name, { capabilities: ['infer', 'factor'] });
    console.log(`Agent ${agent.id} deployed`);
}
deployAgent('sophon-002');
