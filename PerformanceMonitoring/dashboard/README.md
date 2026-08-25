# Performance Monitoring Dashboard

This is a read-only presentation layer that visualizes the JSON outputs of the core `PerformanceMonitoring` system.

## Setup & Installation

1. Navigate to the dashboard directory:
   ```bash
   cd dashboard
   ```
2. Install dependencies (requires Node.js):
   ```bash
   npm install
   ```
3. Copy the output data into the public folder for local consumption:
   ```bash
   mkdir public\data
   cp ..\output\scoring\organisation_scores.json public\data\
   cp ..\output\scoring\ranking_summary.json public\data\
   cp ..\output\evaluation\comparison_summary.json public\data\
   cp ..\data\sample_dataset.json public\data\
   cp ..\config\version_registry.json public\data\
   cp ..\output\test_report.json public\data\
   ```

## Development
Run the local dev server:
```bash
npm run dev
```

## Production Build & Offline Run (Phase 12)
To run the dashboard entirely offline (no node server):
1. Build the static bundle:
   ```bash
   npm run build
   ```
2. The `dist/` directory now contains a completely static, offline-ready web application.
3. You can serve this locally using any static server, or simply open `index.html` (if CORS allows file protocol), or use:
   ```bash
   npx serve -s dist
   ```

## Data Contract
- The dashboard **DOES NOT** compute any scores or ranks. It strictly visualizes what the backend outputs.
- Missing files or malformed JSON will throw an Error Boundary explicitly, and will not fall back to generated data.
- See `docs/DASHBOARD_DATA_CONTRACT.md` for exact JSON mapping.
