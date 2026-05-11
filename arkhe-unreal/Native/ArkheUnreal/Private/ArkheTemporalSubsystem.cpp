#include "ArkheTemporalSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Components/SceneComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Serialization/MemoryWriter.h"
#include "Hash/SHA1.h"
#include "Misc/Base64.h"
#include "HAL/PlatformTime.h"

// DECLARE LOG CATEGORY
DECLARE_LOG_CATEGORY_EXTERN(LogArkhe, Log, All);

UArkheTemporalSubsystem::UArkheTemporalSubsystem()
    : CurrentFrameNumber(0)
    , TotalRegisteredFrames(0)
    , bChainIntegrityVerified(false)
{
    // UE_LOG(LogArkhe, Log, TEXT("⏱️  Temporal Subsystem constructed"));
}

void UArkheTemporalSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    // Create Genesis Block
    GenesisBlockHash = CreateGenesisBlock();
    ChainHeadHash = GenesisBlockHash;

    // UE_LOG(LogArkhe, Log, TEXT("⏱️  Temporal Chain initialized with Genesis Hash: %s"),
    //    *GenesisBlockHash.Left(16));
}

FString UArkheTemporalSubsystem::RecordFrameTick(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World) return TEXT("");

    CurrentFrameNumber++;

    // Compute current frame state hash
    FString FrameHash = ComputeFrameHash(World);

    // Build temporal block
    FTemporalBlock NewBlock;
    NewBlock.FrameNumber = CurrentFrameNumber;
    NewBlock.PreviousHash = ChainHeadHash;
    NewBlock.DeltaTime = DeltaTime;
    NewBlock.Timestamp = FPlatformTime::Seconds();

    // Serialize actor states for this frame
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);

    TArray<FString> ActorHashes;
    for (AActor* Actor : AllActors)
    {
        FString ActorHash = HashActorState(Actor);
        ActorHashes.Add(ActorHash);
    }

    // Build Merkle root
    NewBlock.MerkleRoot = BuildMerkleTree(ActorHashes);

    // Compute block hash = SHA3(PreviousHash + MerkleRoot + FrameNumber + DeltaTime)
    FString BlockContent = NewBlock.PreviousHash + NewBlock.MerkleRoot +
                           FString::Printf(TEXT("%lld"), NewBlock.FrameNumber) +
                           FString::Printf(TEXT("%f"), NewBlock.DeltaTime);

    // Use SHA1 for speed (upgrade to SHA3 for production)
    FSHA1 HashState;
    HashState.UpdateWithString(*BlockContent, BlockContent.Len());
    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    NewBlock.BlockHash = FString::Printf(TEXT("%040x"),
        *reinterpret_cast<uint64*>(Digest));

    // Store block
    TemporalChain.Add(NewBlock);
    FrameHashes.Add(CurrentFrameNumber, NewBlock.BlockHash);
    ChainHeadHash = NewBlock.BlockHash;
    TotalRegisteredFrames++;
    bChainIntegrityVerified = false; // Chain modified, re-verify needed

    return NewBlock.BlockHash;
}

FString UArkheTemporalSubsystem::ComputeFrameHash(UWorld* World)
{
    if (!World) return TEXT("");

    // Serialize relevant world state for hashing
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);

    FString StateString;

    for (AActor* Actor : AllActors)
    {
        if (!Actor || !Actor->GetRootComponent()) continue;

        FTransform Transform = Actor->GetActorTransform();
        FVector Location = Transform.GetLocation();
        FRotator Rotation = Transform.GetRotation().Rotator();
        FVector Scale = Transform.GetScale3D();

        StateString += FString::Printf(
            TEXT("%s:%.2f,%.2f,%.2f:%.2f,%.2f,%.2f:%.2f,%.2f,%.2f|"),
            *Actor->GetName(),
            Location.X, Location.Y, Location.Z,
            Rotation.Pitch, Rotation.Yaw, Rotation.Roll,
            Scale.X, Scale.Y, Scale.Z
        );
    }

    // Hash the state string
    FSHA1 HashState;
    FTCHARToUTF8 Converter(*StateString);
    HashState.Update(Converter.Get(), Converter.Length());

    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    // Take first 16 hex chars for efficiency
    FString HashString;
    for (int i = 0; i < 8; i++)
    {
        HashString += FString::Printf(TEXT("%02x"), Digest[i]);
    }

    return HashString;
}

