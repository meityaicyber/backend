import React, { useEffect, useState } from 'react';
import { loadOrganisationScores, OrganisationScore } from '../data/Loaders';
import { Link } from 'react-router-dom';

const DataQuality = () => {
  const [scores, setScores] = useState<OrganisationScore[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOrganisationScores()
      .then(setScores)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!scores.length) return <div className="p-8">Loading authoritative data...</div>;

  const total = scores.length;
  const notAssessable = scores.filter(s => s.assessment_status === 'not_assessable');
  const missingCount = scores.filter(s => s.missing_features.length > 0).length;

  const featureMissingMap: Record<string, number> = {};
  scores.forEach(s => {
    s.missing_features.forEach(f => {
      featureMissingMap[f] = (featureMissingMap[f] || 0) + 1;
    });
  });

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Data Quality & Irregularity Inspection</h1>
        <p className="text-gray-500">Overview of sparse history, missing values, and unassessable records</p>
      </header>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 mb-1">Total Records Processed</div>
          <div className="text-3xl font-bold">{total}</div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-amber-600 mb-1">Incomplete Records (Processed)</div>
          <div className="text-3xl font-bold">{missingCount - notAssessable.length}</div>
          <div className="text-xs text-gray-500 mt-2">Missing &lt;= 2 features, weights re-normalized</div>
        </div>
        <div className="bg-red-50 p-6 rounded-lg border border-red-100">
          <div className="text-sm font-medium text-red-800 mb-1">Not Assessable (Rejected)</div>
          <div className="text-3xl font-bold text-red-900">{notAssessable.length}</div>
          <div className="text-xs text-red-700 mt-2">Missing &gt; 2 features</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Missingness by Feature</h2>
        </div>
        <div className="p-6">
          {Object.entries(featureMissingMap).sort((a,b) => b[1] - a[1]).map(([feature, count]) => (
            <div key={feature} className="flex items-center mb-4 last:mb-0">
              <div className="w-48 text-sm font-medium text-gray-700 capitalize">{feature.replace(/_/g, ' ')}</div>
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden mx-4">
                <div 
                  className="bg-amber-400 h-full rounded-full" 
                  style={{ width: `${Math.max(0.5, (count / total) * 100)}%` }}
                />
              </div>
              <div className="w-16 text-right text-sm text-gray-500">{((count/total)*100).toFixed(1)}%</div>
            </div>
          ))}
          {Object.keys(featureMissingMap).length === 0 && (
            <div className="text-gray-500 italic">No missing features in dataset.</div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Unassessable Organisations Log</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-200">
            <tr>
              <th className="px-6 py-3">Organisation ID</th>
              <th className="px-6 py-3">Missing Feature Count</th>
              <th className="px-6 py-3">Missing Features</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {notAssessable.slice(0, 50).map(s => (
              <tr key={s.organisation_id}>
                <td className="px-6 py-4">
                  <Link to={`/org/${s.organisation_id}`} className="text-blue-600 hover:underline font-medium">
                    {s.organisation_id}
                  </Link>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 rounded-full bg-red-100 text-red-800 text-xs font-bold">
                    {s.missing_features.length}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-500">{s.missing_features.join(', ')}</td>
              </tr>
            ))}
            {notAssessable.length === 0 && (
              <tr>
                <td colSpan={3} className="px-6 py-8 text-center text-gray-500 italic">
                  No organisations were rejected for missing data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataQuality;
