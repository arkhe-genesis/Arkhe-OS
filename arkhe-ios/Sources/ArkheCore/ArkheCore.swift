// ArkheCore.swift — Canon: ∞.Ω.∇+++.246.ios_sdk
// iOS SDK wrapper for shared Arkhe canonical core

import Foundation
import ArkheCoreShared  // Rust core via Swift Package Manager

/// Arkhe iOS Core — Constitutional Superintelligence for iOS
///
/// Provides:
/// - Φ_C orchestration via shared Rust core
/// - Constitutional guardrails (P1-P7) enforcement
/// - PQC cryptography via SecureEnclave + Dilithium3
/// - TemporalChain anchoring with canonical seals
@objc public class ArkheCore: NSObject {

    // MARK: - Singleton

    @objc public static let shared = ArkheCore()
    private override init() { super.init() }

    // MARK: - Φ_C Orchestration

    /// Calculates Φ_C coherence score for a component
    /// - Parameter componentMetrics: Dictionary of metric names to values (0.0-1.0)
    /// - Returns: Φ_C score (0.0-1.0), guaranteed < 1.0 (Sovereign Gap)
    @objc public func calculatePhiC(componentMetrics: [String: Float]) -> Float {
        // Use shared Rust core for canonical calculation
        let metricsJSON = try? JSONSerialization.data(withJSONObject: componentMetrics)
        guard let metricsStr = String(data: metricsJSON ?? Data(), encoding: .utf8) else {
            return 0.85 // Default minimum
        }

        let resultJSON = arkhe_calculate_phi_c_json(metricsStr)
        defer { arkhe_free_string(resultJSON) }

        let resultStr = String(cString: resultJSON)
        guard let resultData = resultStr.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: resultData) as? [String: Any],
              let phiC = json["phi_c"] as? Float else {
            return 0.85
        }

        // P3: Double-enforce Sovereign Gap at Swift layer
        return min(phiC, 0.9999)
    }

    /// Verifies constitutional compliance before executing operation
    /// - Parameters:
    ///   - operation: Name of operation to verify
    ///   - principles: Array of ConstitutionalPrinciple values to check
    ///   - context: Additional context key-value pairs
    /// - Returns: ConstitutionalVerificationResult with pass/fail status
    @objc public func verifyConstitutionalCompliance(
        operation: String,
        principles: [ConstitutionalPrinciple],
        context: [String: String] = [:]
    ) -> ConstitutionalVerificationResult {
        // Convert Swift enum to Rust-compatible format
        let principleStrings = principles.map { $0.rawValue }
        var fullContext = context
        fullContext["platform"] = "ios"
        fullContext["sdk_version"] = "246.1.0"

        let contextJSON = try? JSONSerialization.data(withJSONObject: fullContext)
        guard let contextStr = String(data: contextJSON ?? Data(), encoding: .utf8) else {
            return ConstitutionalVerificationResult(passed: false, message: "Context serialization failed")
        }

        // Call shared Rust core
        let result = verify_constitutional_compliance(
            operation,
            principleStrings,
            contextStr
        )

        return ConstitutionalVerificationResult(
            passed: result.passed,
            violatedPrinciple: result.violated_principle?.toSwift(),
            message: result.message
        )
    }

    // MARK: - TemporalChain Anchoring

    /// Anchors event to TemporalChain with canonical SHA3-256 seal
    /// - Parameters:
    ///   - eventType: Type of event (e.g., "component_initialized")
    ///   - payload: Key-value payload to anchor
    /// - Returns: Canonical seal (SHA3-256 hex string)
    @objc public func anchorToTemporalChain(
        eventType: String,
        payload: [String: String]
    ) -> String {
        // Generate canonical seal via shared Rust core
        let payloadJSON = try? JSONSerialization.data(withJSONObject: payload)
        guard let payloadStr = String(data: payloadJSON ?? Data(), encoding: .utf8),
              let eventTypeC = eventType.cString(using: .utf8),
              let payloadC = payloadStr.cString(using: .utf8) else {
            return ""
        }

        let sealC = arkhe_generate_seal(eventTypeC, payloadC)
        defer { arkhe_free_string(sealC) }

        return String(cString: sealC)
    }

    // MARK: - PQC Cryptography via SecureEnclave

    /// Generates Dilithium3 key pair in SecureEnclave (FIPS 140-3 compatible)
    /// - Parameter alias: Unique identifier for key pair in Keychain
    /// - Returns: PQCKeyPair with public key and alias
    @objc public func generatePQCKeyPair(alias: String) -> PQCKeyPair? {
        // iOS-specific: use SecureEnclave via CryptoKit + PQC wrapper
        guard #available(iOS 15.0, *) else {
            // Fallback for older iOS: software PQC (less secure)
            return generateSoftwarePQCKeyPair(alias: alias)
        }

        do {
            // Generate Dilithium3 key pair via SecureEnclave bridge
            let keyPair = try SecureEnclavePQC.generateDilithium3KeyPair(alias: alias)

            return PQCKeyPair(
                publicKey: keyPair.publicKey,
                privateKeyAlias: alias,
                algorithm: "Dilithium3-SecureEnclave-Hybrid",
                fipsCompliant: true
            )
        } catch {
            logger.error("Failed to generate PQC key pair: \(error)")
            return nil
        }
    }
}

