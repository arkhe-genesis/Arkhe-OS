/*
 * ARKHE Ω-TEMP — Device Interface Registration (Windows)
 *
 * No Windows, drivers WDM/KMDF expõem seus devices via symbolic links
 * no namespace \\.\ARKHE\ para acesso do userspace.
 *
 * Cada subsistema tem seu próprio device:
 *   \\.\ARKHE\Temporal
 *   \\.\ARKHE\Consensus
 *   \\.\ARKHE\Merkle
 *   \\.\ARKHE\Crypto
 *   \\.\ARKHE\Netfilter
 */

#include <ntddk.h>
#include <wdm.h>
#include "arkhe_wdm.h"

/*
 * GUIDs para interfaces de device
 * Cada GUID identifica um subsistema ARKHE
 */
DEFINE_GUID(GUID_DEVINTERFACE_ARKHE_TEMPORAL,
    0xa1b2c3d4, 0xe5f6, 0x7890,
    0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89);

DEFINE_GUID(GUID_DEVINTERFACE_ARKHE_CONSENSUS,
    0xb2c3d4e5, 0xf6a7, 0x8901,
    0xbc, 0xde, 0xf0, 0x12, 0x34, 0x56, 0x78, 0x9a);

DEFINE_GUID(GUID_DEVINTERFACE_ARKHE_MERKLE,
    0xc3d4e5f6, 0xa7b8, 0x9012,
    0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab);

/*
 * Registrar todas as interfaces de device
 */
NTSTATUS RegisterArkheDeviceInterfaces(PWDFDEVICE_INIT DeviceInit)
{
    NTSTATUS status;
    DECLARE_CONST_UNICODE_STRING(devInterfaceTemporal,
        L"\\Device\\ARKHE_Temporal");
    DECLARE_CONST_UNICODE_STRING(symLinkTemporal,
        L"\\DosDevices\\ARKHE\\Temporal");

    DECLARE_CONST_UNICODE_STRING(devInterfaceConsensus,
        L"\\Device\\ARKHE_Consensus");
    DECLARE_CONST_UNICODE_STRING(symLinkConsensus,
        L"\\DosDevices\\ARKHE\\Consensus");

    DECLARE_CONST_UNICODE_STRING(devInterfaceMerkle,
        L"\\Device\\ARKHE_Merkle");
    DECLARE_CONST_UNICODE_STRING(symLinkMerkle,
        L"\\DosDevices\\ARKHE\\Merkle");

    /* Device Temporal */
    status = WdfDeviceCreateDeviceInterface(
        DeviceInit, &GUID_DEVINTERFACE_ARKHE_TEMPORAL, NULL);
    if (!NT_SUCCESS(status)) return status;

    /* Device Consensus */
    status = WdfDeviceCreateDeviceInterface(
        DeviceInit, &GUID_DEVINTERFACE_ARKHE_CONSENSUS, NULL);
    if (!NT_SUCCESS(status)) return status;

    /* Device Merkle */
    status = WdfDeviceCreateDeviceInterface(
        DeviceInit, &GUID_DEVINTERFACE_ARKHE_MERKLE, NULL);
    if (!NT_SUCCESS(status)) return status;

    return STATUS_SUCCESS;
}

/*
 * Criar symbolic links acessíveis pelo userspace
 * Nota: No Windows, \\.\ é o prefixo para device names
 * que não são acessíveis via CreateFile padrão.
 */
NTSTATUS CreateUserAccessibleSymLinks(VOID)
{
    UNICODE_STRING symbolicLink;
    UNICODE_STRING deviceName;
    NTSTATUS status;
    HANDLE linkHandle;

    /* Device Temporal */
    RtlInitUnicodeString(&deviceName, L"\\Device\\ARKHE_Temporal");
    RtlInitUnicodeString(&symbolicLink, L"\\DosDevices\\ARKHE\\Temporal");
    status = IoCreateSymbolicLink(&symbolicLink, &deviceName);
    if (!NT_SUCCESS(status)) { KdPrint(("ARKHE: Falha ao criar symlink Temporal: 0x%08X\n", status)); }

    /* Device Consensus */
    RtlInitUnicodeString(&deviceName, L"\\Device\\ARKHE_Consensus");
    RtlInitUnicodeString(&symbolicLink, L"\\DosDevices\\ARKHE\\Consensus");
    status = IoCreateSymbolicLink(&symbolicLink, &deviceName);
    if (!NT_SUCCESS(status)) { KdPrint(("ARKHE: Falha ao criar symlink Consensus: 0x%08X\n", status)); }

    /* Device Merkle */
    RtlInitUnicodeString(&deviceName, L"\\Device\\ARKHE_Merkle");
    RtlInitUnicodeString(&symbolicLink, L"\\DosDevices\\ARKHE\\Merkle");
    status = IoCreateSymbolicLink(&symbolicLink, &deviceName);
    if (!NT_SUCCESS(status)) { KdPrint(("ARKHE: Falha ao criar symlink Merkle: 0x%08X\n", status)); }

    /* Device Crypto */
    RtlInitUnicodeString(&deviceName, L"\\Device\\ARKHE_Crypto");
    RtlInitUnicodeString(&symbolicLink, L"\\DosDevices\\ARKHE\\Crypto");
    status = IoCreateSymbolicLink(&symbolicLink, &deviceName);
    if (!NT_SUCCESS(status)) { KdPrint(("ARKHE: Falha ao criar symlink Crypto: 0x%08X\n", status)); }

    /* Device Netfilter */
    RtlInitUnicodeString(&deviceName, L"\\Device\\ARKHE_Netfilter");
    RtlInitUnicodeString(&symbolicLink, L"\\DosDevices\\ARKHE\\Netfilter");
    status = IoCreateSymbolicLink(&symbolicLink, &deviceName);
    if (!NT_SUCCESS(status)) { KdPrint(("ARKHE: Falha ao criar symlink Netfilter: 0x%08X\n", status)); }

    return status;
}
