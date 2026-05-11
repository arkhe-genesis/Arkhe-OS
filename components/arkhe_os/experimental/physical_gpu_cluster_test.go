package experimental

import (
	"context"
	"fmt"
	"math/rand"
	"testing"
	"time"

	"arkhe_os/integration"
	"arkhe_os/network"
)

// Simula dataSource do DataCenterFrontend
type SimulatedClusterDataSource struct {
	iteration int
}

func (s *SimulatedClusterDataSource) Collect() ([]byte, error) {
	s.iteration++
	// Simula saída de nvidia-smi para um cluster de 16 GPUs
	var output string
	for i := 0; i < 16; i++ {
		temp := 45 + rand.Intn(15)
		power := 150 + rand.Intn(150)
		output += fmt.Sprintf("%d, Tesla V100-SXM2-32GB, 32510 MiB, %d C, %d W, 300 W\n", i, temp, power)
	}
	// Simula log de treinamento
	output += fmt.Sprintf("epoch 1/10 loss=%.4f acc=%.4f grad_norm=%.4f throughput=%.2f\n",
		2.5-float64(s.iteration)*0.1, 0.5+float64(s.iteration)*0.02, 1.5, 120.5)

	return []byte(output), nil
}

func TestPhysicalGPUClusterIntegration(t *testing.T) {
	// 1. Configurar Wheeler Mesh mock
	wheelerMesh := network.NewWheelerMeshProtocol(
		"test_node_001",
		network.MeshConfig{
			EnableQuantumChannels: true,
			DefaultFidelityTarget: 0.99,
		},
	)

	// 2. Configurar Integrador
	config := integration.IntegrationConfig{
		ParseIntervalSec:      1, // Rápido para teste
		PromotionEnabled:      true,
		GradientMappingEnabled: true,
		MinGPUsForPromotion:   8,
		CoherenceThreshold:    0.60, // Limiar baixo para garantir promoção no teste
		PromotionHysteresis:   0.05,
	}

	orch, err := integration.NewDataCenterIntegrationOrchestrator(
		"test_cluster_01",
		"datacenter_test_lab",
		wheelerMesh,
		config,
	)

	if err != nil {
		t.Fatalf("Erro ao criar orquestrador: %v", err)
	}

	// 3. Registrar Callbacks para monitorar o teste
	promotionsObserved := 0
	potentialsFired := 0

	orch.RegisterIntegrationCallback(func(e integration.IntegrationEvent) {
		if e.EventType == "promoted" {
			promotionsObserved++
			t.Logf("✅ Promoção observada! Cluster: %s", e.ClusterID)
		}
		if e.EventType == "potential_fired" {
			potentialsFired++
		}
	})

	// 4. Iniciar Parsing
	dataSource := &SimulatedClusterDataSource{}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	job, err := orch.StartParsingJob(ctx, dataSource)
	if err != nil {
		t.Fatalf("Erro ao iniciar parsing: %v", err)
	}

	t.Logf("Job de parsing iniciado: %s", job.JobID)

	// 5. Simular gradientes sendo computados simultaneamente
	go func() {
		for i := 0; i < 50; i++ {
			time.Sleep(100 * time.Millisecond)

			// Gradiente simulado
			grad := make([]float64, 10)
			for j := range grad {
				grad[j] = rand.Float64() * 5.0 // Força o gradiente para ser alto e disparar o potencial
			}

			gpuID := fmt.Sprintf("gpu_%d", rand.Intn(16))
			orch.OnGradientComputed(gpuID, grad)
		}
	}()

	// 6. Aguardar fim do teste
	<-ctx.Done()

	// 7. Verificar métricas
	metrics := orch.GetIntegrationMetrics()
	t.Logf("Métricas finais: %+v", metrics)

	if metrics.ParsingJobsCompleted == 0 {
		t.Errorf("Nenhum parsing completado")
	}

	if potentialsFired == 0 {
		t.Errorf("Nenhum potencial de ação disparado")
	}
}
