import wgpu
adapter = wgpu.gpu.request_adapter_sync()
device = adapter.request_device_sync(required_features=[])
print("Device requested successfully:", device)
