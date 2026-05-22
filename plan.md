1. **Explore & Prepare**: Review the requirements for Substrates 487, 485-v2, 488, and 489. Ensure to strictly avoid f-strings and non-ASCII characters. Use `tempfile.mkstemp` without specifying `dir`. Cast `numpy.bool_` to Python `bool` for JSON serialization.
2. **Create Substrate 487**: Implement `487-PHOTONIC-CRYSTAL` in `substrates/400-499_advanced/substrato_487_photonic_crystal/substrato_487_photonic_crystal.py`. Set $\Phi_C = 0.985$ and the specified seal.
3. **Create Substrate 485-v2**: Implement `485-HOLOGRAPHIC-PROJECTOR v2.0` in `substrates/400-499_advanced/substrato_485_holographic_v2/substrato_485_holographic_v2.py`. Set $\Phi_C = 0.970$ and the specified seal.
4. **Create Substrate 488**: Implement `488-PHOTONIC-GYROTRON` in `substrates/400-499_advanced/substrato_488_photonic_gyrotron/substrato_488_photonic_gyrotron.py`. Incorporate the provided code, adapt the comments and strings to be strictly ASCII, and set $\Phi_C = 0.950$.
5. **Create Substrate 489**: Implement `489-OPTICAL-COMPUTER` in `substrates/400-499_advanced/substrato_489_optical_computer/substrato_489_optical_computer.py`. Incorporate the provided code, remove non-ASCII characters, and set $\Phi_C = 0.930$.
6. **Testing**: Add integration tests for all 4 new substrates under `tests/unit/` using `importlib.util` to load them correctly. Ensure `PYTHONPATH=src make test` runs without issues for these tests.
7. **Pre-commit**: Complete pre-commit steps to make sure proper testing, verifications, reviews and reflections are done.
8. **Submit**: Submit the changes for the new photonic layer.
