import argparse
import os
import subprocess
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Performance Monitoring Module End-to-End Pipeline")
    parser.add_argument("--config", default="config/generator_config.json", help="Path to generator configuration")
    parser.add_argument("--dataset", default="data/sample_dataset.json", help="Path to input dataset (or output for generator)")
    parser.add_argument("--output", default="output", help="Path to output directory")
    args = parser.parse_args()
    
    python_exec = sys.executable

    print("=== 1. Generate Dataset ===")
    run_cmd(f'"{python_exec}" -m src.dataset_generator --config {args.config} --seed 42 -n 10000 --output {args.dataset}')
    
    print("\n=== 2. Train Models ===")
    models_dir = os.path.join(args.output, "models")
    run_cmd(f'"{python_exec}" -m src.pipeline.train --config-prep config/preprocessing_config.json --config-model config/model_config.json --dataset {args.dataset} --output {models_dir}')
    
    print("\n=== 3. Evaluate Models ===")
    eval_dir = os.path.join(args.output, "evaluation")
    run_cmd(f'"{python_exec}" -m src.pipeline.evaluate --config-prep config/preprocessing_config.json --dataset {args.dataset} --models {models_dir} --output {eval_dir}')
    
    print("\n=== 4. Score and Rank ===")
    score_dir = os.path.join(args.output, "scoring")
    run_cmd(f'"{python_exec}" -m src.pipeline.score --config-scoring config/scoring_config.json --config-schema config/feature_schema.json --models-meta {models_dir}/models_metadata.json --dataset {args.dataset} --output {score_dir}')
    
    print("\nPipeline completed successfully.")

if __name__ == "__main__":
    main()
