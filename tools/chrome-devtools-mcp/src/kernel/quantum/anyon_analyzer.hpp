/**
 * @file anyon_analyzer.hpp
 * @brief Real-time Fibonacci anyon fusion analyzer for CORVO OS
 * @author CIC - Complexo Integrado CORVO
 * @version 1.0.0
 */

#ifndef ANYON_ANALYZER_HPP
#define ANYON_ANALYZER_HPP

#include <cstdint>
#include <cmath>
#include <array>
#include <vector>
#include <memory>
#include <algorithm>
#include <numeric>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace corvo {
namespace quantum {

// ============================================================================
// Constants and Physical Parameters
// ============================================================================

constexpr double PHI = (1.0 + 1.2360679774997896964) / 2.0;    // Golden Ratio approx
constexpr double P_VAC_FIBONACCI = 0.38196601125;             // φ⁻²
constexpr double P_TAU_FIBONACCI = 1.0 - P_VAC_FIBONACCI;

constexpr double P_VAC_ISING = 0.5;                            // Null hypothesis
constexpr double P_TAU_ISING = 0.5;

constexpr double MU0 = 0.05;    // Mean photons for vacuum outcome (dark counts)
constexpr double MU1 = 1.0;       // Mean photons for τ outcome (bright)

constexpr double LOG_LIKELIHOOD_THRESHOLD = 6.0;
constexpr uint32_t MIN_TRIALS = 1000;

// ============================================================================
// Statistical Functions
// ============================================================================

/**
 * @brief Log-gamma function (Lanczos approximation)
 */
inline double log_gamma(double x) {
    const double g = 7.0;
    const std::array<double, 9> c = {
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    };

    if (x < 0.5) {
        return std::log(M_PI / std::sin(M_PI * x)) - log_gamma(1.0 - x);
    }

    x -= 1.0;
    double a = c[0];
    for (int i = 1; i < 9; ++i) {
        a += c[i] / (x + i);
    }
    double t = x + g + 0.5;
    return 0.5 * std::log(2.0 * M_PI) + (x + 0.5) * std::log(t) - t + std::log(a);
}

/**
 * @brief Log Poisson PMF (numerically stable)
 */
inline double log_poisson(uint32_t k, double mu) {
    if (mu <= 0.0) return -INFINITY;
    return -mu + k * std::log(mu) - log_gamma(k + 1.0);
}

inline double poisson_pmf(uint32_t k, double mu) {
    return std::exp(log_poisson(k, mu));
}

// ============================================================================
// Mixture Model
// ============================================================================

class MixtureModel {
public:
    double p_vac;
    double mu0;
    double mu1;

    MixtureModel(double p = P_VAC_FIBONACCI, double m0 = MU0, double m1 = MU1)
        : p_vac(p), mu0(m0), mu1(m1) {}

    double log_prob(uint32_t k) const {
        double log_p0 = p_vac > 0 ? std::log(p_vac) + log_poisson(k, mu0) : -INFINITY;
        double log_p1 = (1.0 - p_vac) > 0 ? std::log(1.0 - p_vac) + log_poisson(k, mu1) : -INFINITY;

        if (log_p0 == -INFINITY) return log_p1;
        if (log_p1 == -INFINITY) return log_p0;

        return std::max(log_p0, log_p1) + std::log1p(std::exp(-std::abs(log_p0 - log_p1)));
    }

    double pmf(uint32_t k) const {
        return std::exp(log_prob(k));
    }
};

// ============================================================================
// Likelihood Ratio Test
// ============================================================================

class LikelihoodRatioTest {
private:
    MixtureModel fibonacci_model_;
    MixtureModel ising_model_;
    double log_lambda_;
    uint32_t trial_count_;

public:
    LikelihoodRatioTest()
        : fibonacci_model_(P_VAC_FIBONACCI, MU0, MU1),
          ising_model_(P_VAC_ISING, MU0, MU1),
          log_lambda_(0.0),
          trial_count_(0) {}

    void process_observation(uint32_t photon_count) {
        double log_L_fib = fibonacci_model_.log_prob(photon_count);
        double log_L_ising = ising_model_.log_prob(photon_count);

        log_lambda_ += (log_L_fib - log_L_ising);
        trial_count_++;
    }

