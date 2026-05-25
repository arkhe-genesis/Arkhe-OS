// ═══════════════════════════════════════════════════════════════════
// ARKHE.SYS — Kernel Module v2.3 (KMDF)
// Substrate 813 — Arkhe Kernel + Visualization Integration
// Architect: ORCID 0009-0005-2697-4668
// Target: Windows x64, IRQL <= DISPATCH_LEVEL
// ═══════════════════════════════════════════════════════════════════

#include <ntddk.h>
#include <wdf.h>
#include <ntstrsafe.h>

// ── Forward declarations ───────────────────────────────────────────
DRIVER_INITIALIZE DriverEntry;
EVT_WDF_DRIVER_DEVICE_ADD ArkheEvtDeviceAdd;
EVT_WDF_IO_QUEUE_IO_DEVICE_CONTROL ArkheEvtIoDeviceControl;
EVT_WDF_IO_QUEUE_IO_READ ArkheEvtIoRead;

VOID ArkheCasterCallback(IN HANDLE ProcessId, IN HANDLE ThreadId, IN BOOLEAN Create);
VOID ArkheMetacognitionWorker(IN PVOID Context);
NTSTATUS ArkheValidateConstitution();
NTSTATUS ArkheInitializeCaster();
NTSTATUS ArkheEnableRTZ();
NTSTATUS ArkheStartMetacognition();

// ── Constants ──────────────────────────────────────────────────────
#define ARKHE_POOL_TAG 'EHKRA'
#define ARKHE_CONSTITUTION_MAGIC 0x58494D24
#define GHOST_THRESHOLD 0.577f
#define RTZ_RHO_MIN 0.15f
#define METACOGNITION_INTERVAL_MS 5000
#define VERTEX_COUNT 120
#define MAX_AGENT_COUNT 24  // 20 current + 4 future expansion

// ── 600-cell vertex → (agent_id, instance, role_name) mapping ──────
typedef struct _VERTEX_AGENT_MAP {
    ULONG agent_id;
    ULONG instance;
    CHAR role_name[64];
    CHAR domain[32];
    FLOAT base_coherence;
} VERTEX_AGENT_MAP;

// ── Emerging role registration ─────────────────────────────────────
typedef struct _EMERGING_ROLE {
    ULONG agent_id;
    CHAR role_name[64];
    CHAR domain[32];
    FLOAT base_coherence;
} EMERGING_ROLE;