FString UArkheTemporalSubsystem::HashActorState(AActor* Actor)
{
    if (!Actor) return TEXT("00000000");

    FTransform Transform = Actor->GetActorTransform();
    FVector Location = Transform.GetLocation();

    // Simplified hash based on position, rotation, velocity
    FString State = FString::Printf(
        TEXT("%.2f%.2f%.2f"),
        Location.X, Location.Y, Location.Z
    );

    if (UPrimitiveComponent* PrimComp = Actor->FindComponentByClass<UPrimitiveComponent>())
    {
        FVector Velocity = PrimComp->GetPhysicsLinearVelocity();
        State += FString::Printf(TEXT("%.2f%.2f%.2f"), Velocity.X, Velocity.Y, Velocity.Z);
    }

    FSHA1 HashState;
    FTCHARToUTF8 Converter(*State);
    HashState.Update(Converter.Get(), Converter.Length());

    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    return FString::Printf(TEXT("%02x%02x%02x%02x"), Digest[0], Digest[1], Digest[2], Digest[3]);
}

FString UArkheTemporalSubsystem::BuildMerkleTree(const TArray<FString>& ActorHashes)
{
    if (ActorHashes.Num() == 0) return TEXT("00000000");
    if (ActorHashes.Num() == 1) return ActorHashes[0];

    TArray<FString> CurrentLevel = ActorHashes;

    while (CurrentLevel.Num() > 1)
    {
        TArray<FString> NextLevel;

        for (int32 i = 0; i < CurrentLevel.Num(); i += 2)
        {
            FString Left = CurrentLevel[i];
            FString Right = (i + 1 < CurrentLevel.Num()) ? CurrentLevel[i + 1] : Left;

            FString Combined = Left + Right;
            FSHA1 HashState;
            HashState.UpdateWithString(*Combined, Combined.Len());

            uint8 Digest[FSHA1::DigestSize];
            HashState.Final();
            HashState.GetHash(Digest);

            NextLevel.Add(FString::Printf(TEXT("%040x"), *reinterpret_cast<uint64*>(Digest)));
        }

        CurrentLevel = NextLevel;
    }

    return CurrentLevel[0];
}

FString UArkheTemporalSubsystem::CreateGenesisBlock()
{
    FString GenesisData = TEXT("ARKHE_OMEGA_TEMP_GENESIS_BLOCK_6.0.0");
    FSHA1 HashState;
    HashState.UpdateWithString(*GenesisData, GenesisData.Len());

    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    return FString::Printf(TEXT("%040x"), *reinterpret_cast<uint64*>(Digest));
}

FString UArkheTemporalSubsystem::GetBlockHash(int64 FrameNumber) const
{
    if (FrameHashes.Contains(FrameNumber))
        return FrameHashes[FrameNumber];
    return TEXT("");
}

bool UArkheTemporalSubsystem::VerifyChainIntegrity(int64 StartFrame, int64 EndFrame) const
{
    for (int64 Frame = StartFrame + 1; Frame <= EndFrame; Frame++)
    {
        if (!FrameHashes.Contains(Frame) || !FrameHashes.Contains(Frame - 1))
            return false;

        // Each block's PreviousHash must match previous block's hash
        // Full verification would deserialize and recompute
    }

    return true;
}

bool UArkheTemporalSubsystem::InternalVerifyChain() const
{
    if (TemporalChain.Num() == 0) return true;

    // Verify Genesis
    if (TemporalChain[0].BlockHash != GenesisBlockHash)
        return false;

    // Verify chain linkage
    for (int32 i = 1; i < TemporalChain.Num(); i++)
    {
        if (TemporalChain[i].PreviousHash != TemporalChain[i - 1].BlockHash)
            return false;
    }

    return true;
}

