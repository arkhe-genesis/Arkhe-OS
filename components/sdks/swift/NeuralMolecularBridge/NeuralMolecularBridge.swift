// NeuralMolecularBridge.swift
// Arkhe(n) Layer 7: Biological Substrate Interface
// Platform: iOS 17+ / watchOS 10+
// 
// Translates biometric signals into ConsciousnessPayload for MultiverseManager

import Foundation
import HealthKit
import CoreMotion
import Combine
import GRPC
import NIO

// ═══════════════════════════════════════════════════════════════════════
// MARK: - Constants
// ═══════════════════════════════════════════════════════════════════════

/// π⁵ resonance frequency
let PI_5: Double = 306.0196847852814532

/// Golden ratio coherence threshold
let PHI: Double = 1.618033988749895

/// Sampling interval (ms) — matches EYFP T₂ coherence window
let SAMPLE_INTERVAL_MS: Int = 16

// ═══════════════════════════════════════════════════════════════════════
// MARK: - Biometric Data Structures
// ═══════════════════════════════════════════════════════════════════════

/// Represents a single biometric sample
struct BiometricSample {
    let timestamp: UInt64
    let heartRate: Double          // BPM
    let hrVariance: Double         // HRV in ms
    let skinConductance: Double    // μS
    let acceleration: Vector3
    let gyroscopic: Vector3
    
    /// Compute phase from HRV (stochastic to phase mapping)
    func computePhase() -> ComplexPhase {
        // HRV maps to phase angle: low HRV (stress) = high frequency
        // High HRV (relaxed) = low frequency, high amplitude
        let normalizedHRV = min(hrVariance / 100.0, 1.0)  // Normalize to 0-1
        
        // Phase angle: stress (low HRV) → high frequency oscillation
        let phaseAngle = (1.0 - normalizedHRV) * 2.0 * .pi
        
        // Amplitude: coherence proxy
        let amplitude = normalizedHRV
        
        return ComplexPhase(
            real: amplitude * cos(phaseAngle),
            imaginary: amplitude * sin(phaseAngle)
        )
    }
    
    /// Compute coherence (λ₂)
    func computeCoherence() -> Double {
        // Simplified coherence from HRV
        let hrvNormalized = hrVariance / 50.0  // Normalize
        let hrCoherence = 1.0 / (1.0 + abs(heartRate - 70.0) / 20.0)  // Optimal ~70 BPM
        
        return min(hrvNormalized * hrCoherence, 2.0)  // Cap at 2.0
    }
}

/// 3D vector
struct Vector3 {
    let x: Double
    let y: Double
    let z: Double
    
    func magnitude() -> Double {
        sqrt(x*x + y*y + z*z)
    }
}

/// Complex phase representation
struct ComplexPhase {
    let real: Double
    let imaginary: Double
    
    var magnitude: Double {
        sqrt(real * real + imaginary * imaginary)
    }
    
    var argument: Double {
        atan2(imaginary, real)
    }
}

// ═══════════════════════════════════════════════════════════════════════
// MARK: - Consciousness Payload
// ═══════════════════════════════════════════════════════════════════════

/// Consciousness Payload for gRPC transmission
struct ConsciousnessPayload {
    let nodeId: String
    let timestamp: UInt64
    let samples: [BiometricSample]
    let globalPhase: ComplexPhase
    let coherence: Double
    let isStable: Bool
    
    /// Convert to gRPC message
    func toGrpcMessage() -> Arkhe_V1_ConsciousnessPayload {
        var message = Arkhe_V1_ConsciousnessPayload()
        message.nodeID = nodeId
        
        // Convert samples to neural patterns
        for sample in samples {
            var pattern = Arkhe_V1_ConsciousnessPayload.NeuralPattern()
            pattern.neuronID = UInt64.random(in: 0..<10000)
            pattern.amplitude = Float(sample.computePhase().magnitude)
            
            // Quantum signature
            var sig = Arkhe_V1_ComplexPhase()
            sig.real = sample.computePhase().real
            sig.imag = sample.computePhase().imaginary
            pattern.quantumSignature = sig
            
            message.patterns.append(pattern)
        }
        
        // IIT Φ metric (simplified)
        message.phiIIT = Float(coherence)
        
        // Collective coherence
        message.collectiveLambda = Float(coherence)
        
        return message
    }
}

// ═══════════════════════════════════════════════════════════════════════
// MARK: - Neural-Molecular Bridge
// ═══════════════════════════════════════════════════════════════════════

/// The Neural-Molecular Bridge
@MainActor
class NeuralMolecularBridge: ObservableObject {
    
    // MARK: - Published Properties
    @Published var isCollecting = false
    @Published var currentCoherence: Double = 0.0
    @Published var currentPhase: ComplexPhase = ComplexPhase(real: 0, imaginary: 0)
    @Published var sampleCount: Int = 0
    
