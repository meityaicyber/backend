import React, { useEffect, useState } from 'react';
import { loadVersionRegistry, VersionRegistry } from '../data/Loaders';
import { History, ShieldCheck } from 'lucide-react';

const Versions = () => {
  const [registry, setRegistry] = useState<VersionRegistry | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadVersionRegistry()
      .then(setRegistry)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="p-8 text-red-600">Error loading data: {error}</div>;
  if (!registry) return <div className="p-8">Loading authoritative versions...</div>;

  return (
    <div className="p-8 max-w-5xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Configuration & Version History</h1>
        <p className="text-gray-500">Immutable governance record of schema and scoring changes</p>
      </header>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8 overflow-hidden">
        <div className="bg-blue-50 border-b border-blue-100 px-6 py-4 flex items-center gap-2 text-blue-900 font-semibold">
          <ShieldCheck className="w-5 h-5" /> Current Active Versions
        </div>
        <div className="p-6 grid grid-cols-2 md:grid-cols-3 gap-6">
          {Object.entries(registry.current_versions).map(([component, version]) => (
            <div key={component} className="border border-gray-100 p-4 rounded bg-gray-50">
              <div className="text-xs text-gray-500 font-medium uppercase mb-1">{component.replace(/_/g, ' ')}</div>
              <div className="text-xl font-bold text-gray-900 font-mono">v{version}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 flex items-center gap-2 text-gray-800 font-semibold">
          <History className="w-5 h-5 text-gray-500" /> Immutable Change Log
        </div>
        <div className="p-6">
          {registry.history.length === 0 ? (
            <div className="text-gray-500 italic text-center py-4">No historical changes recorded.</div>
          ) : (
            <div className="space-y-8">
              {[...registry.history].reverse().map((entry, idx) => (
                <div key={idx} className="relative pl-6 border-l-2 border-blue-200">
                  <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-[7px] top-1.5 border-2 border-white"></div>
                  <div className="text-sm text-gray-500 mb-1">{new Date(entry.timestamp).toLocaleString()}</div>
                  <div className="text-lg font-medium text-gray-900 mb-2">{entry.change}</div>
                  <div className="text-sm text-gray-600 mb-3">Approved by: <span className="font-semibold text-gray-800">{entry.approver}</span></div>
                  
                  {entry.updated_components.length > 0 && (
                    <div className="bg-gray-50 rounded border border-gray-200 p-3 text-sm font-mono overflow-x-auto">
                      <table className="w-full text-left">
                        <thead>
                          <tr className="text-gray-500 border-b border-gray-200">
                            <th className="pb-2 font-medium">Component</th>
                            <th className="pb-2 font-medium">Old Version</th>
                            <th className="pb-2 font-medium">New Version</th>
                          </tr>
                        </thead>
                        <tbody>
                          {entry.updated_components.map(comp => (
                            <tr key={comp.component}>
                              <td className="py-2">{comp.component}</td>
                              <td className="py-2 text-gray-500 line-through">v{comp.old_version}</td>
                              <td className="py-2 text-green-600 font-bold">v{comp.new_version}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Versions;
