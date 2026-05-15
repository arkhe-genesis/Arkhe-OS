1. **Create the Project Structure:**
   - Create directories `arkhe-service-template/src`, `arkhe-service-template/tests`, `arkhe-service-template/k8s`.

2. **Create Python Source Files in `src/`:**
   - `__init__.py`
   - `service.py` (FastAPI service with sidecar and security)
   - `sidecar.py` (ArkheSidecar, TemporalChainClient, GuardianClient, QBusClient)
   - `security.py` (HybridSigner)
   - `config.py` (Configuration loader)
   - `metrics.py` (Empty or basic metrics exporter)

3. **Create Testing and Deployment Files:**
   - `tests/test_service.py`
   - `Dockerfile`
   - `docker-compose.yaml`
   - `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/hpa.yaml`
   - `config.yaml.example`
   - `requirements.txt`
   - `Cargo.toml`, `go.mod` (Basic files for Rust and Go as requested)
   - `README.md`

4. **Create Root-level Demonstration and Test Script:**
   - `substrato_196_boilerplate.py` to output the canonical seal and boilerplate structure.
   - `test_substrato_196.py` to run the pytest suite against `arkhe-service-template/tests/test_service.py`.

5. **Pre-commit Steps:**
   - Run `pre_commit_instructions` tool to ensure all verifications, reviews, and tests are passed.

6. **Submit:**
   - Commit the changes and push to a new branch for Substrato 196.