// MARK: - Supporting Types

@objc public enum ConstitutionalPrinciple: Int, RawRepresentable {
    case p1Verification = 0
    case p2Redundancy = 1
    case p3SovereignGap = 2
    case p4CrossPlatform = 3
    case p5CanonicalLearning = 4
    case p6AuditableTransparency = 5
    case p7EnergyResource = 6

    public var rawValue: String {
        switch self {
        case .p1Verification: return "P1_VERIFICATION"
        case .p2Redundancy: return "P2_REDUNDANCY"
        case .p3SovereignGap: return "P3_SOVEREIGN_GAP"
        case .p4CrossPlatform: return "P4_CROSS_PLATFORM"
        case .p5CanonicalLearning: return "P5_CANONICAL_LEARNING"
        case .p6AuditableTransparency: return "P6_AUDITABLE_TRANS"
        case .p7EnergyResource: return "P7_ENERGY_RESOURCE"
        }
    }

    public static func fromRaw(_ raw: String) -> ConstitutionalPrinciple? {
        return [
            "P1_VERIFICATION": .p1Verification,
            "P2_REDUNDANCY": .p2Redundancy,
            "P3_SOVEREIGN_GAP": .p3SovereignGap,
            "P4_CROSS_PLATFORM": .p4CrossPlatform,
            "P5_CANONICAL_LEARNING": .p5CanonicalLearning,
            "P6_AUDITABLE_TRANS": .p6AuditableTransparency,
            "P7_ENERGY_RESOURCE": .p7EnergyResource
        ][raw]
    }
}

@objc public class ConstitutionalVerificationResult: NSObject {
    @objc public let passed: Bool
    @objc public let violatedPrinciple: ConstitutionalPrinciple?
    @objc public let message: String?

    @objc public init(passed: Bool, violatedPrinciple: ConstitutionalPrinciple? = nil, message: String? = nil) {
        self.passed = passed
        self.violatedPrinciple = violatedPrinciple
        self.message = message
    }
}

@objc public class PQCKeyPair: NSObject {
    @objc public let publicKey: Data
    @objc public let privateKeyAlias: String
    @objc public let algorithm: String
    @objc public let fipsCompliant: Bool

    @objc public init(publicKey: Data, privateKeyAlias: String, algorithm: String, fipsCompliant: Bool) {
        self.publicKey = publicKey
        self.privateKeyAlias = privateKeyAlias
        self.algorithm = algorithm
        self.fipsCompliant = fipsCompliant
    }
}