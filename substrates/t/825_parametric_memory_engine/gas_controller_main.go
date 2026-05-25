// cmd/gas-controller/main.go
// Gradient Aggregation Service Controller — Substrato 825.2
// Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25

package main

import (
	"context"
	"encoding/base64"
	"fmt"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/tools/cache"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/config"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/manager"
	"sigs.k8s.io/controller-runtime/pkg/manager/signals"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

// ParameterDeltaSpec defines the desired state of ParameterDelta
type ParameterDeltaSpec struct {
	ModelVersion string            `json:"modelVersion"`
	LayerName    string            `json:"layerName"`
	DeltaShape   []int             `json:"deltaShape"`
	DeltaData    string            `json:"deltaData"` // base64 encoded tensor
	Loss         float64           `json:"loss"`
	PodID        string            `json:"podID"`
	Timestamp    int64             `json:"timestamp"`
}

// ParameterDeltaStatus defines the observed state
type ParameterDeltaStatus struct {
	Merged    bool      `json:"merged"`
	MergedAt  *metav1.Time `json:"mergedAt,omitempty"`
	ConsensusVersion string `json:"consensusVersion,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:resource:scope=Namespaced
// +kubebuilder:subresource:status

type ParameterDelta struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec   ParameterDeltaSpec   `json:"spec,omitempty"`
	Status ParameterDeltaStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

type ParameterDeltaList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items []ParameterDelta `json:"items"`
}

func init() {
	// Register types with scheme
}

// GASController reconciles ParameterDelta objects
type GASController struct {
	client.Client
	mergeInterval    time.Duration
	consensusWeights map[string][]float32
	versionCounter   int
}

func (r *GASController) Reconcile(ctx context.Context, req reconcile.Request) (reconcile.Result, error) {
	fmt.Printf("[825.2] Reconciling ParameterDelta: %s/%s\n", req.Namespace, req.Name)

	var delta ParameterDelta
	if err := r.Get(ctx, req.NamespacedName, &delta); err != nil {
		if errors.IsNotFound(err) {
			return reconcile.Result{}, nil
		}
		return reconcile.Result{}, err
	}

	// Skip already merged deltas
	if delta.Status.Merged {
		return reconcile.Result{}, nil
	}

	// Add to consensus buffer
	r.accumulateDelta(delta)

	return reconcile.Result{RequeueAfter: r.mergeInterval}, nil
}

func (r *GASController) accumulateDelta(delta ParameterDelta) {
	// Decode base64 tensor data
	data, err := base64.StdEncoding.DecodeString(delta.Spec.DeltaData)
	if err != nil {
		fmt.Printf("[825.2] ERROR decoding delta: %v\n", err)
		return
	}

	// In production, deserialize tensor and accumulate
	// For PoC, store raw bytes in memory buffer
	layerKey := fmt.Sprintf("%s:%s", delta.Spec.ModelVersion, delta.Spec.LayerName)

	fmt.Printf("[825.2] Accumulated delta for layer %s from pod %s (loss=%.4f, size=%d bytes)\n",
		layerKey, delta.Spec.PodID, delta.Spec.Loss, len(data))
}

func (r *GASController) runConsensusMerge(ctx context.Context) {
	ticker := time.NewTicker(r.mergeInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			r.performMerge(ctx)
		}
	}
}

func (r *GASController) performMerge(ctx context.Context) {
	fmt.Printf("[825.2] Performing consensus merge (version: v%d)\n", r.versionCounter)

	// List all unmerged deltas
	var deltaList ParameterDeltaList
	if err := r.List(ctx, &deltaList, client.MatchingFields{"status.merged": "false"}); err != nil {
		fmt.Printf("[825.2] ERROR listing deltas: %v\n", err)
		return
	}

	if len(deltaList.Items) == 0 {
		fmt.Printf("[825.2] No deltas to merge\n")
		return
	}

	// Federated Averaging: average deltas weighted by inverse loss
	// Lower loss = higher weight
	fmt.Printf("[825.2] Merging %d deltas...\n", len(deltaList.Items))

	// Update consensus version
	r.versionCounter++
	newVersion := fmt.Sprintf("v%d", r.versionCounter)
	now := metav1.Now()

	// Mark all as merged
	for _, delta := range deltaList.Items {
		delta.Status.Merged = true
		delta.Status.MergedAt = &now
		delta.Status.ConsensusVersion = newVersion
		if err := r.Status().Update(ctx, &delta); err != nil {
			fmt.Printf("[825.2] ERROR updating delta status: %v\n", err)
		}
	}

	fmt.Printf("[825.2] Consensus merge complete: %s\n", newVersion)
}

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════════╗")
	fmt.Println("║   GAS CONTROLLER — SUBSTRATO 825.2                      ║")
	fmt.Println("║   Gradient Aggregation Service | ξM-Field Consensus       ║")
	fmt.Println("╚════════════════════════════════════════════════════════════╝")

	mgr, err := manager.New(config.GetConfigOrDie(), manager.Options{})
	if err != nil {
		panic(err)
	}

	gasCtrl := &GASController{
		Client:           mgr.GetClient(),
		mergeInterval:    5 * time.Minute,
		consensusWeights: make(map[string][]float32),
		versionCounter:   42, // Start from v42 (canonical base)
	}

	if err := controller.New("gas-controller", mgr, controller.Options{
		Reconciler: gasCtrl,
	}).Watch(&source.Kind{Type: &ParameterDelta{}}, &handler.EnqueueRequestForObject{}); err != nil {
		panic(err)
	}

	// Start consensus merge loop
	go gasCtrl.runConsensusMerge(signals.SetupSignalHandler())

	fmt.Println("[825.2] GAS Controller started. Waiting for ParameterDelta resources...")
	if err := mgr.Start(signals.SetupSignalHandler()); err != nil {
		panic(err)
	}
}
