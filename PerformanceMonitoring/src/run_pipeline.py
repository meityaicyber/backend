import argparse

def main():
    parser = argparse.ArgumentParser(description="Performance Monitoring Module")
    parser.add_argument("--config", required=True, help="Path to configuration")
    parser.add_argument("--dataset", required=True, help="Path to input dataset")
    parser.add_argument("--output", required=True, help="Path to output directory")
    args = parser.parse_args()
    
    print("Running pipeline with:")
    print(f"Config: {args.config}")
    print(f"Dataset: {args.dataset}")
    print(f"Output: {args.output}")

if __name__ == "__main__":
    main()
