import numpy as np
import os
import json
from src.arkhe.layers.biological.ncbi_jgi_client import NCBIJGIClient
from src.arkhe.layers.biological.reed_solomon_decoder import benchmark_rs_decoders
from src.arkhe.layers.biological.chaperone_simulator import run_chaperone_comparison

def generate_report(dataset, rs_bench, chap_sims):
    report_path = "biological_expansion_report.json"

    # Basic statistics on dataset with cross validation split
    np.random.seed(42)
    indices = np.random.permutation(len(dataset))
    split = int(0.8 * len(dataset))
    train_idx, test_idx = indices[:split], indices[split:]

    train_junk = [dataset[i].junk_percentage for i in train_idx]
    test_junk = [dataset[i].junk_percentage for i in test_idx]
    train_rad = [dataset[i].rad_resistance for i in train_idx]
    test_rad = [dataset[i].rad_resistance for i in test_idx]

    avg_junk_train = sum(train_junk) / len(train_junk) if train_junk else 0
    avg_junk_test = sum(test_junk) / len(test_junk) if test_junk else 0

    avg_rad_train = sum(train_rad) / len(train_rad) if train_rad else 0
    avg_rad_test = sum(test_rad) / len(test_rad) if test_rad else 0

    report = {
        "dataset_stats": {
            "total_genomes": len(dataset),
            "cross_validation": {
                "train_size": len(train_idx),
                "test_size": len(test_idx),
                "train_avg_junk_percentage": round(avg_junk_train, 2),
                "test_avg_junk_percentage": round(avg_junk_test, 2),
                "train_avg_rad_resistance": round(avg_rad_train, 2),
                "test_avg_rad_resistance": round(avg_rad_test, 2),
                "validation_error_junk": round(abs(avg_junk_train - avg_junk_test), 2),
                "validation_error_rad": round(abs(avg_rad_train - avg_rad_test), 2)
            }
        },
        "rs_benchmark": rs_bench,
        "chaperone_simulation": {
            "no_chaperone_steps": chap_sims[0]["steps_to_fold"],
            "hsp70_steps": chap_sims[1]["steps_to_fold"],
            "groel_steps": chap_sims[2]["steps_to_fold"]
        }
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n--- Report Generated: {report_path} ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    print("=============================================")
    print(" Arkhe OS - Biological Expansion Integration ")
    print("=============================================\n")

    # 1. NCBI/JGI Extremophile Dataset Expansion
    print("1. Expanding Extremophile Dataset...")
    client = NCBIJGIClient()
    dataset = client.build_dataset(target_size=50) # Fetch 50
    print(f"Successfully collected {len(dataset)} extremophile genomes.")

    # 2. Reed-Solomon Decoder Benchmark
    print("\n2. Running Reed-Solomon Decoding Benchmark...")
    rs_bench = benchmark_rs_decoders()

    # 3. Chaperone Simulation
    print("\n3. Running Chaperone Folding Simulation...")
    chap_sims = run_chaperone_comparison()

    # 4. Report Generation
    generate_report(dataset, rs_bench, chap_sims)
