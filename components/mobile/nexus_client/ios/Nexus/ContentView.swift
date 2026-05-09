// ContentView.swift
// Nexus iOS — Interface principal do app de streaming soberano

import SwiftUI
import WebRTC

struct ContentView: View {
    @StateObject private var kymManager = KYMManager()
    @StateObject private var streamClient = WebRTCClient()
    @State private var selectedChannel: Channel?
    @State private var isPlaying = false
    @State private var coherenceScore: Float = 0.0

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header com status de identidade
                IdentityHeaderView(
                    isVerified: kymManager.isVerified,
                    phiRisk: kymManager.phiRisk,
                    onReverify: { await kymManager.verifyIdentity() }
                )

                // Grade de canais
                ChannelGridView(
                    channels: streamClient.availableChannels,
                    selectedChannel: $selectedChannel,
                    onChannelSelected: { channel in
                        Task {
                            await joinChannel(channel)
                        }
                    }
                )

                // Player de vídeo (overlay quando reproduzindo)
                if isPlaying, let channel = selectedChannel {
                    VideoPlayerOverlay(
                        channel: channel,
                        coherenceScore: $coherenceScore,
                        onStop: { isPlaying = false }
                    )
                }

                // Barra de status inferior com métricas
                StatusBarView(
                    coherenceScore: coherenceScore,
                    royaltyBalance: kymManager.royaltyBalance,
                    connectionQuality: streamClient.connectionQuality
                )
            }
            .navigationTitle("Nexus")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: showSettings) {
                        Image(systemName: "gear")
                    }
                }
            }
        }
        .task {
            // Inicializar verificação KYM ao abrir o app
            await kymManager.verifyIdentity()
            // Descobrir canais disponíveis
            await streamClient.discoverChannels()
        }
    }

    private func joinChannel(_ channel: Channel) async {
        // Verificar KYM antes de permitir acesso
        guard await kymManager.verifyIdentity() else {
            showError("Verificação de identidade necessária")
            return
        }

        // Unir-se ao stream WebRTC
        do {
            try await streamClient.joinStream(channel)
            selectedChannel = channel
            isPlaying = true

            // Monitorar coerência em tempo real
            Task {
                for await coherence in streamClient.coherenceUpdates {
                    coherenceScore = coherence
                    // Alertar se coerência cair abaixo do threshold
                    if coherence < 0.7 {
                        showCoherenceWarning(coherence)
                    }
                }
            }
        } catch {
            showError("Falha ao conectar: \(error.localizedDescription)")
        }
    }

    private func showError(_ message: String) {
        // Implementar alerta de erro
    }

    private func showCoherenceWarning(_ coherence: Float) {
        // Implementar alerta de baixa coerência
    }

    private func showSettings() {
        // Navegar para tela de configurações
    }
}

// Componente: Header de Identidade
struct IdentityHeaderView: View {
    let isVerified: Bool
    let phiRisk: Float
    let onReverify: () async -> Void

    var body: some View {
        HStack {
            Image(systemName: isVerified ? "checkmark.shield.fill" : "exclamationmark.shield")
                .foregroundColor(isVerified ? .green : .orange)

            VStack(alignment: .leading) {
                Text(isVerified ? "Identidade Verificada" : "Verificação Necessária")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text("Risco Φ: \(phiRisk, specifier: "%.2f")")
                    .font(.subheadline)
                    .foregroundColor(phiRisk < 0.3 ? .green :
                                   phiRisk < 0.6 ? .orange : .red)
            }

            Spacer()

            if !isVerified {
                Button("Verificar") {
                    Task { await onReverify() }
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .background(Color(.systemGray6))
    }
}

// Componente: Grade de Canais
struct ChannelGridView: View {
    let channels: [Channel]
    @Binding var selectedChannel: Channel?
    let onChannelSelected: (Channel) -> Void

    var body: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(channels) { channel in
                    ChannelCard(
                        channel: channel,
                        isSelected: selectedChannel?.id == channel.id,
                        onTap: { onChannelSelected(channel) }
                    )
                }
            }
            .padding()
        }
    }
}

// Componente: Card de Canal
struct ChannelCard: View {
    let channel: Channel
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 8) {
                // Thumbnail do canal
                AsyncImage(url: channel.thumbnailURL) { image in
                    image.resizable().aspectRatio(contentMode: .fill)
                } placeholder: {
                    Color.gray.opacity(0.3)
                }
                .frame(height: 120)
                .cornerRadius(8)

                // Informações do canal
                VStack(alignment: .leading, spacing: 4) {
                    Text(channel.title)
                        .font(.headline)
                        .lineLimit(1)

                    HStack {
                        Image(systemName: "eye")
                        Text("\(channel.viewerCount)")

                        Spacer()

                        // Badge de coerência
                        HStack(spacing: 4) {
                            Circle()
                                .fill(coherenceColor(channel.coherenceScore))
                                .frame(width: 8, height: 8)
                            Text("Φ: \(channel.coherenceScore, specifier: "%.2f")")
                                .font(.caption2)
                        }
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
            }
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }

    private func coherenceColor(_ score: Float) -> Color {
        if score >= 0.85 { return .green }
        if score >= 0.7 { return .yellow }
        return .red
    }
}