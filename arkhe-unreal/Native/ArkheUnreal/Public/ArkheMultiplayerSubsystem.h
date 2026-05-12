#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ArkheMultiplayerSubsystem.generated.h"

/**
 * ARKHE Multiplayer — Temporal State Synchronization
 *
 * Synchronizes game state across clients using temporal chain blocks.
 * Each tick generates a temporal block that can be verified by all clients.
 * Server acts as Temporal Authority, clients verify Merkle proofs.
 *
 * Protocol:
 *   Server → Clients: Frame number + Merkle root + Authoritative state hash
 *   Client → Server: Verification proof + inputs
 *
 * Deterministic lockstep with optional probabilistic rollback.
 */
UCLASS(BlueprintType, Blueprintable)
class ARKHEUNREAL_API UArkheMultiplayerSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UArkheMultiplayerSubsystem();

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /** Synchronize temporal state to clients */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Multiplayer")
    void SyncTemporalState(int64 Frame, const FString& MerkleRoot);

    /** Request temporal verification from server */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Multiplayer",
        meta = (DisplayName = "Verify Server State"))
    bool VerifyServerState(int64 Frame, const TArray<uint8>& Proof);

    /** Get network latency estimate */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Multiplayer")
    float GetNetworkLatency() const;

    /** Set server address */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Multiplayer")
    void SetServerAddress(const FString& Address, int32 Port);

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Multiplayer")
    bool bIsConnected;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Multiplayer")
    int32 ConnectedClients;

    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Multiplayer")
    float AverageLatencyMs;

protected:
    FString ServerAddress;
    int32 ServerPort;

    // Temporal state cache
    TMap<int64, FString> CachedStates;
};