# Performance Monitoring Module

## Contents
- `/config/`: D1 feature definitions and scoring configuration
- `/data/`: D2 dataset generator and generated sample dataset
- `/src/`: D3, D5, D6 pipeline, scoring and version mechanism
- `/deploy/`: D7 air-gapped package and update process
- `/tests/`: D8 automated test suite
- `/output/`: D4, D9 evaluation results and sample outputs
- `/docs/`: D10, D11, D12, D13 design, runbook, analysis, comparative study

## Run Command
The canonical command to run the module end-to-end from a fresh clone is:
```bash
python -m src.run_pipeline --config config/generator_config.json --dataset data/sample_dataset.json --output output/
```
(See `docs/D11_runbook.md` for full instructions.)