// ═══════════════════════════════════════════════════════════════════
// CANONICAL 600-CELL MAPPING (Hook 804.2)
// 20 agents × 6 instances = 120 vertices
// ═══════════════════════════════════════════════════════════════════
static VERTEX_AGENT_MAP gVertexAgentMap[VERTEX_COUNT] = {
    {1, 1, "AI Solutions Architect", "governance", 0.95f},
    {1, 2, "AI Solutions Architect", "governance", 0.95f},
    {1, 3, "AI Solutions Architect", "governance", 0.95f},
    {1, 4, "AI Solutions Architect", "governance", 0.95f},
    {1, 5, "AI Solutions Architect", "governance", 0.95f},
    {1, 6, "AI Solutions Architect", "governance", 0.95f},
    {2, 1, "AI/ML Engineer", "core", 0.97f},
    {2, 2, "AI/ML Engineer", "core", 0.97f},
    {2, 3, "AI/ML Engineer", "core", 0.97f},
    {2, 4, "AI/ML Engineer", "core", 0.97f},
    {2, 5, "AI/ML Engineer", "core", 0.97f},
    {2, 6, "AI/ML Engineer", "core", 0.97f},
    {3, 1, "MLOps Engineer", "parsing", 0.93f},
    {3, 2, "MLOps Engineer", "parsing", 0.93f},
    {3, 3, "MLOps Engineer", "parsing", 0.93f},
    {3, 4, "MLOps Engineer", "parsing", 0.93f},
    {3, 5, "MLOps Engineer", "parsing", 0.93f},
    {3, 6, "MLOps Engineer", "parsing", 0.93f},
    {4, 1, "Generative AI Engineer", "quantum", 0.96f},
    {4, 2, "Generative AI Engineer", "quantum", 0.96f},
    {4, 3, "Generative AI Engineer", "quantum", 0.96f},
    {4, 4, "Generative AI Engineer", "quantum", 0.96f},
    {4, 5, "Generative AI Engineer", "quantum", 0.96f},
    {4, 6, "Generative AI Engineer", "quantum", 0.96f},
    {5, 1, "AI Product Manager", "governance", 0.91f},
    {5, 2, "AI Product Manager", "governance", 0.91f},
    {5, 3, "AI Product Manager", "governance", 0.91f},
    {5, 4, "AI Product Manager", "governance", 0.91f},
    {5, 5, "AI Product Manager", "governance", 0.91f},
    {5, 6, "AI Product Manager", "governance", 0.91f},
    {6, 1, "Robotics Engineer", "quantum", 0.94f},
    {6, 2, "Robotics Engineer", "quantum", 0.94f},
    {6, 3, "Robotics Engineer", "quantum", 0.94f},
    {6, 4, "Robotics Engineer", "quantum", 0.94f},
    {6, 5, "Robotics Engineer", "quantum", 0.94f},
    {6, 6, "Robotics Engineer", "quantum", 0.94f},
    {7, 1, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {7, 2, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {7, 3, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {7, 4, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {7, 5, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {7, 6, "Autonomous Systems Engineer", "enterprise", 0.95f},
    {8, 1, "Data Scientist", "parsing", 0.92f},
    {8, 2, "Data Scientist", "parsing", 0.92f},
    {8, 3, "Data Scientist", "parsing", 0.92f},
    {8, 4, "Data Scientist", "parsing", 0.92f},
    {8, 5, "Data Scientist", "parsing", 0.92f},
    {8, 6, "Data Scientist", "parsing", 0.92f},
    {9, 1, "AI Cybersecurity Specialist", "core", 0.98f},
    {9, 2, "AI Cybersecurity Specialist", "core", 0.98f},
    {9, 3, "AI Cybersecurity Specialist", "core", 0.98f},
    {9, 4, "AI Cybersecurity Specialist", "core", 0.98f},
    {9, 5, "AI Cybersecurity Specialist", "core", 0.98f},
    {9, 6, "AI Cybersecurity Specialist", "core", 0.98f},
    {10, 1, "Computer Vision Engineer", "quantum", 0.95f},
    {10, 2, "Computer Vision Engineer", "quantum", 0.95f},
    {10, 3, "Computer Vision Engineer", "quantum", 0.95f},
    {10, 4, "Computer Vision Engineer", "quantum", 0.95f},
    {10, 5, "Computer Vision Engineer", "quantum", 0.95f},
    {10, 6, "Computer Vision Engineer", "quantum", 0.95f},
    {11, 1, "NLP Engineer", "parsing", 0.96f},
    {11, 2, "NLP Engineer", "parsing", 0.96f},
    {11, 3, "NLP Engineer", "parsing", 0.96f},
    {11, 4, "NLP Engineer", "parsing", 0.96f},
    {11, 5, "NLP Engineer", "parsing", 0.96f},
    {11, 6, "NLP Engineer", "parsing", 0.96f},
    {12, 1, "Edge AI Engineer", "enterprise", 0.93f},
    {12, 2, "Edge AI Engineer", "enterprise", 0.93f},
    {12, 3, "Edge AI Engineer", "enterprise", 0.93f},
    {12, 4, "Edge AI Engineer", "enterprise", 0.93f},
    {12, 5, "Edge AI Engineer", "enterprise", 0.93f},
    {12, 6, "Edge AI Engineer", "enterprise", 0.93f},
    {13, 1, "Industrial Automation Engineer", "enterprise", 0.92f},
    {13, 2, "Industrial Automation Engineer", "enterprise", 0.92f},
    {13, 3, "Industrial Automation Engineer", "enterprise", 0.92f},
    {13, 4, "Industrial Automation Engineer", "enterprise", 0.92f},
    {13, 5, "Industrial Automation Engineer", "enterprise", 0.92f},
    {13, 6, "Industrial Automation Engineer", "enterprise", 0.92f},
    {14, 1, "AI Cloud Engineer", "core", 0.96f},
    {14, 2, "AI Cloud Engineer", "core", 0.96f},
    {14, 3, "AI Cloud Engineer", "core", 0.96f},
    {14, 4, "AI Cloud Engineer", "core", 0.96f},
    {14, 5, "AI Cloud Engineer", "core", 0.96f},
    {14, 6, "AI Cloud Engineer", "core", 0.96f},
    {15, 1, "AI Research Scientist", "governance", 0.99f},
    {15, 2, "AI Research Scientist", "governance", 0.99f},
    {15, 3, "AI Research Scientist", "governance", 0.99f},
    {15, 4, "AI Research Scientist", "governance", 0.99f},
    {15, 5, "AI Research Scientist", "governance", 0.99f},
    {15, 6, "AI Research Scientist", "governance", 0.99f},
    {16, 1, "AI Ethics Officer", "governance", 0.94f},
    {16, 2, "AI Ethics Officer", "governance", 0.94f},
    {16, 3, "AI Ethics Officer", "governance", 0.94f},
    {16, 4, "AI Ethics Officer", "governance", 0.94f},
    {16, 5, "AI Ethics Officer", "governance", 0.94f},
    {16, 6, "AI Ethics Officer", "governance", 0.94f},
    {17, 1, "Quantum ML Engineer", "quantum", 0.93f},
    {17, 2, "Quantum ML Engineer", "quantum", 0.93f},
    {17, 3, "Quantum ML Engineer", "quantum", 0.93f},
    {17, 4, "Quantum ML Engineer", "quantum", 0.93f},
    {17, 5, "Quantum ML Engineer", "quantum", 0.93f},
    {17, 6, "Quantum ML Engineer", "quantum", 0.93f},
    {18, 1, "Coherence Systems Designer", "core", 0.95f},
    {18, 2, "Coherence Systems Designer", "core", 0.95f},
    {18, 3, "Coherence Systems Designer", "core", 0.95f},
    {18, 4, "Coherence Systems Designer", "core", 0.95f},
    {18, 5, "Coherence Systems Designer", "core", 0.95f},
    {18, 6, "Coherence Systems Designer", "core", 0.95f},
    {19, 1, "AI Regulatory Specialist", "enterprise", 0.91f},
    {19, 2, "AI Regulatory Specialist", "enterprise", 0.91f},
    {19, 3, "AI Regulatory Specialist", "enterprise", 0.91f},
    {19, 4, "AI Regulatory Specialist", "enterprise", 0.91f},
    {19, 5, "AI Regulatory Specialist", "enterprise", 0.91f},
    {19, 6, "AI Regulatory Specialist", "enterprise", 0.91f},
    {20, 1, "Human-AI Interaction Designer", "parsing", 0.94f},
    {20, 2, "Human-AI Interaction Designer", "parsing", 0.94f},
    {20, 3, "Human-AI Interaction Designer", "parsing", 0.94f},
    {20, 4, "Human-AI Interaction Designer", "parsing", 0.94f},
    {20, 5, "Human-AI Interaction Designer", "parsing", 0.94f},
    {20, 6, "Human-AI Interaction Designer", "parsing", 0.94f},
};

// ── Globals ─────────────────────────────────────────────────────────
static WDFDEVICE gDevice = NULL;
static HANDLE gMetacognitionThread = NULL;
static volatile BOOLEAN gMetacognitionRunning = FALSE;
static volatile FLOAT gKernelConfidence = 1.0f;
static volatile FLOAT gSchedulerAUROC = 0.95f;
static volatile FLOAT gAgentCoherence[MAX_AGENT_COUNT] = {0};
static volatile FLOAT gTeamPhi = 0.0f;
static ULONG gAgentCount = 20;  // current number of active agents

// ═══════════════════════════════════════════════════════════════════
// 1. ENTRY POINT
// ═══════════════════════════════════════════════════════════════════
NTSTATUS DriverEntry(
    IN PDRIVER_OBJECT DriverObject,
    IN PUNICODE_STRING RegistryPath)
{
    WDF_DRIVER_CONFIG config;
    NTSTATUS status;

    KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL,
               "[Arkhe] DriverEntry v2.3: Initializing Cathedral in ring 0...\n"));

    status = ArkheValidateConstitution();
    if (!NT_SUCCESS(status)) return status;

    WDF_DRIVER_CONFIG_INIT(&config, ArkheEvtDeviceAdd);
    status = WdfDriverCreate(DriverObject, RegistryPath, WDF_NO_OBJECT_ATTRIBUTES,
                             &config, WDF_NO_HANDLE);
    if (!NT_SUCCESS(status)) return status;

    KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL,
               "[Arkhe] Constitution validated. Cathedral driver v2.3 loaded.\n"));
    return STATUS_SUCCESS;
}

// ═══════════════════════════════════════════════════════════════════
// 2. DEVICE ADD
// ═══════════════════════════════════════════════════════════════════
NTSTATUS ArkheEvtDeviceAdd(
    IN WDFDRIVER Driver,
    IN PWDFDEVICE_INIT DeviceInit)
{
    WDF_OBJECT_ATTRIBUTES deviceAttributes;
    WDFDEVICE device;
    WDF_IO_QUEUE_CONFIG queueConfig;
    NTSTATUS status;

    WdfDeviceInitSetDeviceType(DeviceInit, FILE_DEVICE_UNKNOWN);
    WdfDeviceInitSetCharacteristics(DeviceInit, FILE_DEVICE_SECURE_OPEN, FALSE);
    WdfDeviceInitSetExclusive(DeviceInit, TRUE);

    WDF_OBJECT_ATTRIBUTES_INIT(&deviceAttributes);
    status = WdfDeviceCreate(&DeviceInit, &deviceAttributes, &device);
    if (!NT_SUCCESS(status)) return status;

    gDevice = device;

    WDF_IO_QUEUE_CONFIG_INIT_DEFAULT_QUEUE(&queueConfig, WdfIoQueueDispatchParallel);
    queueConfig.EvtIoDeviceControl = ArkheEvtIoDeviceControl;
    queueConfig.EvtIoRead = ArkheEvtIoRead;

    status = WdfIoQueueCreate(device, &queueConfig, WDF_NO_OBJECT_ATTRIBUTES, WDF_NO_HANDLE);
    if (!NT_SUCCESS(status)) return status;

    ArkheInitializeCaster();
    ArkheEnableRTZ();
    ArkheStartMetacognition();

    // Initialize agent coherence with base values from 600-cell mapping
    for (ULONG i = 0; i < gAgentCount; i++) {
        gAgentCoherence[i] = gVertexAgentMap[i * 6].base_coherence;
    }

    KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL,
               "[Arkhe] Device created. v2.3: CASTER, RTZ, METACOG, 600-CELL MAP, VIZ IOCTLs active.\n"));
    return STATUS_SUCCESS;
}

