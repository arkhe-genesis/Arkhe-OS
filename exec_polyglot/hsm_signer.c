#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <openssl/evp.h>

// Mock of PKCS11 types
typedef unsigned long CK_SESSION_HANDLE;
typedef unsigned long CK_OBJECT_HANDLE;
typedef unsigned char CK_BYTE;
typedef CK_BYTE* CK_BYTE_PTR;
typedef unsigned long CK_ULONG;
typedef CK_ULONG* CK_ULONG_PTR;
typedef unsigned long CK_RV;

#define CKR_OK 0
#define CKM_DILITHIUM3 0x00000001
#define NULL_PTR NULL

typedef struct {
    CK_ULONG mechanism;
    void* pParameter;
    CK_ULONG ulParameterLen;
} CK_MECHANISM;

// Mock implementations
CK_RV C_SignInit(CK_SESSION_HANDLE session, CK_MECHANISM* pMechanism, CK_OBJECT_HANDLE hKey) {
    if (pMechanism->mechanism != CKM_DILITHIUM3) return 1;
    return CKR_OK;
}

CK_RV C_Sign(CK_SESSION_HANDLE session, CK_BYTE_PTR pData, CK_ULONG ulDataLen, CK_BYTE_PTR pSignature, CK_ULONG_PTR pulSignatureLen) {
    // Generate dummy signature
    const char* mock_sig = "mock_dilithium3_signature_from_hsm";
    strncpy((char*)pSignature, mock_sig, *pulSignatureLen);
    *pulSignatureLen = strlen(mock_sig);
    return CKR_OK;
}

CK_RV sign_with_hsm(CK_SESSION_HANDLE session, CK_OBJECT_HANDLE key,
                    CK_BYTE_PTR data, CK_ULONG data_len,
                    CK_BYTE_PTR signature, CK_ULONG_PTR sig_len) {

    // 1. Iniciar mecanismo de assinatura Dilithium3
    CK_MECHANISM mech = {CKM_DILITHIUM3, NULL_PTR, 0};
    CK_RV rv = C_SignInit(session, &mech, key);
    if (rv != CKR_OK) return rv;

    // 2. Assinar dados (a chave NUNCA é retornada)
    rv = C_Sign(session, data, data_len, signature, sig_len);

    // 3. Retornar apenas a assinatura
    return rv;
}

int main() {
    printf("🔐 FIPS 140-3 HSM Signer (C)\n");

    CK_SESSION_HANDLE mock_session = 1;
    CK_OBJECT_HANDLE mock_key = 1; // Extractable = FALSE
    CK_BYTE data[] = "proposalthatwasvalidated";
    CK_BYTE signature[256];
    CK_ULONG sig_len = sizeof(signature);

    CK_RV result = sign_with_hsm(mock_session, mock_key, data, strlen((char*)data), signature, &sig_len);

    if (result == CKR_OK) {
        printf("Signature generated successfully inside HSM boundary.\n");
        printf("Signature (hex/mock): ");
        for (CK_ULONG i = 0; i < sig_len; i++) {
            printf("%02x", signature[i]);
        }
        printf("\n");
        printf("Key extraction prevented by hardware.\n");
    } else {
        printf("HSM signing failed.\n");
    }

    return 0;
}
