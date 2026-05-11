# Track 3 Octonionic ZEE200 GTZK Implementation

We have successfully reimplemented the Track 3 Octonionic Simulation into a
real C-based ZEE200 GTZK Proof. You can find the track3 code in
`benchmarks/track3/track3.c` and its generated ZK artifacts.

To run:

```bash
./scripts/zkvm/run_zkvm_track3_prover.sh &
./scripts/zkvm/run_zkvm_track3_verifier.sh
```

This generates an actual mathematical proof instead of a Python simulation.
