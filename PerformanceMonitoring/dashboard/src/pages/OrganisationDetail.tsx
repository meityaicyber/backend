import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { loadOrganisationScores, loadDataset, OrganisationScore, Dataset } from '../data/Loaders';
import { ArrowLeft, AlertCircle } from 'lucide-react';

const OrganisationDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [scoreData, setScoreData] = useState<OrganisationScore | null>(null);
  const [featureData, setFeatureData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadOrganisationScores(), loadDataset()])
      .then(([scores, dataset]) => {
        const s = scores.find(x => x.organisation_id === id);
        const f = dataset.data.find(x => x.organisation_id === id);
        
        if (!s || !f) throw new Error("Organisation not found");
        setScoreData(s);
        setFeatureData(f);
      })
      .catch(err => setError(err.message));
  }, [id]);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!scoreData || !featureData) return <div className="p-8">Loading details...</div>;

  return (
    <div className="p-8 max-w-5xl">
      <Link to="/ranking" className="flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 mb-6 w-fit">
        <ArrowLeft className="w-4 h-4" /> Back to Ranking
      </Link>

      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">{scoreData.organisation_id}</h1>
          <p className="text-gray-500">Organisation Inspection View</p>
        </div>
        
        {scoreData.assessment_status === 'not_assessable' ? (
          <div className="px-4 py-2 bg-red-100 text-red-800 rounded-lg flex items-center gap-2 font-medium">
            <AlertCircle className="w-5 h-5" /> Not Assessable
          </div>
        ) : (
          <div className="text-right">
            <div className="text-sm text-gray-500 font-medium">Authoritative Rank</div>
            <div className="text-4xl font-bold text-blue-600">#{scoreData.rank}</div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">Raw Feature Data</h2>
          </div>
          <div className="p-6 space-y-4">
            {Object.entries(featureData.features).map(([key, val]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm font-medium text-gray-600 capitalize">
                  {key.replace(/_/g, ' ')}
                  {scoreData.missing_features.includes(key) && (
                    <span className="ml-2 text-xs text-red-500 bg-red-50 px-1 py-0.5 rounded border border-red-100">MISSING</span>
                  )}
                </span>
                <span className="text-sm font-mono text-gray-900">
                  {val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800">Prediction & Score</h2>
            </div>
            <div className="p-6 grid grid-cols-2 gap-6">
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Score</div>
                <div className="text-2xl font-bold">{scoreData.performance_score.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Outcome</div>
                <div className="text-xl font-bold">
                  {scoreData.renewal_prediction?.class.toUpperCase() || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Probability</div>
                <div className="text-lg font-medium">{scoreData.renewal_prediction?.probability.toFixed(3) || 'N/A'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Boundary Status</div>
                <div className="text-sm font-medium">
                  {scoreData.renewal_prediction?.boundary_status === 'close_to_decision_boundary' 
                    ? <span className="text-amber-600">Borderline</span> 
                    : <span className="text-green-600">Normal</span>}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800">Provenance</h2>
            </div>
            <div className="p-6">
              <div className="space-y-3 text-sm">
                {Object.entries(scoreData.provenance).map(([key, val]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-500">{key.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-gray-900">{val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-100 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-2">Explain Score</h2>
        <p className="text-sm text-blue-800 mb-4">
          This section surfaces the score derivation exactly as calculated by the backend. No secondary scoring engine is used here. 
          The score shown ({scoreData.performance_score.toFixed(2)}) is mathematically composed of the features displayed above, 
          normalized according to <code>{scoreData.provenance.scoring_config_version}</code>.
        </p>
        {scoreData.missing_features.length > 0 && (
          <p className="text-sm text-blue-800 font-medium">
            Note: Feature(s) {scoreData.missing_features.join(', ')} were missing. Weights were proportionally renormalized 
            across the remaining features to achieve a sum of 1.0.
          </p>
        )}
      </div>
    </div>
  );
};

export default OrganisationDetail;
