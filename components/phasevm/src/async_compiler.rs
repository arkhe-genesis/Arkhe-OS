// phasevm/src/async_compiler.rs — Async JIT compilation via thread pool
use crate::{PhaseVM, PhaseVMError};
use num_complex::Complex64;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use crossbeam_channel::{bounded, Sender, Receiver};

/// Message type for async compilation requests
#[derive(Debug, Clone)]
pub enum CompilationRequest {
    Compile {
        gates: Vec<String>,
        response_tx: Sender<CompilationResult>,
    },
    ClearCache,
    GetStats {
        response_tx: Sender<CacheStats>,
    },
    Warmup {
        circuits: Vec<Vec<String>>,
    },
}

/// Result of async compilation
#[derive(Debug, Clone)]
pub enum CompilationResult {
    Success { jones: Complex64, cache_hit: bool },
    Error { message: String },
    Timeout,
}

/// Cache statistics for monitoring
#[derive(Debug, Clone, Default)]
pub struct CacheStats {
    pub circuit_cache_size: usize,
    pub gate_cache_size: usize,
    pub total_compilations: u64,
    pub cache_hits: u64,
}

/// Async compiler wrapper with dedicated thread pool
pub struct AsyncPhaseVM {
    vm: Arc<Mutex<PhaseVM>>,
    request_tx: Sender<CompilationRequest>,
    _worker_handles: Vec<thread::JoinHandle<()>>,
}

impl AsyncPhaseVM {
    /// Create new async compiler with N worker threads
    pub fn new(num_workers: usize) -> Result<Self, PhaseVMError> {
        let vm = Arc::new(Mutex::new(PhaseVM::new()?));
        let (request_tx, request_rx) = bounded::<CompilationRequest>(100);

        // Spawn worker threads
        let mut handles = Vec::with_capacity(num_workers);
        for _ in 0..num_workers {
            let vm_clone = Arc::clone(&vm);
            let rx_clone = request_rx.clone();

            let handle = thread::spawn(move || {
                worker_loop(vm_clone, rx_clone);
            });
            handles.push(handle);
        }

        // Drop original receiver; workers hold clones
        drop(request_rx);

        Ok(AsyncPhaseVM {
            vm,
            request_tx,
            _worker_handles: handles,
        })
    }

    /// Submit compilation request asynchronously
    pub fn compile_async(
        &self,
        gates: Vec<String>,
        timeout: Duration,
    ) -> Result<Receiver<CompilationResult>, PhaseVMError> {
        let (response_tx, response_rx) = bounded(1);

        self.request_tx
            .send(CompilationRequest::Compile { gates, response_tx })
            .map_err(|_| PhaseVMError::CompilationFailed("Channel closed".into()))?;

        // Optional: spawn timeout watcher
        if timeout < Duration::from_secs(300) {
            let rx_clone = response_rx.clone();
            thread::spawn(move || {
                thread::sleep(timeout);
                // Send timeout if no result yet
                let _ = rx_clone.try_send(CompilationResult::Timeout);
            });
        }

        Ok(response_rx)
    }

    /// Clear compilation cache across all workers
    pub fn clear_cache(&self) -> Result<(), PhaseVMError> {
        self.request_tx
            .send(CompilationRequest::ClearCache)
            .map_err(|_| PhaseVMError::CompilationFailed("Channel closed".into()))?;
        Ok(())
    }

    /// Get cache statistics
    pub fn get_stats(&self) -> Result<CacheStats, PhaseVMError> {
        let (response_tx, response_rx) = bounded(1);
        self.request_tx
            .send(CompilationRequest::GetStats { response_tx })
            .map_err(|_| PhaseVMError::CompilationFailed("Channel closed".into()))?;

        response_rx
            .recv_timeout(Duration::from_millis(100))
            .map_err(|_| PhaseVMError::CompilationFailed("Stats timeout".into()))
    }

    /// Warm up cache with frequent circuits
    pub fn warmup_cache(&self, circuits: Vec<Vec<String>>) -> Result<(), PhaseVMError> {
        self.request_tx
            .send(CompilationRequest::Warmup { circuits })
            .map_err(|_| PhaseVMError::CompilationFailed("Channel closed".into()))?;
        Ok(())
    }
}

/// Worker thread loop: process compilation requests
fn worker_loop(vm: Arc<Mutex<PhaseVM>>, request_rx: Receiver<CompilationRequest>) {
    while let Ok(request) = request_rx.recv() {
        match request {
            CompilationRequest::Compile { gates, response_tx } => {
                let result = {
                    let mut vm_guard = vm.lock().unwrap();
                    // Perform JIT compilation (PhaseVM cache is internal)
                    match vm_guard.compile_circuit(&gates) {
                        Ok(jones) => CompilationResult::Success { jones, cache_hit: false },
                        Err(e) => CompilationResult::Error { message: e.to_string() },
                    }
                };
                let _ = response_tx.send(result);
            }
            CompilationRequest::ClearCache => {
                if let Ok(mut vm_guard) = vm.lock() {
                    vm_guard.clear_cache();
                }
            }
            CompilationRequest::GetStats { response_tx } => {
                let stats = if let Ok(vm_guard) = vm.lock() {
                    CacheStats {
                        circuit_cache_size: vm_guard.cache_size(),
                        gate_cache_size: 4, // default gates
                        total_compilations: 0,
                        cache_hits: 0,
                    }
                } else {
                    CacheStats::default()
                };
                let _ = response_tx.send(stats);
            }
            CompilationRequest::Warmup { circuits } => {
                if let Ok(mut vm_guard) = vm.lock() {
                    for circuit in circuits {
                        let _ = vm_guard.compile_circuit(&circuit);
                    }
                }
            }
        }
    }
}
