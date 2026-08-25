import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Activity, BarChart2, ShieldAlert, FileText, Database, GitCommit, LayoutTemplate } from 'lucide-react';
import Overview from './pages/Overview';
import Ranking from './pages/Ranking';
import OrganisationDetail from './pages/OrganisationDetail';
import ModelComparison from './pages/ModelComparison';
import DataQuality from './pages/DataQuality';
import Versions from './pages/Versions';
import AcceptanceTests from './pages/AcceptanceTests';
import Architecture from './pages/Architecture';

const App = () => {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 text-gray-900">
        <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Activity className="text-blue-600" />
              PerfMon
            </h1>
            <p className="text-xs text-gray-500 mt-1">AI Agent Dashboard</p>
          </div>
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <NavLink to="/" icon={<BarChart2 />} label="Overview" />
            <NavLink to="/ranking" icon={<Database />} label="Ranking" />
            <NavLink to="/models" icon={<Activity />} label="Model Comparison" />
            <NavLink to="/quality" icon={<ShieldAlert />} label="Data Quality" />
            <NavLink to="/versions" icon={<GitCommit />} label="Version History" />
            <NavLink to="/tests" icon={<FileText />} label="Acceptance Tests" />
            <NavLink to="/architecture" icon={<LayoutTemplate />} label="Architecture" />
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/ranking" element={<Ranking />} />
            <Route path="/org/:id" element={<OrganisationDetail />} />
            <Route path="/models" element={<ModelComparison />} />
            <Route path="/quality" element={<DataQuality />} />
            <Route path="/versions" element={<Versions />} />
            <Route path="/tests" element={<AcceptanceTests />} />
            <Route path="/architecture" element={<Architecture />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

const NavLink = ({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) => (
  <Link
    to={to}
    className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors text-sm font-medium"
  >
    {React.cloneElement(icon as React.ReactElement<any>, { className: 'w-5 h-5 text-gray-500' })}
    {label}
  </Link>
);

export default App;
