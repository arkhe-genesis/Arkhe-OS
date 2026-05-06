const MAX_NODES = 10000;

async function initWebGPU() {
    return "gpu";
}

function createParticleBuffer(device, size) {
    return "buffer";
}

function updateParticles(buffer, nodes) {
}

function drawTeleportArcs(teleports) {
}

function updatePhiMeter(globalPhi) {
}

async function start() {
    const ws = new WebSocket('ws://localhost:8080/phi-field');
    const gpuDevice = await initWebGPU();
    const particleBuffer = createParticleBuffer(gpuDevice, MAX_NODES);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateParticles(particleBuffer, data.nodes); // color = coherence
        drawTeleportArcs(data.teleports);
        updatePhiMeter(data.globalPhi);
    };
}