    // MARK: - Private Properties
    private let healthStore = HKHealthStore()
    private let motionManager = CMMotionManager()
    
    private var sampleBuffer: [BiometricSample] = []
    private var cancellables = Set<AnyCancellable>()
    
    private var grpcClient: Arkhe_V1_CoherenceOracleAsyncClient?
    private var nodeIdentity: Arkhe_V1_NodeIdentity?
    
    // Configuration
    private let config: BridgeConfig
    
    // MARK: - Initialization
    
    init(config: BridgeConfig = .default) {
        self.config = config
        
        Task {
            await setupHealthKit()
            await setupMotion()
            await setupGrpc()
        }
    }
    
    // MARK: - Setup
    
    private func setupHealthKit() async {
        guard HKHealthStore.isHealthDataAvailable() else {
            print("⚠ HealthKit not available")
            return
        }
        
        let types: Set = [
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!
        ]
        
        do {
            try await healthStore.requestAuthorization(toShare: nil, read: types)
            print("✓ HealthKit authorized")
        } catch {
            print("⚠ HealthKit authorization failed: \(error)")
        }
    }
    
    private func setupMotion() async {
        guard motionManager.isAccelerometerAvailable else {
            print("⚠ Accelerometer not available")
            return
        }
        
        motionManager.accelerometerUpdateInterval = 1.0 / 60.0  // 60 Hz
        motionManager.gyroUpdateInterval = 1.0 / 60.0
        
        print("✓ Motion sensors configured")
    }
    
    private func setupGrpc() async {
        do {
            let group = PlatformSupport.makeEventLoopGroup(loopCount: 1)
            
            let channel = try GRPCChannelPool.with(
                target: .host(config.multiverseHost, port: config.multiversePort),
                transportSecurity: .plaintext,
                eventLoopGroup: group
            )
            
            grpcClient = Arkhe_V1_CoherenceOracleAsyncClient(channel: channel)
            
            // Register node
            var identity = Arkhe_V1_NodeIdentity()
            identity.nodeID = config.nodeId
            
            var substrate = Arkhe_V1_NodeIdentity.BiologicalSubstrate()
            substrate.eyfpLineage = "NeuralBridge-iOS"
            substrate.temperatureK = 310.0
            substrate.qubitCount = UInt32(config.bufferSize)
            identity.biological = substrate
            
            nodeIdentity = identity
            
            print("✓ gRPC connected to \(config.multiverseHost):\(config.multiversePort)")
        } catch {
            print("⚠ gRPC connection failed: \(error)")
        }
    }
    
    // MARK: - Collection
    
    /// Start collecting biometric data
    func startCollection() async {
        guard !isCollecting else { return }
        
        isCollecting = true
        sampleBuffer.removeAll()
        
        print("🜏 Neural-Molecular Bridge ACTIVE")
        print("   Sampling at \(SAMPLE_INTERVAL_MS)ms intervals")
        print("   Buffer size: \(config.bufferSize)")
        
        // Start motion updates
        motionManager.startAccelerometerUpdates()
        motionManager.startGyroUpdates()
        
        // Start HeartKit query
        await startHeartRateQuery()
        
        // Start processing loop
        await processLoop()
    }
    
    /// Stop collecting
    func stopCollection() async {
        isCollecting = false
        
        motionManager.stopAccelerometerUpdates()
        motionManager.stopGyroUpdates()
        
        print("🜏 Neural-Molecular Bridge STOPPED")
        print("   Total samples: \(sampleCount)")
        print("   Final coherence: \(currentCoherence)")
    }
    
    private func startHeartRateQuery() async {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return
        }
        
        let query = HKObserverQuery(sampleType: heartRateType, predicate: nil) { [weak self] _, _, error in
            if let error = error {
                print("⚠ Heart rate query error: \(error)")
                return
            }
            
            Task { [weak self] in
                await self?.fetchLatestHeartRate()
            }
        }
        
