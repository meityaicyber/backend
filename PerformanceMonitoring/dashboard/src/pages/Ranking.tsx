import React, { useEffect, useState } from 'react';
import { loadOrganisationScores, OrganisationScore } from '../data/Loaders';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';

const Ranking = () => {
  const [scores, setScores] = useState<OrganisationScore[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadOrganisationScores()
      .then(setScores)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!scores.length) return <div className="p-8">Loading authoritative ranking...</div>;

  const filtered = scores.filter(s => {
    if (search && !s.organisation_id.toLowerCase().includes(search.toLowerCase())) return false;
    if (filter === 'renewed' && s.renewal_prediction?.class !== 'renewed') return false;
    if (filter === 'not_renewed' && s.renewal_prediction?.class !== 'not_renewed') return false;
    if (filter === 'borderline' && s.renewal_prediction?.boundary_status !== 'close_to_decision_boundary') return false;
    if (filter === 'not_assessable' && s.assessment_status !== 'not_assessable') return false;
    return true;
  });

  return (
    <div className="p-8">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organisation Ranking</h1>
          <p className="text-gray-500">Authoritative ordering from backend</p>
        </div>
        
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search ID..." 
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-md text-sm w-64"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            className="border border-gray-300 rounded-md text-sm px-3 py-2"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Outcomes</option>
            <option value="renewed">Renewed Only</option>
            <option value="not_renewed">Not Renewed Only</option>
            <option value="borderline">Borderline Cases</option>
            <option value="not_assessable">Not Assessable</option>
          </select>
        </div>
      </header>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-600 font-medium border-b border-gray-200">
            <tr>
              <th className="px-6 py-3">Rank</th>
              <th className="px-6 py-3">Organisation ID</th>
              <th className="px-6 py-3">Score</th>
              <th className="px-6 py-3">Prediction</th>
              <th className="px-6 py-3">Probability</th>
              <th className="px-6 py-3">Boundary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.slice(0, 500).map(s => (
              <tr key={s.organisation_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 font-mono">{s.rank ?? '-'}</td>
                <td className="px-6 py-4">
                  <Link to={`/org/${s.organisation_id}`} className="text-blue-600 hover:underline font-medium">
                    {s.organisation_id}
                  </Link>
                </td>
                <td className="px-6 py-4">{s.performance_score.toFixed(2)}</td>
                <td className="px-6 py-4">
                  {s.assessment_status === 'not_assessable' ? (
                    <span className="px-2 py-1 rounded bg-gray-100 text-gray-600 text-xs">N/A</span>
                  ) : (
                    <span className={`px-2 py-1 rounded text-xs ${s.renewal_prediction?.class === 'renewed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {s.renewal_prediction?.class.toUpperCase()}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">{s.renewal_prediction?.probability.toFixed(3) ?? '-'}</td>
                <td className="px-6 py-4">
                  {s.renewal_prediction?.boundary_status === 'close_to_decision_boundary' && (
                    <span className="px-2 py-1 rounded bg-amber-100 text-amber-700 text-xs">Borderline</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length > 500 && (
          <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 border-t border-gray-100">
            Showing top 500 results of {filtered.length}. Use search to narrow down.
          </div>
        )}
      </div>
    </div>
  );
};

export default Ranking;
