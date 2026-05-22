import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var agent = ArkheAgent()
    @State private var inputText: String = ""

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Main visual area (Status/Agent Representation)
                ZStack {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Color.black.opacity(0.05))

                    VStack {
                        Image(systemName: agent.isProcessing ? "brain.head.profile" : "brain")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 80, height: 80)
                            .foregroundColor(agent.isProcessing ? .orange : .accentColor)
                            .padding()

                        Text(agent.statusMessage)
                            .font(.headline)
                    }
                }
                .frame(maxHeight: 250)
                .padding(.horizontal)

                // Response Area
                ScrollView {
                    Text(agent.responseText)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(12)
                .padding(.horizontal)

                Spacer()

                // Input Area
                HStack(spacing: 12) {
                    // Vision Button
                    Button(action: {
                        Task { await agent.captureAndProcessVision() }
                    }) {
                        Image(systemName: "camera.fill")
                            .font(.system(size: 20))
                            .foregroundColor(.primary)
                            .padding(12)
                            .background(Color.secondary.opacity(0.2))
                            .clipShape(Circle())
                    }

                    // Text Input
                    TextField("Message Arkhe...", text: $inputText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit {
                            submitText()
                        }

                    // Voice Button
                    Button(action: {
                        agent.toggleVoiceRecording()
                    }) {
                        Image(systemName: agent.isRecordingVoice ? "mic.fill" : "mic")
                            .font(.system(size: 20))
                            .foregroundColor(agent.isRecordingVoice ? .red : .white)
                            .padding(12)
                            .background(agent.isRecordingVoice ? Color.red.opacity(0.2) : Color.accentColor)
                            .clipShape(Circle())
                    }
                }
                .padding()
            }
            .navigationTitle("Arkhe")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func submitText() {
        guard !inputText.isEmpty else { return }
        let textToProcess = inputText
        inputText = ""
        Task {
            await agent.processText(textToProcess)
        }
    }
}

// MARK: - Arkhe Agent Logic

@MainActor
class ArkheAgent: ObservableObject {
    @Published var responseText: String = "Waiting for input..."
    @Published var statusMessage: String = "Arkhe Agent Active"
    @Published var isProcessing: Bool = false
    @Published var isRecordingVoice: Bool = false

    private var audioRecorder: AVAudioRecorder?

    func processText(_ text: String) async {
        isProcessing = true
        statusMessage = "Processing Text..."
        responseText = ""

        // Simulate real-time streaming AI response
        let words = "I am processing your text input: '\(text)'. This is a simulated real-time streaming response from the Arkhe multimodal agent.".components(separatedBy: " ")

        for word in words {
            responseText += word + " "
            try? await Task.sleep(nanoseconds: 100_000_000) // 100ms delay per word
        }

        isProcessing = false
        statusMessage = "Arkhe Agent Active"
    }

    func toggleVoiceRecording() {
        if isRecordingVoice {
            stopRecording()
        } else {
            startRecording()
        }
    }

    private func startRecording() {
        // Simplified AVFoundation setup for demonstration
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .default)
            try session.setActive(true)

            let url = FileManager.default.temporaryDirectory.appendingPathComponent("arkhe_voice.m4a")
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 12000,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
            ]

            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.record()

            isRecordingVoice = true
            statusMessage = "Listening..."
            responseText = ""
        } catch {
            responseText = "Failed to start recording: \(error.localizedDescription)"
        }
    }

    private func stopRecording() {
        audioRecorder?.stop()
        isRecordingVoice = false

        Task {
            isProcessing = true
            statusMessage = "Processing Voice..."
            // Simulate processing audio
            try? await Task.sleep(nanoseconds: 1_500_000_000)

            await processText("[Transcribed Voice Audio]")
        }
    }

    func captureAndProcessVision() async {
        isProcessing = true
        statusMessage = "Analyzing Vision..."
        responseText = "Simulating camera capture and Core ML processing..."

        try? await Task.sleep(nanoseconds: 2_000_000_000)

        await processText("[Analyzed Visual Context: A room with a desk]")
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
