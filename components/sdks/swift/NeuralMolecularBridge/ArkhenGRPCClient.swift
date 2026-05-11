import Foundation
import GRPC
import NIO
import NIOHPACK

/// Client for the Layer 7 Neural-Molecular Bridge.
/// Translates biological stochasticity into a ConsciousnessPayload via gRPC.
class ArkhenGRPCClient: ObservableObject {
    private var channel: GRPCChannel?
    private var client: Arkhen_Layer7_MultiverseManagerClient?
    private var stream: BidirectionalStreamingCall<Arkhen_Layer7_ConsciousnessPayload, Arkhen_Layer7_IngestionResponse>?
    
    @Published var connectionStatus: String = "Disconnected"
    @Published var currentLambdaAdjustment: Double = 0.0
    @Published var currentPhaseState: String = "Unknown"
    
    let nodeId = UUID().uuidString
    
    func connect(host: String = "api.arkhen.network", port: Int = 443) {
        let group = MultiThreadedEventLoopGroup(numberOfThreads: 1)
        
        do {
            self.channel = try GRPCChannelPool.with(
                target: .host(host, port: port),
                transportSecurity: .tls(.makeClientConfigurationBackedByNIOSSL()),
                eventLoopGroup: group
            )
            
            self.client = Arkhen_Layer7_MultiverseManagerClient(channel: self.channel!)
            self.connectionStatus = "Connected"
            self.startStream()
            
        } catch {
            self.connectionStatus = "Connection Failed: \(error.localizedDescription)"
        }
    }
    
    private func startStream() {
        guard let client = client else { return }
        
        // Initialize bidirectional stream
        stream = client.streamConsciousness { [weak self] response in
            DispatchQueue.main.async {
                self?.currentLambdaAdjustment = response.lambdaAdjustment
                self?.currentPhaseState = response.phaseState
            }
        }
    }
    
    func transmitConsciousnessPayload(heartRate: Double, hrv: Double) {
        guard let stream = stream, heartRate > 0 else { return }
        
        // Calculate coherence index (simplified mapping for prototype)
        // High HRV generally indicates higher parasympathetic activity (coherence)
        let coherence = min(max(hrv / 100.0, 0.0), 1.0)
        
        // Generate raw entropy bytes from the stochastic noise
        let entropyString = "\(heartRate)-\(hrv)-\(Date().timeIntervalSince1970)"
        let entropyData = Data(entropyString.utf8)
        
        var payload = Arkhen_Layer7_ConsciousnessPayload()
        payload.nodeId = self.nodeId
        payload.heartRate = heartRate
        payload.hrvSdnn = hrv
        payload.coherenceIndex = coherence
        payload.timestamp = Int64(Date().timeIntervalSince1970 * 1000)
        payload.rawEntropy = entropyData
        
        // Transmit to MultiverseManager
        stream.sendMessage(payload).whenFailure { error in
            print("Failed to transmit payload: \(error)")
        }
    }
    
    func disconnect() {
        _ = stream?.sendEnd()
        _ = channel?.close()
        self.connectionStatus = "Disconnected"
    }
}