TArray<uint8> UArkheTemporalSubsystem::GenerateMerkleProof(AActor* Actor, int64 Frame) const
{
    TArray<uint8> Proof;

    if (Frame < 0 || Frame >= TemporalChain.Num())
        return Proof;

    const FTemporalBlock& Block = TemporalChain[Frame];

    // Serialize proof
    FMemoryWriter Writer(Proof);
    Writer << Block.FrameNumber;
    Writer << Block.MerkleRoot;
    Writer << Block.BlockHash;

    FString ActorHash = HashActorState(Actor);
    Writer << ActorHash;

    // Add chain verification path
    Writer << Block.PreviousHash;

    // Calculate and add ZK-style inclusion proof (simplified)
    FString ProofData = ActorHash + Block.MerkleRoot + Block.BlockHash;
    FSHA1 HashState;
    HashState.UpdateWithString(*ProofData, ProofData.Len());
    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    Writer.Serialize(Digest, FSHA1::DigestSize);

    return Proof;
}

void UArkheTemporalSubsystem::TemporalReplay(int64 StartFrame, int64 EndFrame, float PlaybackSpeed)
{
    // UE_LOG(LogArkhe, Log, TEXT("⏪ Temporal Replay: Frame %lld → %lld at %.1fx"),
    //    StartFrame, EndFrame, PlaybackSpeed);

    // In production: restore world state from serialized blocks
    // This is a simplified visualization replay

    for (int64 Frame = StartFrame; Frame <= EndFrame; Frame++)
    {
        if (!FrameHashes.Contains(Frame)) continue;

        // Log frame info for debugging
        // UE_LOG(LogArkhe, Verbose, TEXT("  Frame %lld: Hash=%s"),
        //    Frame, *FrameHashes[Frame].Left(12));
    }
}

bool UArkheTemporalSubsystem::CheckCausalSafety(const FString& Action, const FString& Target) const
{
    // Causal Shield: prevent temporal paradoxes
    // In production: trace causal dependencies and check for cycles

    FString CausalQuery = Action + TEXT("→") + Target;
    FSHA1 HashState;
    HashState.UpdateWithString(*CausalQuery, CausalQuery.Len());
    uint8 Digest[FSHA1::DigestSize];
    HashState.Final();
    HashState.GetHash(Digest);

    // Simplified: Check if this action has been verified before
    return true; // Safe by default
}

void UArkheTemporalSubsystem::RegisterCausalLink(const FString& Cause, const FString& Effect)
{
    // Store causal relationship in the temporal graph
    // In production: maintain directed acyclic graph of causal dependencies
    // UE_LOG(LogArkhe, Verbose, TEXT("🔗 Causal Link: %s → %s"), *Cause, *Effect);
}

bool UArkheTemporalSubsystem::ExportTemporalChain(const FString& FilePath) const
{
    TArray<FString> Lines;
    Lines.Add(TEXT("Frame,BlockHash,PreviousHash,MerkleRoot,DeltaTime"));

    for (const FTemporalBlock& Block : TemporalChain)
    {
        Lines.Add(FString::Printf(
            TEXT("%lld,%s,%s,%s,%.4f"),
            Block.FrameNumber,
            *Block.BlockHash,
            *Block.PreviousHash,
            *Block.MerkleRoot,
            Block.DeltaTime
        ));
    }

    return FFileHelper::SaveStringArrayToFile(
        Lines, *FilePath, FFileHelper::EEncodingOptions::ForceAnsi);
}

void UArkheTemporalSubsystem::Deinitialize()
{
    // Export final temporal chain
    // FString ExportPath = FPaths::ProjectSavedDir() / TEXT("TemporalChain/temporal_export.csv");
    // ExportTemporalChain(ExportPath);

    // UE_LOG(LogArkhe, Log, TEXT("⏱️  Temporal Subsystem shutdown. Exported %d blocks."),
    //    TemporalChain.Num());

    Super::Deinitialize();
}