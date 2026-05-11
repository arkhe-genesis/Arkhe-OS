import SwiftUI

struct ContentView: View {
    @StateObject private var healthManager = HealthKitManager()
    @StateObject private var arkhenClient = ArkhenGRPCClient()
    
    // Timer to sample and transmit data at 1Hz
    let timer = Timer.publish(every: 1.0, on: .main, in: .common).autoconnect()
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Arkhe(n) Layer 7")
                .font(.system(size: 24, weight: .bold, design: .monospaced))
                .foregroundColor(.cyan)
            
            Text("Neural-Molecular Bridge")
                .font(.system(size: 14, weight: .regular, design: .monospaced))
                .foregroundColor(.gray)
            
            Divider().background(Color.cyan.opacity(0.3))
            
            // Biometric Telemetry
            VStack(alignment: .leading, spacing: 15) {
                HStack {
                    Text("Heart Rate (BPM):")
                        .font(.system(size: 14, design: .monospaced))
                        .foregroundColor(.gray)
                    Spacer()
                    Text(String(format: "%.1f", healthManager.currentHeartRate))
                        .font(.system(size: 18, weight: .bold, design: .monospaced))
                        .foregroundColor(.red)
                }
                
                HStack {
                    Text("Stochastic Noise (HRV):")
                        .font(.system(size: 14, design: .monospaced))
                        .foregroundColor(.gray)
                    Spacer()
                    Text(String(format: "%.1f ms", healthManager.currentHRV))
                        .font(.system(size: 18, weight: .bold, design: .monospaced))
                        .foregroundColor(.purple)
                }
                
                HStack {
                    Text("Coherence Index (λ₂):")
                        .font(.system(size: 14, design: .monospaced))
                        .foregroundColor(.gray)
                    Spacer()
                    let coherence = min(max(healthManager.currentHRV / 100.0, 0.0), 1.0)
                    Text(String(format: "%.3f", coherence))
                        .font(.system(size: 18, weight: .bold, design: .monospaced))
                        .foregroundColor(.green)
                }
            }
            .padding()
            .background(Color.black.opacity(0.5))
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(Color.cyan.opacity(0.3), lineWidth: 1)
            )
            
            // Arkhe(n) Feedback
            VStack(alignment: .leading, spacing: 10) {
                Text("MultiverseManager Feedback")
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundColor(.cyan)
                
                HStack {
                    Text("Status:")
                        .font(.system(size: 12, design: .monospaced))
                    Spacer()
                    Text(arkhenClient.connectionStatus)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(arkhenClient.connectionStatus == "Connected" ? .green : .red)
                }
                
                HStack {
                    Text("Phase State:")
                        .font(.system(size: 12, design: .monospaced))
                    Spacer()
                    Text(arkhenClient.currentPhaseState)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(.purple)
                }
            }
            .padding()
            .background(Color.black.opacity(0.5))
            .cornerRadius(10)
            
            Spacer()
            
            Button(action: {
                if !healthManager.isAuthorized {
                    healthManager.requestAuthorization()
                }
                if arkhenClient.connectionStatus != "Connected" {
                    arkhenClient.connect()
                }
            }) {
                Text(arkhenClient.connectionStatus == "Connected" ? "BRIDGE ACTIVE" : "INITIALIZE BRIDGE")
                    .font(.system(size: 16, weight: .bold, design: .monospaced))
                    .foregroundColor(arkhenClient.connectionStatus == "Connected" ? .black : .cyan)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(arkhenClient.connectionStatus == "Connected" ? Color.cyan : Color.clear)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.cyan, lineWidth: 2)
                    )
            }
        }
        .padding()
        .background(Color(red: 0.05, green: 0.05, blue: 0.07).edgesIgnoringSafeArea(.all))
        .preferredColorScheme(.dark)
        .onReceive(timer) { _ in
            if arkhenClient.connectionStatus == "Connected" {
                arkhenClient.transmitConsciousnessPayload(
                    heartRate: healthManager.currentHeartRate,
                    hrv: healthManager.currentHRV
                )
            }
        }
    }
}
