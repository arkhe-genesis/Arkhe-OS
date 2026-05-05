1. **Fix dnspython import issue:** Install `dnspython` using pip since the script requires `dns.resolver`.
2. **Implement IPFS Node logic:**
    - Since the prompt explicitly requests "deploy da rede ARKHE sobre IPFS e a ativação do roteamento interplanetário com handshake quântico", we need to create an IPFS integration script (`arkhe_os/network/interplanetary_ipfs.py`).
    - The new script will integrate IPFS via a simulated daemon/node wrapper, and a "handshake quântico".
3. **Write the code for Interplanetary Routing over IPFS:**
    - `ArkheIPFSNode`: A wrapper to interface with IPFS via REST APIs or mock interactions (for simulation purposes).
    - `QuantumHandshakeProtocol`: Implement a handshake protocol combining IPFS DHT with a quantum key exchange simulator.
    - `InterplanetaryRouter`: Route packets through IPFS.
4. **Complete pre commit steps**: Ensure proper verification by running the new file.
5. **Submit the change**.
