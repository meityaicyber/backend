import React from 'react';

const Architecture = () => {
  return (
    <div className="p-8 max-w-5xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Architecture / Technical View</h1>
        <p className="text-gray-500">System pipeline and data flow representation</p>
      </header>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-6">Backend Data Pipeline</h2>
        
        <div className="flex flex-col items-center max-w-2xl mx-auto space-y-2 font-mono text-sm">
          <div className="flex items-center gap-4 bg-gray-50 p-4 rounded-lg w-full justify-center border border-gray-200">
            <span>Synthetic Data</span>
            <span className="text-gray-400">→</span>
            <span>Validation</span>
            <span className="text-gray-400">→</span>
            <span>Preprocessing</span>
            <span className="text-gray-400">→</span>
            <span>4 Models</span>
            <span className="text-gray-400">→</span>
            <span>Evaluation</span>
          </div>
          <div className="text-gray-400 text-lg">↓</div>
          <div className="flex items-center gap-8 bg-blue-50 p-4 rounded-lg w-full justify-center border border-blue-100 text-blue-900 font-bold">
            <span>Renewal Prediction</span>
            <span>Performance Score</span>
          </div>
          <div className="text-gray-400 text-lg">↓</div>
          <div className="bg-gray-50 p-4 rounded-lg w-full text-center border border-gray-200">
            Ranking
          </div>
          <div className="text-gray-400 text-lg">↓</div>
          <div className="bg-gray-50 p-4 rounded-lg w-full text-center border border-gray-200">
            Traceability / Versioning
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-6">Dashboard Presentation Layer</h2>
        <div className="flex flex-col items-center max-w-2xl mx-auto space-y-4 font-mono text-sm">
          <div className="bg-amber-50 text-amber-900 border border-amber-200 p-4 rounded-lg w-full text-center font-bold">
            JSON Outputs (Authoritative)
          </div>
          <div className="text-gray-400 text-lg">↓</div>
          <div className="bg-indigo-50 text-indigo-900 border border-indigo-200 p-4 rounded-lg w-full text-center font-bold">
            Dashboard (Read-Only)
          </div>
        </div>
        <div className="mt-8 text-sm text-gray-600 bg-gray-50 p-6 rounded-lg border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-2">Data Contract Mapping:</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Overview:</strong> Consumes <code>ranking_summary.json</code> for aggregates.</li>
            <li><strong>Ranking:</strong> Consumes <code>organisation_scores.json</code> for tabular listing.</li>
            <li><strong>Details:</strong> Consumes <code>sample_dataset.json</code> and scores.</li>
            <li><strong>Models:</strong> Consumes <code>comparison_summary.json</code>.</li>
            <li><strong>Versions:</strong> Consumes <code>version_registry.json</code>.</li>
            <li><strong>Tests:</strong> Consumes <code>test_report.json</code>.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Architecture;