    double get_log_lambda() const { return log_lambda_; }
    uint32_t get_trial_count() const { return trial_count_; }

    int8_t decision() const {
        if (trial_count_ < MIN_TRIALS) return 0;
        if (log_lambda_ > LOG_LIKELIHOOD_THRESHOLD) return 1;
        if (log_lambda_ < -LOG_LIKELIHOOD_THRESHOLD) return -1;
        return 0;
    }

    void reset() {
        log_lambda_ = 0.0;
        trial_count_ = 0;
    }
};

// ============================================================================
// Real-Time Analyzer Class
// ============================================================================

class AnyonAnalyzer {
public:
    enum class State : uint8_t { IDLE = 0, CALIBRATING, MEASURING, ANALYSIS_COMPLETE, ERROR };
    enum class Result : uint8_t { UNKNOWN = 0, FIBONACCI_ANYON_DETECTED, ISING_ANYON_DETECTED, CLASSICAL_SYSTEM, INSUFFICIENT_DATA, MEASUREMENT_ERROR };

private:
    static constexpr size_t HISTOGRAM_SIZE = 16;
    std::array<uint64_t, HISTOGRAM_SIZE> histogram_;
    std::unique_ptr<LikelihoodRatioTest> lr_test_;
    State current_state_;
    Result last_result_;
    uint64_t total_photons_;
    uint64_t window_start_time_;
    double measured_mu0_;
    double measured_mu1_;
    bool calibration_valid_;

public:
    AnyonAnalyzer()
        : histogram_{},
          lr_test_(std::make_unique<LikelihoodRatioTest>()),
          current_state_(State::IDLE),
          last_result_(Result::UNKNOWN),
          total_photons_(0),
          window_start_time_(0),
          measured_mu0_(0.0),
          measured_mu1_(0.0),
          calibration_valid_(false) {}

    void initialize() {
        histogram_.fill(0);
        lr_test_->reset();
        current_state_ = State::IDLE;
        last_result_ = Result::UNKNOWN;
        total_photons_ = 0;
        calibration_valid_ = false;
    }

    void start_measurement() {
        initialize();
        current_state_ = State::MEASURING;
    }

    void on_photon_detection(uint32_t photon_count) {
        if (current_state_ != State::MEASURING) return;
        size_t idx = std::min(static_cast<size_t>(photon_count), HISTOGRAM_SIZE - 1);
        histogram_[idx]++;
        total_photons_++;
        lr_test_->process_observation(photon_count);
    }

    Result analyze() {
        if (current_state_ != State::MEASURING && current_state_ != State::CALIBRATING) {
            last_result_ = Result::MEASUREMENT_ERROR;
            return last_result_;
        }
        current_state_ = State::ANALYSIS_COMPLETE;
        int8_t decision = lr_test_->decision();
        switch (decision) {
            case 1: last_result_ = Result::FIBONACCI_ANYON_DETECTED; break;
            case -1:
                if (lr_test_->get_log_lambda() < -LOG_LIKELIHOOD_THRESHOLD * 2) last_result_ = Result::CLASSICAL_SYSTEM;
                else last_result_ = Result::ISING_ANYON_DETECTED;
                break;
            default: last_result_ = Result::INSUFFICIENT_DATA; break;
        }
        return last_result_;
    }

    const std::array<uint64_t, HISTOGRAM_SIZE>& get_histogram() const { return histogram_; }
    double get_log_lambda() const { return lr_test_->get_log_lambda(); }
    State get_state() const { return current_state_; }
    Result get_result() const { return last_result_; }
};

#ifdef __cplusplus
extern "C" {
#endif
void corvo_anyon_init(void);
void corvo_anyon_start_measurement(void);
void corvo_anyon_submit_count(uint32_t count);
uint8_t corvo_anyon_analyze(void);
double corvo_anyon_get_log_lambda(void);
uint64_t corvo_anyon_get_histogram_bin(uint8_t bin);
void corvo_anyon_reset(void);
#ifdef __cplusplus
}
#endif

} // namespace quantum
} // namespace corvo

#endif // ANYON_ANALYZER_HPP
