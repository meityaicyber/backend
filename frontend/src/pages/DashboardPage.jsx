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
  Button,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  Description,
  People,
  CheckCircle,
  Warning,
  CloudUpload,
  TrendingUp,
  Storage,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid
} from 'recharts';
import api from '../api/axios';

const statusColor = {
  UPLOADED: 'info',
  VALIDATED: 'success',
  REJECTED: 'error',
  QUARANTINED: 'warning',
};

function formatBytes(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function AnimatedNumber({ value, duration = 1200 }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value == null) return;
    const target = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(target)) {
      setDisplay(value);
      return;
    }
    let start = 0;
    const startTime = performance.now();
    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target * 10) / 10;
      setDisplay(Number.isInteger(target) ? Math.round(eased * target) : current);
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }, [value, duration]);

  return <>{display}</>;
}

function StatCard({ title, value, icon, color, delay, isString = false }) {
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
              {isString ? value : <AnimatedNumber value={value} />}
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
  const navigate = useNavigate();
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
  const uploadedCount = stats?.reports_by_status?.UPLOADED || 0;
  const quarantinedCount = stats?.reports_by_status?.QUARANTINED || 0;

  const pieChartData = [
    { name: 'Validated', value: validatedCount, color: '#00E676' },
    { name: 'Rejected', value: rejectedCount, color: '#FF1744' },
    { name: 'Uploaded', value: uploadedCount, color: '#00D4FF' },
    { name: 'Quarantined', value: quarantinedCount, color: '#FF9100' },
  ].filter(item => item.value > 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Overview of your cybersecurity audit reports
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={() => navigate('/bulk-upload')}
          sx={{
            background: 'linear-gradient(45deg, #00D4FF 30%, #7C4DFF 90%)',
            boxShadow: '0 3px 5px 2px rgba(124, 77, 255, .3)',
            color: 'white',
            fontWeight: 'bold',
            borderRadius: 2,
            px: 3,
            py: 1
          }}
        >
          Upload Report
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Total Reports"
            value={stats?.total_reports || 0}
            icon={<Description />}
            color="#00D4FF"
            delay={0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Total Storage"
            value={formatBytes(stats?.total_storage || 0)}
            icon={<Storage />}
            color="#E040FB"
            delay={50}
            isString={true}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Validated"
            value={validatedCount}
            icon={<CheckCircle />}
            color="#00E676"
            delay={100}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Quarantined"
            value={quarantinedCount}
            icon={<Warning />}
            color="#FF9100"
            delay={150}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Rejected"
            value={rejectedCount}
            icon={<Warning />}
            color="#FF1744"
            delay={200}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Total Users"
            value={stats?.total_users || 0}
            icon={<People />}
            color="#7C4DFF"
            delay={250}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Charts Section */}
        <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Card className="fade-in-up" sx={{ animationDelay: '400ms', flex: 1 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 3 }}>
                Reports by Status
              </Typography>
              <Box sx={{ height: 220, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {pieChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={70}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: '#1E1E1E', border: 'none', borderRadius: '8px' }}
                        itemStyle={{ color: '#fff' }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <Typography color="text.secondary">No report data available</Typography>
                )}
              </Box>
            </CardContent>
          </Card>
          
          <Card className="fade-in-up" sx={{ animationDelay: '500ms', flex: 1 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 3 }}>
                Upload Trend (7 Days)
              </Typography>
              <Box sx={{ height: 220 }}>
                {stats?.upload_trend?.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={stats.upload_trend}>
                      <defs>
                        <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" tick={{fontSize: 10}} tickMargin={10} axisLine={false} tickLine={false} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: '#1E1E1E', border: 'none', borderRadius: '8px' }}
                        itemStyle={{ color: '#00D4FF' }}
                      />
                      <Area type="monotone" dataKey="count" stroke="#00D4FF" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <Typography color="text.secondary">No trend data available</Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>


        {/* Recent Uploads */}
        <Grid item xs={12} md={8}>
          <Card className="fade-in-up" sx={{ animationDelay: '500ms', height: '100%' }}>
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
        </Grid>
      </Grid>
    </Box>
  );
}

export default DashboardPage;
