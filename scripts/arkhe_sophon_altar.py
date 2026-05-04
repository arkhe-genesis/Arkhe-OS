import wgpu
import wgpu.backends.wgpu_native  # Select backend
import numpy as np
import time

def run_sophon_altar():
    # Carregar o shader WGSL do Sophon
    with open("shaders/sophon.wgsl", "r") as f:
        wgsl_code = f.read()

    # Try different adapter request syntax
    adapter = wgpu.gpu.request_adapter_sync()
    device = adapter.request_device_sync()

    shader = device.create_shader_module(code=wgsl_code)

    # Uniform buffer: mapear exatamente a struct Uniforms
    # layout: time, res_x, res_y, pad, speed, sphere_size, warp_amp, ...
    # Devido ao alinhamento, precisamos de um array float32 com padding correto.
    uniform_data = np.zeros(32, dtype=np.float32)  # tamanho suficiente
    # Inicializar parâmetros do GUI
    uniform_data[3] = 0.0  # pad
    uniform_data[4] = 1.0  # speed
    uniform_data[5] = 1.0  # sphere_size
    uniform_data[6] = 0.6  # warp_amp
    uniform_data[7] = 1.2  # warp_falloff
    uniform_data[8] = 6.0  # warp_freq
    uniform_data[9] = 10.0 # warp_steps
    uniform_data[10] = -0.4 # warp_velocity
    uniform_data[11] = 0.6  # noise_contrast
    # Cores (normalizadas)
    uniform_data[12:15] = np.array([0.0, 0.164, 1.0])   # color1
    uniform_data[15] = 0.0  # pad
    uniform_data[16:19] = np.array([1.0, 0.0, 0.5])    # color2
    uniform_data[19] = 0.0  # pad
    uniform_data[20:23] = np.array([0.0, 1.0, 0.8])    # color3

    uniform_buffer = device.create_buffer_with_data(
        data=uniform_data,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
    )

    # For now, print success
    print("Sophon shader loaded and uniform buffer created successfully.")

if __name__ == "__main__":
    run_sophon_altar()
