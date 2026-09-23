import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { Box, CircularProgress } from '@mui/material';

import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleGuard from './components/RoleGuard';
import BulkProgressWidget from './components/BulkProgressWidget';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UploadReportPage from './pages/UploadReportPage';
import ReportsPage from './pages/ReportsPage';
import ReportDetailPage from './pages/ReportDetailPage';
import UserManagementPage from './pages/UserManagementPage';
import AgencyManagementPage from './pages/AgencyManagementPage';
import AuditLogsPage from './pages/AuditLogsPage';
import ProfilePage from './pages/ProfilePage';
import AnalyticsDashboardPage from './pages/AnalyticsDashboardPage';
import MLAnalyticsDashboardPage from './pages/MLAnalyticsDashboardPage';

function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          background: '#0A0E17',
        }}
      >
        <CircularProgress sx={{ color: '#00D4FF' }} size={48} />
      </Box>
    );
  }

  return (
    <>
      <div className="cyber-grid"></div>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadReportPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/:id" element={<ReportDetailPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/analytics" element={<AnalyticsDashboardPage />} />
            <Route path="/ml-analytics" element={<MLAnalyticsDashboardPage />} />
            <Route
              path="/users"
              element={
                <RoleGuard roles={['ADMIN']}>
                  <UserManagementPage />
                </RoleGuard>
              }
            />
            <Route
              path="/agencies"
              element={
                <RoleGuard roles={['ADMIN']}>
                  <AgencyManagementPage />
                </RoleGuard>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <RoleGuard roles={['ADMIN']}>
                  <AuditLogsPage />
                </RoleGuard>
              }
            />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <BulkProgressWidget />
    </>
  );
}

export default App;
