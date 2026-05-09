// KYM/SecureEnclaveManager.swift
// Nexus iOS — Gerenciamento seguro de chaves criptográficas via Secure Enclave

import Foundation
import LocalAuthentication
import Security

class SecureEnclaveManager {
    static let shared = SecureEnclaveManager()

    private let keyTag = "os.arkhe.nexus.kym.key"
    private let accessControl: SecAccessControl

    private init() {
        // Configurar controle de acesso: requer biometria + dispositivo desbloqueado
        accessControl = SecAccessControlCreateWithFlags(
            nil,
            kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly,
            [.privateKeyUsage, .userPresence],
            nil
        )!
    }

    /// Gera novo par de chaves Ed25519 no Secure Enclave
    func generateKeyPair() async throws -> Data {
        // Verificar se Secure Enclave está disponível
        guard #available(iOS 11.0, *), SecEnclaveIsPresent() else {
            throw NSError(domain: "SecureEnclave", code: -1,
                         userInfo: [NSLocalizedDescriptionKey: "Secure Enclave não disponível"])
        }

        // Parâmetros para geração de chave
        let parameters: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
            kSecAttrKeySizeInBits as String: 256,
            kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave,
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: keyTag.data(using: .utf8)!,
                kSecAttrAccessControl as String: accessControl
            ]
        ]

        // Gerar par de chaves
        var error: Unmanaged<CFError>?
        guard let privateKey = SecKeyCreateRandomKey(parameters as CFDictionary, &error) else {
            throw error!.takeRetainedValue() as Error
        }

        // Extrair chave pública para uso externo
        guard let publicKey = SecKeyCopyPublicKey(privateKey) else {
            throw NSError(domain: "KeyExtraction", code: -2,
                         userInfo: [NSLocalizedDescriptionKey: "Falha ao extrair chave pública"])
        }

        // Exportar chave pública em formato DER
        var pubError: Unmanaged<CFError>?
        guard let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, &pubError) as Data? else {
            throw pubError!.takeRetainedValue() as Error
        }

        return publicKeyData
    }

    /// Assina desafio de verificação KYM usando chave privada no Secure Enclave
    func signChallenge(_ challenge: Data) async throws -> Data {
        // Recuperar chave privada do Secure Enclave
        let query: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrApplicationTag as String: keyTag.data(using: .utf8)!,
            kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
            kSecReturnRef as String: true
        ]

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let privateKey = item as? SecKey else {
            throw NSError(domain: "KeyRetrieval", code: -3,
                         userInfo: [NSLocalizedDescriptionKey: "Chave privada não encontrada"])
        }

        // Preparar parâmetros de assinatura (Ed25519 via Secure Enclave)
        let algorithm: SecKeyAlgorithm = .ECDSASignatureDigestX962SHA256

        // Verificar se chave suporta o algoritmo
        guard SecKeyIsAlgorithmSupported(privateKey, .sign, algorithm) else {
            throw NSError(domain: "Algorithm", code: -4,
                         userInfo: [NSLocalizedDescriptionKey: "Algoritmo não suportado"])
        }

        // Assinar desafio
        var signError: Unmanaged<CFError>?
        guard let signature = SecKeyCreateSignature(
            privateKey,
            algorithm,
            challenge as CFData,
            &signError
        ) as Data? else {
            throw signError!.takeRetainedValue() as Error
        }

        return signature
    }

    /// Verifica integridade do dispositivo (jailbreak detection)
    func verifyDeviceIntegrity() -> Bool {
        // Verificações básicas de integridade
        let checks = [
            // Verificar se app está em sandbox
            !FileManager.default.fileExists(atPath: "/.bootstrapped"),

            // Verificar ausência de Cydia/Substrate
            !FileManager.default.fileExists(atPath: "/Applications/Cydia.app"),

            // Verificar permissões de escrita em diretórios do sistema
            !FileManager.default.isWritableFile(atPath: "/"),

            // Verificar se debugger está anexado
            !isDebuggerAttached()
        ]

        return checks.allSatisfy { $0 }
    }

    private func isDebuggerAttached() -> Bool {
        var info = kinfo_proc()
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        var size = MemoryLayout<kinfo_proc>.stride
        return sysctl(&mib, UInt32(mib.count), &info, &size, nil, 0) == 0 &&
               (info.kp_proc.p_flag & P_TRACED) != 0
    }
}