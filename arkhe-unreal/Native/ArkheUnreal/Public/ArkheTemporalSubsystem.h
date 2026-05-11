#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Engine/World.h"
#include "Misc/SecureHash.h"
#include "Serialization/BufferArchive.h"
#include "ArkheTemporalSubsystem.generated.h"

/**
 * ARKHE Temporal Hash Chain — Per-Frame Block Registration
 *
 * Every frame (tick) is registered as a block in the temporal chain.
 * Each block contains:
 *   - Frame hash (Merkle root of all actor states)
 *   - Previous block hash (chain linkage)
 *   - Physics state snapshot
 *   - Metadata (timestamp, frame number, delta time)
 *
 * This enables:
 *   - Temporal replay with cryptographic integrity
 *   - Causal debugging (trace any state to origin)
 *   - Multiplayer deterministic lockstep verification
 *   - Provenance: who changed what, when
 */
UCLASS(BlueprintType, Blueprintable)
class ARKHEUNREAL_API UArkheTemporalSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UArkheTemporalSubsystem();

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // === Temporal Chain Operations ===

    /** Record current frame state as a temporal block */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    FString RecordFrameTick(float DeltaTime);

    /** Get hash of a specific frame */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    FString GetBlockHash(int64 FrameNumber) const;

    /** Verify integrity of the chain from frame A to B */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    bool VerifyChainIntegrity(int64 StartFrame, int64 EndFrame) const;

    /** Generate Merkle proof for a specific actor in a frame */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    TArray<uint8> GenerateMerkleProof(AActor* Actor, int64 Frame) const;

    /** Replay temporal chain to reconstruct world state */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    void TemporalReplay(int64 StartFrame, int64 EndFrame, float PlaybackSpeed = 1.0f);

    /** Export temporal chain to file */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    bool ExportTemporalChain(const FString& FilePath) const;

    // === Causal Shield ===

    /** Check if an action would create a temporal paradox */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    bool CheckCausalSafety(const FString& Action, const FString& Target) const;

    /** Register a causal dependency between events */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal")
    void RegisterCausalLink(const FString& Cause, const FString& Effect);

    // === Properties ===

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    int64 CurrentFrameNumber;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    FString ChainHeadHash;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    int32 TotalRegisteredFrames;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    bool bChainIntegrityVerified;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    TMap<int64, FString> FrameHashes; // Frame number → block hash

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Temporal")
    FString GenesisBlockHash;

protected:
    // Internal temporal block structure
    struct FTemporalBlock
    {
        int64 FrameNumber;
        FString BlockHash;
        FString PreviousHash;
        FString MerkleRoot;
        TArray<uint8> FrameSnapshot;
        double Timestamp;
        float DeltaTime;
        TArray<uint8> IntegrityProof;
    };

    TArray<FTemporalBlock> TemporalChain;

    // Compute frame hash from all actor states
    FString ComputeFrameHash(UWorld* World);

    // Build Merkle tree from actor states
    FString BuildMerkleTree(const TArray<FString>& ActorHashes);

    // Hash an individual actor state
    FString HashActorState(AActor* Actor);

    // Genesis block creation
    FString CreateGenesisBlock();

    // Internal consistency oracle
    bool InternalVerifyChain() const;
};