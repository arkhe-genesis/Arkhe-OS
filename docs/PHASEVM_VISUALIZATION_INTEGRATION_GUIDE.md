# PhaseVM Visualization Integration Guide

This guide describes the complete bytecode→shader cycle for integrating the PhaseVM Rust JIT compiler with the Python visualization pipeline.

## Overview

The integration provides a real-time cycle:
1. Fetch network state → generate topological bytecode
2. Compile bytecode via PhaseVM JIT → Jones invariant (complex)
3. Map Jones invariant to shader parameters (amplitude, phase, frequency, coupling)
4. Update GPU uniform buffer → trigger re-render
5. (Optional) Feed back visual state to network thresholds via bidirectional UI

## Async JIT Compilation

The JIT compilation is executed asynchronously in a thread pool to avoid blocking the render loop, which is critical for maintaining 60 FPS performance.
