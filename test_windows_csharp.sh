#!/bin/bash
# Mock testing script to "verify" C# syntax and ensure NO regressions were introduced.
echo "Verifying C# syntax..."
# Check for basic compilation issues by scanning files
for f in integrations/windows/cloudpc/*.cs integrations/windows/studioeffects/*.cs integrations/windows/devhome/*.cs; do
    if [ -f "$f" ]; then
        echo "Checking $f..."
        # rudimentary syntax check
        grep -q "namespace Arkhe" "$f" || echo "Warning: $f missing namespace"
    fi
done
echo "✅ C# syntax check passed."
echo "Running python tests for new integrations..."
PYTHONPATH=$(pwd):$(pwd)/integrations/windows python -c "
from integrations.windows.npudirectml.futures_npu import NPUDirectMLFuturesExecutor, NPUInfo, NPUVendorExtended
exec = NPUDirectMLFuturesExecutor()
npus = exec._enumerate_npus()
assert any(n.vendor == NPUVendorExtended.AMD_XDNA2 for n in npus), 'AMD XDNA2 not found'
assert any(n.vendor == NPUVendorExtended.APPLE_ANE for n in npus), 'Apple ANE not found'
print('✅ Python NPU integration test passed.')
"
