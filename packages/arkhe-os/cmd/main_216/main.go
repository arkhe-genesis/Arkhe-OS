package main

import (
	"context"
	"log"
	"time"

	"arkhe/ai"
	"arkhe/integration"
)

func main() {
	// Configurar canal de gradientes
	gradientChannel := ai.NewCoherenceGradientChannel(
		"container_coherence_channel",
		"arkhe_node_earth_001",
		"containerization",
		nil,
		ai.ChannelConfig{
			EnablePrivacyProtection: false,
			AggregationStrategy:     "weighted_average",
		},
	)

	// Configurar orquestrador
	containerConfig := integration.ContainerizationIntegrationConfig{
		ScanIntervalSec:      180, // Scan a cada 3 minutos (containers são dinâmicos)
		EnableCoherenceMap:   true,
		EnableAutoPromotion:  true,
		CoherenceThreshold:   0.70,
		MonitorManifestPaths: []string{"/k8s/manifests", "/deployments"},
		MonitorLogPaths:      []string{"/var/log/containers", "/var/log/pods"},
		PollKubectl:          true,
		PollDocker:           false,
		KubeConfigPath:       "/home/user/.kube/config",
	}

	orchestrator, err := integration.NewContainerizationIntegrationOrchestrator(
		containerConfig,
		gradientChannel,
	)
	if err != nil {
		log.Fatalf("Failed to create containerization integration orchestrator: %v", err)
	}

	// Registrar callbacks
	orchestrator.RegisterIntegrationCallback(func(event integration.IntegrationEvent) {
		log.Printf("🔗 Containerization event [%s]: %v", event.EventType, event.Data)
	})

	// Iniciar scan contínuo
	ctx := context.Background()
	go orchestrator.StartContinuousScanning(ctx)

	log.Printf("✅ Containerization integration orchestrator started")

	time.Sleep(2 * time.Second) // Run for a short time in tests
}