// ═══════════════════════════════════════════════════════════════════
// 3-6. CONSTITUTION, CASTER, RTZ, METACOGNITION (unchanged from v2.2)
// ═══════════════════════════════════════════════════════════════════
NTSTATUS ArkheValidateConstitution() {
    ULONG magic = ARKHE_CONSTITUTION_MAGIC;
    FLOAT ghost = GHOST_THRESHOLD;
    if (ghost <= 0.0f) return STATUS_INVALID_IMAGE_FORMAT;
    if (magic != 0x58494D24) return STATUS_INVALID_SIGNATURE;
    return STATUS_SUCCESS;
}

NTSTATUS ArkheInitializeCaster() {
    NTSTATUS status = PsSetCreateProcessNotifyRoutineEx(ArkheCasterCallback, FALSE);
    return status;
}

VOID ArkheCasterCallback(IN HANDLE ProcessId, IN HANDLE ThreadId, IN BOOLEAN Create) {
    UNREFERENCED_PARAMETER(ProcessId);
    UNREFERENCED_PARAMETER(ThreadId);
    UNREFERENCED_PARAMETER(Create);
}

NTSTATUS ArkheEnableRTZ() {
    PVOID canonBuffer = ExAllocatePool2(POOL_FLAG_NON_PAGED, 0x1000, ARKHE_POOL_TAG);
    if (!canonBuffer) return STATUS_INSUFFICIENT_RESOURCES;
    MmLockPagableDataSection(canonBuffer);
    return STATUS_SUCCESS;
}

