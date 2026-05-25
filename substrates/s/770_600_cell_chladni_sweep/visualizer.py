import math

def generate_600_cell_vertices():
    """Generates the 120 vertices of the 600-cell in R4."""
    phi = (1 + math.sqrt(5)) / 2
    inv_phi = 1 / phi

    vertices = []

    # 1. 16-cell vertices: permutations of (0, 0, 0, +/-1) -> 8 vertices
    for i in range(4):
        for sign in [-1, 1]:
            v = [0, 0, 0, 0]
            v[i] = sign
            vertices.append(tuple(v))

    # 2. Tesseract vertices: (+/-0.5, +/-0.5, +/-0.5, +/-0.5) -> 16 vertices
    for i in range(16):
        v = [
            0.5 if (i & 1) else -0.5,
            0.5 if (i & 2) else -0.5,
            0.5 if (i & 4) else -0.5,
            0.5 if (i & 8) else -0.5
        ]
        vertices.append(tuple(v))

    # 3. Icosian vertices: even permutations of (+/- phi/2, +/- 0.5, +/- 1/(2*phi), 0) -> 96 vertices
    base_coords = [phi/2, 0.5, inv_phi/2, 0]

    # Even permutations of indices (0, 1, 2, 3)
    even_perms = [
        (0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2),
        (1, 0, 3, 2), (1, 2, 0, 3), (1, 3, 2, 0),
        (2, 0, 1, 3), (2, 1, 3, 0), (2, 3, 0, 1),
        (3, 0, 2, 1), (3, 1, 0, 2), (3, 2, 1, 0)
    ]

    for perm in even_perms:
        for s1 in [-1, 1]:
            for s2 in [-1, 1]:
                for s3 in [-1, 1]:
                    v = [0, 0, 0, 0]
                    v[perm[0]] = base_coords[0] * s1
                    v[perm[1]] = base_coords[1] * s2
                    v[perm[2]] = base_coords[2] * s3
                    v[perm[3]] = base_coords[3] # 0 has no sign
                    vertices.append(tuple(v))

    # Ensure uniqueness just in case
    return list(set(vertices))

def export_threejs_html(vertices, filepath="600_cell_chladni.html"):
    """Exports an HTML file with Three.js to visualize the 4D to 3D sweep."""

    # Convert vertices to JSON string for JS
    verts_js = "[\n" + ",\n".join(["    [" + ",".join([str(x) for x in v]) + "]" for v in vertices]) + "\n]"

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>600-Cell Chladni Sweep (w-axis)</title>
    <style>
        body { margin: 0; overflow: hidden; background-color: #000; color: #fff; font-family: monospace; }
        #canvas-container { width: 100vw; height: 100vh; }
        #ui-panel { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); padding: 10px; border: 1px solid #333; }
        input[type=range] { width: 300px; }
    </style>
    <!-- Include Three.js from CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>

<div id="ui-panel">
    <h3>600-Cell Chladni Sweep</h3>
    <p>Substrate 770 / Campo ξM (120 Vertices)</p>
    <label for="w-slider">w(t) cross-section: <span id="w-val">0.00</span></label><br/>
    <input type="range" id="w-slider" min="-1" max="1" step="0.01" value="0"><br/>
    <label><input type="checkbox" id="auto-sweep" checked> Auto Sweep</label>
    <p><i>Nodes sized by distance to projection hyperplane.</i></p>
</div>

<div id="canvas-container"></div>

<script>
    const vertices4D = """ + verts_js + """;

    // Setup Three.js
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 2.5;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.getElementById('canvas-container').appendChild(renderer.domElement);

    // Materials
    const materialNode = new THREE.MeshBasicMaterial({ color: 0xffd700 }); // Golden color for Phi coordinates
    const geometryNode = new THREE.SphereGeometry(1, 16, 16);

    // Create meshes for 120 vertices
    const meshes = [];
    const group = new THREE.Group();
    scene.add(group);

    for (let i = 0; i < vertices4D.length; i++) {
        const mesh = new THREE.Mesh(geometryNode, materialNode);
        meshes.push(mesh);
        group.add(mesh);
    }

    // UI Elements
    const wSlider = document.getElementById('w-slider');
    const wValDisplay = document.getElementById('w-val');
    const autoSweepCb = document.getElementById('auto-sweep');

    let time = 0;

    // Projection function
    // For a given w_cut, project nodes close to w_cut.
    // Nodes fade out / shrink based on |w - w_cut|.
    const sliceThickness = 0.2; // How thick the 3D slice in 4D space is

    function updateProjection(w_cut) {
        for (let i = 0; i < vertices4D.length; i++) {
            const v4 = vertices4D[i];
            const x = v4[0];
            const y = v4[1];
            const z = v4[2];
            const w = v4[3];

            // Stereographic projection for visualization base (ignoring w for pure 3D coords, or standard orthographic)
            // We'll use simple orthographic projection dropping w, but scaling based on distance to w_cut
            const dist = Math.abs(w - w_cut);

            const mesh = meshes[i];

            if (dist < sliceThickness) {
                mesh.visible = true;
                // Scale inversely to distance (nodes exactly on slice are largest)
                const scale = 0.08 * (1 - (dist / sliceThickness));
                mesh.scale.set(scale, scale, scale);
                mesh.position.set(x, y, z);

                // Color intensity
                const intensity = Math.floor(255 * (1 - (dist / sliceThickness)));
                mesh.material.color.setRGB(intensity/255, 0.84 * (intensity/255), 0); // Gold tint
            } else {
                mesh.visible = false;
            }
        }
    }

    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);

        let currentW = parseFloat(wSlider.value);

        if (autoSweepCb.checked) {
            time += 0.005;
            currentW = Math.sin(time); // Sweep from -1 to 1 to -1
            wSlider.value = currentW;
        }

        wValDisplay.innerText = currentW.toFixed(2);

        // Rotate the group slightly to view the 3D projection
        group.rotation.x += 0.002;
        group.rotation.y += 0.003;

        updateProjection(currentW);

        renderer.render(scene, camera);
    }

    // Window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    animate();
</script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    vertices = generate_600_cell_vertices()
    print("Generated " + str(len(vertices)) + " vertices for the 600-cell.")
    export_threejs_html(vertices, "600_cell_chladni.html")
    print("Exported 3D visualization to 600_cell_chladni.html")
