/**
 * @file coherence_biometrics.h
 * @brief CoherenceBiometrics — OrbVM Module for Phase-Based Biometric Identity
 *
 * ARKHE-Ω / Arkhe(n) — Tzinor Core
 */

#ifndef COHERENCE_BIOMETRICS_H
#define COHERENCE_BIOMETRICS_H

#include <cmath>
#include <vector>
#include <string>
#include <array>
#include <cstdint>
#include <algorithm>
#include <numeric>
#include <limits>
#include <functional>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <chrono>
#include <random>

namespace arkhe {
namespace biometrics {

// ============================================================================
//  Physical & Mathematical Constants
// ============================================================================

static constexpr double PHI_INV_SQ      = 0.38196601125010515;
static constexpr double LAMBDA2_CRITICAL = 0.847;
static constexpr double D_FRACTAL_OPTIMAL = 2.5;
static constexpr int VITAL_ID_BITS       = 128;
static constexpr int FINGERPRINT_CHANNELS = 16;
static constexpr double CLONE_THRESHOLD   = 0.92;
static constexpr double AUTH_THRESHOLD    = 0.85;

// --- Liveness Constants ---
static constexpr double MICRO_SACCADE_RATE_MIN = 1.0;
static constexpr double MICRO_SACCADE_RATE_MAX = 5.0;
static constexpr double SACCADE_VEL_THRESHOLD = 20.0;
static constexpr double LIVENESS_THRESHOLD_SIGMA0 = 0.90;
static constexpr double IR_CAMERA_FPS = 240.0;
static constexpr double GSR_SAMPLE_FREQ_HZ = 20.0;

// ============================================================================
//  Enums
// ============================================================================

enum class AcquisitionModality { PPG, EEG, ECG, GSR, IMPEDANCE };
enum class SigmaLevel { LEVEL_0, LEVEL_1, LEVEL_2 };
enum class AttackType { NONE, SILICONE_MASK, VIDEO_REPLAY, SYNTHETIC_GSR, NEURAL_IMPLANT, DEAD_TISSUE, UNKNOWN };
enum class AuthResult { AUTHENTICATED, INCONCLUSIVE, REJECTED, CLONE_DETECTED, LOW_QUALITY };

// ============================================================================
//  Data Structures
// ============================================================================

struct CoherenceSample {
    int64_t timestamp_ms = 0;
    double R_coherence = 0.0;
    double lambda2 = 0.0;
    double K_local = 0.0;
    double omega_mean = 0.0;
    double omega_std = 0.0;
    double D_f = 0.0;
    double SNR_dB = 0.0;
    double quality = 0.0;
    std::vector<std::vector<double>> phase_angles;
};

struct VitalID {
    std::array<uint8_t, 16> bytes{};
    std::string hex() const {
        std::ostringstream oss;
        for (auto b : bytes) oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(b);
        return oss.str();
    }
};

struct PhaseFingerprint {
    std::array<uint8_t, FINGERPRINT_CHANNELS> channels{};
    double similarity(const PhaseFingerprint& other) const {
        int matches = 0;
        for (int i = 0; i < FINGERPRINT_CHANNELS; ++i) {
            if (std::abs(static_cast<int>(channels[i]) - static_cast<int>(other.channels[i])) <= 1) ++matches;
        }
        return static_cast<double>(matches) / FINGERPRINT_CHANNELS;
    }
};

struct VitalIDRecord {
    VitalID id;
    PhaseFingerprint fingerprint;
    std::string orcid;
};

struct Point2D { double x = 0.0; double y = 0.0; };

struct MicroSaccadeFeatures {
    double rate_hz = 0.0;
    double mean_amplitude_deg = 0.0;
    double peak_velocity_deg_s = 0.0;
};

struct GSRFeatures {
    double tonic_level_uS = 0.0;
    double phasic_amplitude_uS = 0.0;
    double response_count = 0.0;
};

struct LivenessEvidence {
    double liveness_score = 0.0;
    AttackType attack_type = AttackType::NONE;
    std::string attack_detail;
};

struct AuthResultDetail {
    AuthResult result = AuthResult::REJECTED;
    double similarity = 0.0;
    double quality_score = 0.0;
    std::string detail;
};

// ============================================================================
//  Implementation
// ============================================================================

inline double assessSampleQuality(const CoherenceSample& sample) {
    double q = 1.0;
    if (sample.R_coherence < 0.1 || sample.R_coherence > 0.99) q -= 0.3;
    if (sample.SNR_dB < 10.0) q -= 0.2;
    return std::max(0.0, std::min(1.0, q));
}

inline PhaseFingerprint extractFingerprint(const std::vector<CoherenceSample>& samples) {
    PhaseFingerprint fp;
    if (samples.empty()) return fp;
    double mean_R = 0, mean_l2 = 0, mean_K = 0;
    for (const auto& s : samples) {
        mean_R += s.R_coherence; mean_l2 += s.lambda2; mean_K += s.K_local;
    }
    mean_R /= samples.size(); mean_l2 /= samples.size(); mean_K /= samples.size();

    fp.channels[0] = static_cast<uint8_t>(mean_R * 255.0);
    fp.channels[1] = static_cast<uint8_t>((mean_l2 / 1.5) * 255.0);
    fp.channels[2] = static_cast<uint8_t>((mean_K / 25.0) * 255.0);
    return fp;
}

inline VitalID deriveVitalID(const PhaseFingerprint& fp) {
    uint64_t h_low = 0xCBF29CE484222325ULL;
    uint64_t h_high = 0xCBF29CE484222325ULL ^ 0xAAAAAAAAAAAAAAAAULL;
    for (int i = 0; i < FINGERPRINT_CHANNELS; ++i) {
        h_low ^= fp.channels[i]; h_low *= 0x00000100000001B3ULL;
    }
    // Golden ratio cascade
    for (int r = 0; r < 3; ++r) {
        h_low += static_cast<uint64_t>(PHI_INV_SQ * static_cast<double>(h_high));
        h_high += static_cast<uint64_t>(PHI_INV_SQ * static_cast<double>(h_low));
    }
    VitalID id;
    for (int i = 0; i < 8; ++i) {
        id.bytes[i] = (h_low >> (i * 8)) & 0xFF;
        id.bytes[i+8] = (h_high >> (i * 8)) & 0xFF;
    }
    return id;
}

inline AuthResultDetail authenticate(const CoherenceSample& live_sample, const VitalIDRecord& stored_record) {
    AuthResultDetail result;
    double q = assessSampleQuality(live_sample);
    if (q < 0.7) { result.result = AuthResult::LOW_QUALITY; return result; }

    PhaseFingerprint live_fp = extractFingerprint({live_sample});
    result.similarity = live_fp.similarity(stored_record.fingerprint);

    if (result.similarity >= CLONE_THRESHOLD) result.result = AuthResult::CLONE_DETECTED;
    else if (result.similarity >= AUTH_THRESHOLD) result.result = AuthResult::AUTHENTICATED;
    else result.result = AuthResult::REJECTED;

    return result;
}

} // namespace biometrics
} // namespace arkhe

#endif // COHERENCE_BIOMETRICS_H
