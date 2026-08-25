import React, { useEffect, useState } from 'react';
import { loadRankingSummary, RankingSummary, loadOrganisationScores, OrganisationScore } from '../data/Loaders';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Overview = () => {
  const [summary, setSummary] = useState<RankingSummary | null>(null);
  const [scores, setScores] = useState<OrganisationScore[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadRankingSummary(), loadOrganisationScores()])
      .then(([summaryData, scoresData]) => {
        setSummary(summaryData);
        setScores(scoresData);
      })
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!summary) return <div className="p-8">Loading authoritative data...</div>;

  const validScores = scores.filter(s => s.assessment_status === 'assessable');
  const avgScore = validScores.reduce((acc, s) => acc + s.performance_score, 0) / validScores.length;
  
  const renewedCount = validScores.filter(s => s.renewal_prediction?.class === 'renewed').length;
  const notRenewedCount = validScores.length - renewedCount;
  const borderlineCount = validScores.filter(s => s.renewal_prediction?.boundary_status === 'close_to_decision_boundary').length;
  const notAssessableCount = scores.length - validScores.length;

  const pieData = [
    { name: 'Renewed', value: renewedCount, color: '#3b82f6' },
    { name: 'Not Renewed', value: notRenewedCount, color: '#ef4444' },
  ];

  // Score distribution bins
  const bins = Array(10).fill(0);
  validScores.forEach(s => {
    const binIndex = Math.min(Math.floor(s.performance_score / 10), 9);
    bins[binIndex]++;
  });
  const distData = bins.map((count, i) => ({
    range: `${i * 10}-${i * 10 + 9}`,
    count,
  }));

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Executive Overview</h1>
        <p className="text-gray-500">Read-only presentation of Performance Monitoring outputs</p>
      </header>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Organisations" value={summary.metadata.total_organisations} />
        <StatCard title="Assessable" value={summary.metadata.assessable_organisations} />
        <StatCard title="Average Score" value={avgScore.toFixed(1)} />
        <StatCard title="Not Assessable" value={notAssessableCount} className="border-red-200 bg-red-50 text-red-700" />
      </div>

      <div className="grid grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Renewal Prediction Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} label>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center mt-2 text-sm text-gray-500">
            Borderline Cases: <span className="font-medium text-amber-600">{borderlineCount}</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Score Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distData}>
                <XAxis dataKey="range" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold mb-4">Provenance Metadata</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          {Object.entries(summary.metadata.provenance).map(([key, val]) => (
            <div key={key} className="flex justify-between py-2 border-b border-gray-50 last:border-0">
              <span className="text-gray-500 font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
              <span className="font-mono text-gray-900">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, className = 'bg-white border-gray-100' }: { title: string; value: string | number; className?: string }) => (
  <div className={`p-6 rounded-lg shadow-sm border ${className}`}>
    <h3 className="text-sm font-medium opacity-80 mb-1">{title}</h3>
    <div className="text-3xl font-bold">{value}</div>
  </div>
);

export default Overview;
