#include "ArkheUnreal.h"
#include "Modules/ModuleManager.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFilemanager.h"
#include "Interfaces/IPluginManager.h"

#include "ArkheTemporalSubsystem.h"
#include "ArkheSpatialSubsystem.h"
#include "ArkheWasmSubsystem.h"
#include "ArkheConsciousnessSubsystem.h"

#define LOCTEXT_NAMESPACE "FArkheUnrealModule"

// DEFINE LOG CATEGORY
DEFINE_LOG_CATEGORY_STATIC(LogArkhe, Log, All);

IMPLEMENT_GAME_MODULE(FArkheUnrealModule, ArkheUnreal);

FArkheUnrealModule& FArkheUnrealModule::Get()
{
    return FModuleManager::LoadModuleChecked<FArkheUnrealModule>("ArkheUnreal");
}

void FArkheUnrealModule::StartupModule()
{
    UE_LOG(LogArkhe, Log, TEXT("ARKHE Ω-TEMP v6.0.0 — Initializing Unreal Integration"));

    // Register tick
    TickHandle = FWorldDelegates::OnWorldPostActorTick.AddRaw(
       this, &FArkheUnrealModule::OnWorldTickStart);

    // Initialize systems
    InitializeTemporalSystem();
    InitializeSpatialSystem();
    InitializeWasmRuntime();
    InitializeConsciousnessSystem();

    // Register custom asset types and menu commands
    // RegisterMenus();
    // RegisterAssetTypes();

    UE_LOG(LogArkhe, Log, TEXT("✅ ARKHE Unreal Integration Ready"));
}

void FArkheUnrealModule::ShutdownModule()
{
    FWorldDelegates::OnWorldPostActorTick.Remove(TickHandle);

    // Shutdown in reverse order
    ConsciousnessEngine = nullptr;
    WasmRuntime = nullptr;
    SpatialSystem = nullptr;
    TemporalSystem = nullptr;

    UE_LOG(LogArkhe, Log, TEXT("ARKHE Unreal Integration Shutdown"));
}

void FArkheUnrealModule::InitializeTemporalSystem()
{
    TemporalSystem = NewObject<UArkheTemporalSubsystem>();
    // TemporalSystem->Initialize();

    UE_LOG(LogArkhe, Log, TEXT("⏱️  Temporal Chain initialized"));
}

void FArkheUnrealModule::InitializeSpatialSystem()
{
    SpatialSystem = NewObject<UArkheSpatialSubsystem>();
    SpatialSystem->Initialize(1024.0f); // 1km world bounds

    UE_LOG(LogArkhe, Log, TEXT("🌐 Spatial Hash initialized"));
}

void FArkheUnrealModule::InitializeWasmRuntime()
{
    WasmRuntime = NewObject<UArkheWasmSubsystem>();
    // WasmRuntime->Initialize();

    // Load default Wasm plugins
    // FString PluginDir = FPaths::Combine(
    //    IPluginManager::Get().FindPlugin("ArkheUnreal")->GetBaseDir(),
    //    TEXT("Plugins/WasmModules"));

    // WasmRuntime->LoadAllFromDirectory(PluginDir);

    UE_LOG(LogArkhe, Log, TEXT("🔧 Wasm Runtime initialized with %d plugins"),
        WasmRuntime->LoadedModuleCount);
}

void FArkheUnrealModule::InitializeConsciousnessSystem()
{
    ConsciousnessEngine = NewObject<UArkheConsciousnessSubsystem>();
    // ConsciousnessEngine->Initialize();

    UE_LOG(LogArkhe, Log, TEXT("🧠 Consciousness Engine initialized"));
}

void FArkheUnrealModule::OnWorldTickStart(ELevelTick TickType, float DeltaTime)
{
    if (!GWorld || TickType != ELevelTick::LEVELTICK_All)
       return;

    // 1. Temporal Chain — registrar bloco por frame
    if (TemporalSystem)
    {
        TemporalSystem->RecordFrameTick(DeltaTime);
    }

    // 2. Spatial System — atualizar hashes espaciais
    if (SpatialSystem)
    {
        SpatialSystem->UpdateSpatialQueries(DeltaTime);
    }

    // 3. Consciousness — simular mentes NPC
    if (ConsciousnessEngine)
    {
        ConsciousnessEngine->TickConsciousness(DeltaTime);
    }

    // 4. Wasm modules — executar módulos registrados
    if (WasmRuntime)
    {
        WasmRuntime->TickAll(DeltaTime);
    }
}

bool FArkheUnrealModule::LoadWasmModule(const FString& ModulePath, const FString& ModuleName)
{
    if (!WasmRuntime)
        return false;
    return WasmRuntime->LoadModule(ModulePath, ModuleName);
}

TArray<uint8> FArkheUnrealModule::ExecuteWasmFunction(
    const FString& ModuleName, const FString& FunctionName,
    const TArray<uint8>& Input)
{
    if (!WasmRuntime)
        return TArray<uint8>();
    return WasmRuntime->CallFunction(ModuleName, FunctionName, Input);
}

#undef LOCTEXT_NAMESPACE