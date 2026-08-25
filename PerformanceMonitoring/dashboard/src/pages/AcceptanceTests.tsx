import React, { useEffect, useState } from 'react';
import { loadTestReport, TestReport } from '../data/Loaders';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

const AcceptanceTests = () => {
  const [report, setReport] = useState<TestReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTestReport()
      .then(setReport)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!report) return <div className="p-8">Loading authoritative test report...</div>;

  const passed = report.summary.passed || 0;
  const failed = report.summary.failed || 0;
  const total = report.summary.total || 0;

  return (
    <div className="p-8 max-w-5xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Acceptance Tests</h1>
        <p className="text-gray-500">Automated machine-generated test execution report</p>
      </header>

      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 mb-1">Total Tests</div>
          <div className="text-3xl font-bold">{total}</div>
        </div>
        <div className="bg-green-50 p-6 rounded-lg border border-green-100">
          <div className="text-sm font-medium text-green-800 mb-1">Passed</div>
          <div className="text-3xl font-bold text-green-900">{passed}</div>
        </div>
        <div className={`p-6 rounded-lg border ${failed > 0 ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100'}`}>
          <div className={`text-sm font-medium mb-1 ${failed > 0 ? 'text-red-800' : 'text-gray-500'}`}>Failed</div>
          <div className={`text-3xl font-bold ${failed > 0 ? 'text-red-900' : 'text-gray-900'}`}>{failed}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 mb-1">Execution Time</div>
          <div className="text-3xl font-bold">{(report.summary.duration || 0).toFixed(2)}s</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Test Cases</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {report.tests.map(test => {
            const isPass = test.outcome === 'passed';
            return (
              <div key={test.nodeid} className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {isPass ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                    <h3 className="font-semibold text-gray-900">{test.nodeid.split('::').pop()}</h3>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Clock className="w-4 h-4" /> {(test.call?.duration || 0).toFixed(3)}s
                  </div>
                </div>
                {!isPass && test.call?.crash && (
                  <div className="mt-3 bg-red-50 border border-red-100 p-4 rounded text-sm text-red-900 font-mono whitespace-pre-wrap overflow-x-auto">
                    {test.call.crash.message}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AcceptanceTests;
