import React, { useEffect, useState } from 'react';
import { loadModelComparison, ModelComparison as ModelCompType } from '../data/Loaders';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

const ModelComparison = () => {
  const [metrics, setMetrics] = useState<ModelCompType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadModelComparison()
      .then(setMetrics)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!metrics) return <div className="p-8">Loading authoritative metrics...</div>;

  const chartData = Object.entries(metrics).map(([model, data]) => ({
    name: model.replace(/_/g, ' ').toUpperCase(),
    accuracy: Number(data.accuracy.toFixed(3)),
    macro_f1: Number(data.macro_f1.toFixed(3)),
    isProduction: model === 'gradient_boosting' // Configured as production in backend
  }));

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Model Comparison</h1>
        <p className="text-gray-500">Authoritative evaluation results generated during pipeline execution</p>
      </header>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <h2 className="text-lg font-semibold mb-6 text-gray-800">Performance Metrics</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
              <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} dy={10} />
              <YAxis domain={[0, 1]} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
              <Tooltip cursor={{ fill: '#f9fafb' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar dataKey="accuracy" name="Accuracy" fill="#93c5fd" radius={[4, 4, 0, 0]} />
              <Bar dataKey="macro_f1" name="Macro F1 Score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {chartData.map(m => (
          <div key={m.name} className={`p-6 rounded-lg border ${m.isProduction ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200 shadow-sm'}`}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{m.name}</h3>
              {m.isProduction && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase tracking-wider">
                  Production Model
                </span>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Macro F1</div>
                <div className="text-2xl font-bold">{m.macro_f1.toFixed(3)}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Accuracy</div>
                <div className="text-2xl font-bold">{m.accuracy.toFixed(3)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelComparison;
