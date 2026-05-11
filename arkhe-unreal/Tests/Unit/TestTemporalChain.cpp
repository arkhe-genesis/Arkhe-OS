#include "Misc/AutomationTest.h"
#include "ArkheTemporalSubsystem.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FTestTemporalGenesis,
    "ARKHE.Temporal.GenesisBlock",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FTestTemporalGenesis::RunTest(const FString& Parameters)
{
    UArkheTemporalSubsystem* Subsystem =
        FModuleManager::Get().LoadModuleChecked<FArkheUnrealModule>("ArkheUnreal")
            .GetTemporalSystem();

    TestNotNull("TemporalSystem exists", Subsystem);
    TestTrue("Genesis hash is not empty", !Subsystem->GenesisBlockHash.IsEmpty());
    TestEqual("Initial frame count", Subsystem->TotalRegisteredFrames, (int64)0);

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FTestTemporalRecord,
    "ARKHE.Temporal.RecordAndVerify",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FTestTemporalRecord::RunTest(const FString& Parameters)
{
    UArkheTemporalSubsystem* Subsystem = FModuleManager::Get().LoadModuleChecked<FArkheUnrealModule>("ArkheUnreal").GetTemporalSystem();

    // Record first frame
    FString Hash1 = Subsystem->RecordFrameTick(0.016f); // 60fps
    TestTrue("Hash1 is not empty", !Hash1.IsEmpty());
    TestEqual("Frame count after 1 record", Subsystem->TotalRegisteredFrames, (int64)1);

    // Record second frame
    FString Hash2 = Subsystem->RecordFrameTick(0.016f);
    TestTrue("Hash2 is not empty", !Hash2.IsEmpty());
    TestTrue("Hashes are different", Hash1 != Hash2);

    // Verify chain
    bool bValid = Subsystem->VerifyChainIntegrity(0, 1);
    TestTrue("Chain integrity valid", bValid);

    return true;
}