import asyncio
import numpy as np

# Import the modules we just created/updated
from arkp_benchmark.ewc_gem_continual_learning import ContinualLearningCycle
from arkp_bio.chaperones.cryo_em_validation import ChaperoneValidator
from arkp_field.src.services.rl_profile_adapter import RlProfileOptimizer, AttractorParams

async def run_all_tests():
    print("\n--- Testing EWC/GEM Continual Learning ---")
    cl_cycle = ContinualLearningCycle()

    # Task 1
    data_task1 = [{"input": "sample", "label": 1} for _ in range(100)]
    cl_cycle.train_task(task_id=1, train_data=data_task1, epochs=2)

    # Task 2 (testing catastrophic forgetting prevention)
    data_task2 = [{"input": "sample_2", "label": 2} for _ in range(100)]
    cl_cycle.train_task(task_id=2, train_data=data_task2, epochs=2)

    print("\n--- Testing Cryo-EM Validation ---")
    validator = ChaperoneValidator(chaperone_network=None) # Mock network
    dataset = validator.load_cryo_em_data("PDB_1A2B", sequence="MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEE")
    result = validator.validate_folding("PDB_1A2B", np.ones(4), 1.0)
    print(f"Validation result: Correlation {result['cross_correlation']:.3f}, Validated: {result['validated']}")

    print("\n--- Testing RL Profile Optimizer ---")
    optimizer = RlProfileOptimizer("user_123", AttractorParams(1.5, 0.5, 0.5, 1.0))
    for step in range(5):
        action = optimizer.choose_action()
        print(f"Step {step} action: {action}")

        # Simulate environment response
        metrics = {'exorcised': False, 'phi_c': 0.8, 'latency_ms': 150}
        reward = optimizer.calculate_reward(user_feedback=4.0, metrics=metrics)

        optimizer.update(state_metrics=metrics, deltas=action, reward=reward)
        print(f"Reward: {reward:.3f}, New Params: {optimizer.current_params}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