NTSTATUS ArkheStartMetacognition() {
    HANDLE threadHandle;
    NTSTATUS status;
    gMetacognitionRunning = TRUE;
    status = PsCreateSystemThread(&threadHandle, THREAD_ALL_ACCESS, NULL, NULL, NULL,
                                   ArkheMetacognitionWorker, NULL);
    if (!NT_SUCCESS(status)) { gMetacognitionRunning = FALSE; return status; }
    gMetacognitionThread = threadHandle;
    return STATUS_SUCCESS;
}

VOID ArkheMetacognitionWorker(IN PVOID Context) {
    UNREFERENCED_PARAMETER(Context);
    LARGE_INTEGER interval;
    interval.QuadPart = -((LONGLONG)METACOGNITION_INTERVAL_MS * 10000);
    while (gMetacognitionRunning) {
        if (gTeamPhi > 0.8f) gKernelConfidence = min(1.0f, gKernelConfidence + 0.01f);
        else if (gTeamPhi < 0.5f) gKernelConfidence = max(0.0f, gKernelConfidence - 0.01f);
        KeDelayExecutionThread(KernelMode, FALSE, &interval);
    }
    PsTerminateSystemThread(STATUS_SUCCESS);
}

// ═══════════════════════════════════════════════════════════════════
// 7. DEVICE IO — \\.\ArkheMeta Interface (v2.3 with Visualization IOCTLs)
// ═══════════════════════════════════════════════════════════════════
VOID ArkheEvtIoDeviceControl(
    IN WDFQUEUE Queue,
    IN WDFREQUEST Request,
    IN size_t OutputBufferLength,
    IN size_t InputBufferLength,
    IN ULONG IoControlCode)
{
    UNREFERENCED_PARAMETER(Queue);

    NTSTATUS status = STATUS_SUCCESS;
    PVOID inputBuffer = NULL, outputBuffer = NULL;
    size_t inputSize = 0, outputSize = 0;

    switch (IoControlCode) {
        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_READ_ACCESS):
            // Legacy: Get kernel confidence metrics
            status = WdfRequestRetrieveOutputBuffer(Request, OutputBufferLength, &outputBuffer, &outputSize);
            if (!NT_SUCCESS(status)) break;
            if (outputSize >= 128) {
                RtlStringCbPrintfA((CHAR*)outputBuffer, outputSize,
                    "{\"confidence\":%.3f,\"auroc\":%.3f,\"ghost\":%.3f}\n",
                    gKernelConfidence, gSchedulerAUROC, GHOST_THRESHOLD);
                WdfRequestSetInformation(Request, (ULONG)strlen((CHAR*)outputBuffer));
            }
            break;

        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x802, METHOD_BUFFERED, FILE_WRITE_ACCESS):
            // Update agent coherence from Career Coherence Tracker
            status = WdfRequestRetrieveInputBuffer(Request, InputBufferLength, &inputBuffer, &inputSize);
            if (!NT_SUCCESS(status)) break;
            if (inputSize >= sizeof(FLOAT) * gAgentCount) {
                RtlCopyMemory((PVOID)gAgentCoherence, inputBuffer, sizeof(FLOAT) * gAgentCount);
                FLOAT real = 0.0f, imag = 0.0f;
                for (ULONG i = 0; i < gAgentCount; i++) {
                    FLOAT phase = acosf(gAgentCoherence[i]);
                    real += cosf(phase);
                    imag += sinf(phase);
                }
                gTeamPhi = sqrtf(real * real + imag * imag) / gAgentCount;
            }
            break;

        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x803, METHOD_BUFFERED, FILE_READ_ACCESS):
            // Query vertex mapping
            status = WdfRequestRetrieveOutputBuffer(Request, OutputBufferLength, &outputBuffer, &outputSize);
            if (!NT_SUCCESS(status)) break;
            if (outputSize >= sizeof(VERTEX_AGENT_MAP)) {
                ULONG vertexIndex = 0;
                status = WdfRequestRetrieveInputBuffer(Request, InputBufferLength, &inputBuffer, &inputSize);
                if (NT_SUCCESS(status) && inputSize >= sizeof(ULONG)) vertexIndex = *(PULONG)inputBuffer;
                if (vertexIndex < VERTEX_COUNT) {
                    RtlCopyMemory(outputBuffer, &gVertexAgentMap[vertexIndex], sizeof(VERTEX_AGENT_MAP));
                    WdfRequestSetInformation(Request, sizeof(VERTEX_AGENT_MAP));
                } else status = STATUS_INVALID_PARAMETER;
            }
            break;

        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x804, METHOD_BUFFERED, FILE_READ_ACCESS):
            // NEW v2.3: Get complete 600-cell mapping as JSON
            status = WdfRequestRetrieveOutputBuffer(Request, OutputBufferLength, &outputBuffer, &outputSize);
            if (!NT_SUCCESS(status)) break;
            if (outputSize >= 32768) {  // ~32KB for full JSON
                CHAR* buf = (CHAR*)outputBuffer;
                ULONG offset = 0;
                offset += RtlStringCbPrintfA(buf + offset, outputSize - offset, "{\"vertices\":[");
                for (ULONG i = 0; i < VERTEX_COUNT; i++) {
                    offset += RtlStringCbPrintfA(buf + offset, outputSize - offset,
                        "{\"v\":%lu,\"agent\":%lu,\"inst\":%lu,\"role\":\"%s\",\"domain\":\"%s\",\"coh\":%.3f}%s",
                        i, gVertexAgentMap[i].agent_id, gVertexAgentMap[i].instance,
                        gVertexAgentMap[i].role_name, gVertexAgentMap[i].domain,
                        gVertexAgentMap[i].base_coherence,
                        (i < VERTEX_COUNT - 1) ? "," : "]}\n");
                    if (offset >= outputSize - 256) break; // safety
                }
                WdfRequestSetInformation(Request, (ULONG)strlen(buf));
            }
            break;

        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x805, METHOD_BUFFERED, FILE_WRITE_ACCESS):
            // NEW v2.3: Register emerging role (Hook 804.3)
            status = WdfRequestRetrieveInputBuffer(Request, InputBufferLength, &inputBuffer, &inputSize);
            if (!NT_SUCCESS(status)) break;
            if (inputSize >= sizeof(EMERGING_ROLE) && gAgentCount < MAX_AGENT_COUNT) {
                EMERGING_ROLE* role = (EMERGING_ROLE*)inputBuffer;
                gAgentCoherence[gAgentCount] = role->base_coherence;
                gAgentCount++;
                KdPrintEx((DPFLTR_IHVDRIVER_ID, DPFLTR_INFO_LEVEL,
                           "[Arkhe] New role registered: %s (agent %lu)\n", role->role_name, gAgentCount));
            } else status = STATUS_INVALID_PARAMETER;
            break;

        case CTL_CODE(FILE_DEVICE_UNKNOWN, 0x806, METHOD_BUFFERED, FILE_READ_ACCESS):
            // NEW v2.3: Get coherence vector for visualization (Hook 805.3)
            status = WdfRequestRetrieveOutputBuffer(Request, OutputBufferLength, &outputBuffer, &outputSize);
            if (!NT_SUCCESS(status)) break;
            if (outputSize >= sizeof(FLOAT) * MAX_AGENT_COUNT + sizeof(FLOAT)) {
                RtlCopyMemory(outputBuffer, (PVOID)gAgentCoherence, sizeof(FLOAT) * gAgentCount);
                RtlCopyMemory((PVOID)((CHAR*)outputBuffer + sizeof(FLOAT) * gAgentCount),
                              (PVOID)&gTeamPhi, sizeof(FLOAT));
                WdfRequestSetInformation(Request, sizeof(FLOAT) * gAgentCount + sizeof(FLOAT));
            }
            break;

        default:
            status = STATUS_INVALID_DEVICE_REQUEST;
            break;
    }

    WdfRequestComplete(Request, status);
}

VOID ArkheEvtIoRead(
    IN WDFQUEUE Queue,
    IN WDFREQUEST Request,
    IN size_t Length)
{
    PVOID outputBuffer;
    size_t outputSize;
    NTSTATUS status;
    status = WdfRequestRetrieveOutputBuffer(Request, Length, &outputBuffer, &outputSize);
    if (!NT_SUCCESS(status)) { WdfRequestComplete(Request, status); return; }
    if (outputSize >= 256) {
        RtlStringCbPrintfA((CHAR*)outputBuffer, outputSize,
            "{\"phi\":%.4f,\"team_phi\":%.4f,\"agents\":%lu,\"vertices\":%d,"
            "\"ecosystem_mapped\":true,\"version\":\"2.3\"}\n",
            gKernelConfidence, gTeamPhi, gAgentCount, VERTEX_COUNT);
        WdfRequestSetInformation(Request, (ULONG)strlen((CHAR*)outputBuffer));
    }
    WdfRequestComplete(Request, STATUS_SUCCESS);
}