        healthStore.execute(query)
    }
    
    private func fetchLatestHeartRate() async {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return
        }
        
        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)
        let query = HKSampleQuery(
            sampleType: heartRateType,
            predicate: nil,
            limit: 1,
            sortDescriptors: [sortDescriptor]
        ) { [weak self] _, samples, _ in
            guard let sample = samples?.first as? HKQuantitySample else { return }
            
            let heartRate = sample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
            
            Task { [weak self] in
                await self?.processHeartRate(heartRate)
            }
        }
        
        healthStore.execute(query)
    }
    
    private func processHeartRate(_ heartRate: Double) async {
        // Get motion data
        let accel = motionManager.accelerometerData?.acceleration ?? CMAcceleration(x: 0, y: 0, z: 0)
        let gyro = motionManager.gyroData?.rotationRate ?? CMRotationRate(x: 0, y: 0, z: 0)
        
        // Create sample
        let sample = BiometricSample(
            timestamp: UInt64(Date().timeIntervalSince1970 * 1_000_000_000),
            heartRate: heartRate,
            hrVariance: 50.0,  // Would fetch from HRV query
            skinConductance: 0.0,  // Would require external sensor
            acceleration: Vector3(x: accel.x, y: accel.y, z: accel.z),
            gyroscopic: Vector3(x: gyro.x, y: gyro.y, z: gyro.z)
        )
        
        sampleBuffer.append(sample)
        
        // Trim buffer
        if sampleBuffer.count > config.bufferSize {
            sampleBuffer.removeFirst()
        }
        
        sampleCount += 1
        
        // Update published properties
        currentPhase = sample.computePhase()
        currentCoherence = sample.computeCoherence()
    }
    
    private func processLoop() async {
        while isCollecting {
            try? await Task.sleep(nanoseconds: UInt64(SAMPLE_INTERVAL_MS * 1_000_000))
            
            if sampleBuffer.count >= config.bufferSize {
                await sendConsciousnessPayload()
            }
        }
    }
    
    // MARK: - gRPC Transmission
    
    private func sendConsciousnessPayload() async {
        guard let client = grpcClient else { return }
        
        let payload = ConsciousnessPayload(
            nodeId: config.nodeId,
            timestamp: UInt64(Date().timeIntervalSince1970 * 1_000_000_000),
            samples: Array(sampleBuffer.suffix(config.bufferSize)),
            globalPhase: currentPhase,
            coherence: currentCoherence,
            isStable: currentCoherence >= PHI
        )
        
        do {
            let message = payload.toGrpcMessage()
            let _ = try await client.reportState(message)
            
            if config.verboseLogging {
                print("↑ ConsciousnessPayload sent")
                print("  λ₂ = \(String(format: "%.3f", currentCoherence))")
                print("  Phase = \(String(format: "%.2f", currentPhase.argument)) rad")
            }
        } catch {
            print("⚠ Failed to send payload: \(error)")
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// MARK: - Configuration
// ═══════════════════════════════════════════════════════════════════════

struct BridgeConfig {
    let nodeId: String
    let multiverseHost: String
    let multiversePort: Int
    let bufferSize: Int
    let verboseLogging: Bool
    
    static var `default`: BridgeConfig {
        BridgeConfig(
            nodeId: "TEKNET-iOS-\(UIDevice.current.identifierForVendor?.uuidString.prefix(8) ?? "unknown")",
            multiverseHost: "host.docker.internal",
            multiversePort: 50052,
            bufferSize: 100,
            verboseLogging: true
        )
    }
}

// ═══════════════════════════════════════════════════════════════════════
// MARK: - SwiftUI View
// ═══════════════════════════════════════════════════════════════════════

import SwiftUI

struct NeuralBridgeView: View {
    @StateObject private var bridge = NeuralMolecularBridge()
    
    var body: some View {
        VStack(spacing: 20) {
            // Title
            Text("🜏 Neural-Molecular Bridge")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            // Coherence display
            ZStack {
                Circle()
                    .stroke(
                        bridge.currentCoherence >= PHI ? Color.green : Color.orange,
                        lineWidth: 4
                    )
                    .frame(width: 150, height: 150)
                
                VStack {
                    Text("λ₂")
                        .font(.caption)
                    Text(String(format: "%.3f", bridge.currentCoherence))
                        .font(.title)
                        .fontWeight(.bold)
                    
                    if bridge.currentCoherence >= PHI {
                        Text("COHERENT")
                            .font(.caption2)
                            .foregroundColor(.green)
                    } else {
                        Text("DECOHERENT")
                            .font(.caption2)
                            .foregroundColor(.orange)
                    }
                }
            }
            
            // Phase display
            HStack {
                VStack {
                    Text("Phase")
                        .font(.caption)
                    Text(String(format: "%.2f rad", bridge.currentPhase.argument))
                        .font(.headline)
                }
                
                Spacer()
                
                VStack {
                    Text("Samples")
                        .font(.caption)
                    Text("\(bridge.sampleCount)")
                        .font(.headline)
                }
            }
            .padding(.horizontal)
            
            // Control button
            Button(action: {
                Task {
                    if bridge.isCollecting {
                        await bridge.stopCollection()
                    } else {
                        await bridge.startCollection()
                    }
                }
            }) {
                Text(bridge.isCollecting ? "Stop Bridge" : "Start Bridge")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(bridge.isCollecting ? Color.red : Color.green)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .padding(.horizontal)
            
            // Status
            Text(bridge.isCollecting ? "🟢 Collecting biometric data..." : "⚪ Bridge inactive")
                .font(.caption)
        }
        .padding()
    }
}
