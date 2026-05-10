#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ArkheTemporalSubsystem.h"
#include "ArkheConsciousnessSubsystem.generated.h"

/**
 * ARKHE Consciousness System — NPC Mind Simulation
 *
 * Bridges the Continental Mind (250T parameter model) with UE actors.
 * Each NPC gets a "consciousness component" that:
 *   1. Receives perceptual input from SpatialHash
 *   2. Generates behavioral decisions via ML model
 *   3. Outputs actions as Behavior Tree tasks
 *   4. Records temporal state for replay
 *
 * Architecture:
 *   Perception → Consciousness Component → Wasm Inference → Behavior Tree
 */
UCLASS(BlueprintType, Blueprintable)
class ARKHEUNREAL_API UArkheConsciousnessSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UArkheConsciousnessSubsystem();

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /** Tick all active consciousness agents */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness")
    void TickConsciousness(float DeltaTime);

    /** Register a Pawn as a conscious agent */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness")
    void RegisterAgent(APawn* Agent, const FString& PersonalitySeed = TEXT(""));

    /** Remove an agent from simulation */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness")
    void UnregisterAgent(APawn* Agent);

    /** Get the consciousness component for a pawn */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness")
    class UArkheConsciousnessComponent* GetAgentComponent(APawn* Agent) const;

    /** Set ML inference mode */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness")
    void SetInferenceMode(EArkheInferenceMode Mode);

    /** Get memory usage */
    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Consciousness")
    int64 TotalMemoryBytes;

    /** Get number of active agents */
    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Consciousness")
    int32 ActiveAgentCount;

    /** Inference mode */
    UPROPERTY(BlueprintReadWrite, Category = "ARKHE|Consciousness")
    TEnumAsByte<EArkheInferenceMode> InferenceMode;

    // Enum for inference modes
    UENUM(BlueprintType)
    enum class EArkheInferenceMode : uint8
    {
        Cloud       UMETA(DisplayName = "Cloud (250T via Wasm)"),
        Local       UMETA(DisplayName = "Local ONNX Model"),
        Hybrid      UMETA(DisplayName = "Hybrid Cloud + Local"),
        Simulation   UMETA(DisplayName = "Rule-Based Simulation"),
    };

protected:
    // Map of registered agents
    TMap<TWeakObjectPtr<APawn>, TObjectPtr<UArkheConsciousnessComponent>> Agents;

    // Wasm runtime reference
    TObjectPtr<class UArkheWasmSubsystem> WasmRuntime;

    // Temporal subsystem reference
    TObjectPtr<class UArkheTemporalSubsystem> TemporalSystem;

    // Per-frame decision buffer
    TArray<uint8> InferenceBuffer;

    void RunInferenceBatch(float DeltaTime);
    void ProcessAgentPerception(class UArkheConsciousnessComponent* Component);
};