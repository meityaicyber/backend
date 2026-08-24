import sys
import subprocess

def verify():
    try:
        import sklearn
        import numpy as np
        import src.utils.json_utils
        print("PASS: Core dependencies and modules loaded.")
        
        print("Running end-to-end smoke test...")
        python_exec = sys.executable
        # Generate just 10 records
        cmd = f"{python_exec} -m src.dataset_generator --config config/generator_config.json --seed 1 --n 10 --output data/smoke_dataset.json"
        subprocess.run(cmd, shell=True, check=True)
        print("PASS: Smoke test generator")
        
        # Train, eval, score
        cmd = f"{python_exec} -m src.pipeline.train --config-prep config/preprocessing_config.json --config-model config/model_config.json --dataset data/smoke_dataset.json --output output/smoke_models"
        subprocess.run(cmd, shell=True, check=True)
        print("PASS: Smoke test training")
        
        cmd = f"{python_exec} -m src.pipeline.evaluate --config-prep config/preprocessing_config.json --dataset data/smoke_dataset.json --models output/smoke_models --output output/smoke_eval"
        subprocess.run(cmd, shell=True, check=True)
        print("PASS: Smoke test evaluation")
        
        cmd = f"{python_exec} -m src.pipeline.score --config-scoring config/scoring_config.json --config-schema config/feature_schema.json --models-meta output/smoke_models/models_metadata.json --dataset data/smoke_dataset.json --output output/smoke_scoring"
        subprocess.run(cmd, shell=True, check=True)
        print("PASS: Smoke test scoring")
        
        print("ALL VERIFICATIONS PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
