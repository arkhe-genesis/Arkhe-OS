import Foundation
import HealthKit

/// Manages the collection of stochastic biological data (Heart Rate, HRV)
/// to be used as entropy and coherence inputs for the Arkhe(n) system.
class HealthKitManager: ObservableObject {
    let healthStore = HKHealthStore()
    
    @Published var currentHeartRate: Double = 0.0
    @Published var currentHRV: Double = 0.0
    @Published var isAuthorized: Bool = false
    
    let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
    let hrvType = HKQuantityType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!
    
    func requestAuthorization() {
        guard HKHealthStore.isHealthDataAvailable() else { return }
        
        let typesToRead: Set = [heartRateType, hrvType]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { success, error in
            DispatchQueue.main.async {
                self.isAuthorized = success
                if success {
                    self.startBiometricStreaming()
                }
            }
        }
    }
    
    private func startBiometricStreaming() {
        // 1. Heart Rate Streaming (Continuous)
        let hrQuery = HKAnchoredObjectQuery(type: heartRateType, predicate: nil, anchor: nil, limit: HKObjectQueryNoLimit) { [weak self] query, samples, deletedObjects, newAnchor, error in
            self?.processHeartRateSamples(samples)
        }
        
        hrQuery.updateHandler = { [weak self] query, samples, deletedObjects, newAnchor, error in
            self?.processHeartRateSamples(samples)
        }
        
        // 2. HRV Streaming (Stochastic Noise)
        let hrvQuery = HKAnchoredObjectQuery(type: hrvType, predicate: nil, anchor: nil, limit: HKObjectQueryNoLimit) { [weak self] query, samples, deletedObjects, newAnchor, error in
            self?.processHRVSamples(samples)
        }
        
        hrvQuery.updateHandler = { [weak self] query, samples, deletedObjects, newAnchor, error in
            self?.processHRVSamples(samples)
        }
        
        healthStore.execute(hrQuery)
        healthStore.execute(hrvQuery)
    }
    
    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let hrSamples = samples as? [HKQuantitySample], let latest = hrSamples.last else { return }
        DispatchQueue.main.async {
            self.currentHeartRate = latest.quantity.doubleValue(for: HKUnit(from: "count/min"))
        }
    }
    
    private func processHRVSamples(_ samples: [HKSample]?) {
        guard let hrvSamples = samples as? [HKQuantitySample], let latest = hrvSamples.last else { return }
        DispatchQueue.main.async {
            self.currentHRV = latest.quantity.doubleValue(for: HKUnit.secondUnit(with: .milli))
        }
    }
}
