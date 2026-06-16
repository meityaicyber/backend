import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Skeleton,
} from '@mui/material';
import {
  Description,
  People,
  CheckCircle,
  Warning,
  CloudUpload,
  TrendingUp,
} from '@mui/icons-material';
import api from '../api/axios';

const statusColor = {
  UPLOADED: 'info',
  VALIDATED: 'success',
  REJECTED: 'error',
  QUARANTINED: 'warning',
};

function StatCard({ title, value, icon, color, delay }) {
  return (
    <Card
      className="fade-in-up"
      sx={{
        animationDelay: `${delay}ms`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5, fontWeight: 500 }}>
              {title}
            </Typography>
            <Typography variant="h3" fontWeight={800} sx={{ color }}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              background: `${color}15`,
              display: 'flex',
            }}
          >
            {React.cloneElement(icon, { sx: { fontSize: 28, color } })}
          </Box>
        </Box>
      </CardContent>
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 3,
          background: `linear-gradient(90deg, ${color}, transparent)`,
        }}
      />
    </Card>
  );
}

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/api/dashboard/stats');
        setStats(response.data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rounded" height={120} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rounded" height={300} sx={{ borderRadius: 3 }} />
      </Box>
    );
  }

  const validatedCount = stats?.reports_by_status?.VALIDATED || 0;
  const rejectedCount = stats?.reports_by_status?.REJECTED || 0;

  return (
    <Box>
      <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
        Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Overview of your cybersecurity audit reports
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Reports"
            value={stats?.total_reports || 0}
            icon={<Description />}
            color="#00D4FF"
            delay={0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={stats?.total_users || 0}
            icon={<People />}
            color="#7C4DFF"
            delay={100}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Validated"
            value={validatedCount}
            icon={<CheckCircle />}
            color="#00E676"
            delay={200}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Rejected"
            value={rejectedCount}
            icon={<Warning />}
            color="#FF1744"
            delay={300}
          />
        </Grid>
      </Grid>

      {/* Recent Uploads */}
      <Card className="fade-in-up" sx={{ animationDelay: '400ms' }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ p: 3, pb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <CloudUpload sx={{ color: '#00D4FF' }} />
              <Typography variant="h6" fontWeight={700}>
                Recent Uploads
              </Typography>
            </Box>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Filename</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {stats?.recent_uploads?.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">No reports uploaded yet</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  stats?.recent_uploads?.map((report) => (
                    <TableRow
                      key={report.report_id}
                      sx={{
                        transition: 'background 0.2s',
                        '&:hover': { backgroundColor: 'rgba(0,212,255,0.03)' },
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={500} noWrap sx={{ maxWidth: 300 }}>
                          {report.original_filename}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {(report.file_size / 1024).toFixed(1)} KB
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={report.upload_status}
                          color={statusColor[report.upload_status] || 'default'}
                          size="small"
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(report.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

export default DashboardPage;
