package main

import (
	"context"
	"flag"
	"fmt"
	"math"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/arkhe-os/arkhe-go/pkg/interlink"
	"github.com/arkhe-os/arkhe-go/pkg/oracle"
	"github.com/arkhe-os/arkhe-go/pkg/temporal"
	"github.com/spf13/viper"
	"go.uber.org/zap"
	"golang.org/x/sync/errgroup"
)

func main() {
	// Flags
	configPath := flag.String("config", "config.yaml", "Path to config file")
	nodeID := flag.String("node-id", "ARKHE-NODE-01", "Node identifier")
	position := flag.String("position", "0,0,0", "Position in AU (x,y,z)")
	flag.Parse()

	// Logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	// Config
	viper.SetConfigFile(*configPath)
	if err := viper.ReadInConfig(); err != nil {
		logger.Warn("Failed to read config, using defaults", zap.Error(err))
	}

	// Parse position
	var posAU [3]float64
	fmt.Sscanf(*position, "%f,%f,%f", &posAU[0], &posAU[1], &posAU[2])

	// Initialize components
	oracleInst := oracle.NewHeytingOracle(logger,
		oracle.WithGalacticCoherence(true),
		oracle.WithObserverDistance(math.Sqrt(posAU[0]*posAU[0]+posAU[1]*posAU[1]+posAU[2]*posAU[2])),
	)

	laserConfig := interlink.DefaultConfig()
	if viper.IsSet("interlink.modulation") {
		laserConfig.Modulation = viper.GetString("interlink.modulation")
	}

	engine := interlink.NewLaserEngine(*nodeID, laserConfig, posAU, logger)

	// Register peers from config
	for peerID, peerCfg := range viper.GetStringMap("peers") {
		// Parse peer config and register
		// (simplificado para demonstração)
		_ = peerID
		_ = peerCfg
	}

	// Context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Goroutines
	var g errgroup.Group

	// Goroutine 1: Process incoming messages
	g.Go(func() error {
		return processIncoming(ctx, engine, oracleInst, logger)
	})

	// Goroutine 2: Periodic link health checks
	g.Go(func() error {
		ticker := time.NewTicker(60 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return nil
			case <-ticker.C:
				checkLinkHealth(engine, logger)
			}
		}
	})

	// Goroutine 3: Handle OS signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	g.Go(func() error {
		<-sigChan
		logger.Info("Shutdown signal received")
		cancel()
		return nil
	})

	// Start
	logger.Info("ARKHE Node starting",
		zap.String("node_id", *nodeID),
		zap.Float64s("position_au", posAU[:]),
		zap.Float64("quantum_window", oracleInst.QuantumWindowScaled()),
	)

	if err := g.Wait(); err != nil {
		logger.Error("Node exited with error", zap.Error(err))
		os.Exit(1)
	}

	logger.Info("ARKHE Node stopped gracefully")
}

func processIncoming(ctx context.Context, engine *interlink.LaserEngine, oracleInst *oracle.HeytingOracle, logger *zap.Logger) error {
	// Em produção: ler de socket/UDP real
	// Aqui: simular recebimento periódico
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil
		case <-ticker.C:
			// Simular recebimento de mensagem
			msg, err := temporal.NewMessage(
				map[string]string{"test": "heartbeat"},
				fmt.Sprintf("SENDER-%d", engine.Stats().FramesSent),
				"SELF",
			)
			if err != nil {
				logger.Error("Failed to create test message", zap.Error(err))
				continue
			}

			// Avaliar consistência
			report := oracleInst.Evaluate(msg)
			if report.Consistent {
				logger.Debug("Message consistent",
					zap.Float64("score", report.Score),
					zap.Bool("quantum", report.QuantumCoherent),
					zap.Bool("solar", report.SolarCoherent),
					zap.Bool("galactic", report.GalacticCoherent),
				)
			} else {
				logger.Warn("Message inconsistent",
					zap.Float64("score", report.Score),
					zap.Strings("violations", report.Violations),
				)
			}
		}
	}
}

func checkLinkHealth(engine *interlink.LaserEngine, logger *zap.Logger) {
	stats := engine.Stats()
	logger.Info("Link health check",
		zap.Uint64("frames_sent", stats.FramesSent),
		zap.Uint64("frames_received", stats.FramesReceived),
		zap.Float64("avg_snr_db", stats.AvgSNRdB),
		zap.Uint64("link_failures", stats.LinkFailures),
	)
}
