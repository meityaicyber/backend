import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Skeleton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  alpha,
  useTheme,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  OutlinedInput,
  Button,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  BugReport,
  ErrorOutline,
  CheckCircleOutline,
  Speed,
  Shield,
  Assessment,
  TrendingUp,
  Category,
  Layers,
  Repeat,
  Storage,
  GppBad,
  Download,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import api from '../api/axios';

/* ─────────────────────── Color Palettes ─────────────────────── */
const SEVERITY_COLORS = {
  CRITICAL: '#FF1744',
  HIGH: '#FF9100',
  MEDIUM: '#FFD600',
  LOW: '#00E676',
  INFORMATIONAL: '#7C4DFF',
};

const STATUS_COLORS = {
  OPEN: '#FF1744',
  CLOSED: '#00E676',
  ACCEPTED: '#7C4DFF',
  RISK_ACCEPTED: '#FF9100',
  IN_PROGRESS: '#00D4FF',
};

const ENUM_LABELS = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
  INFORMATIONAL: 'Informational',
  OPEN: 'Open',
  CLOSED: 'Closed',
  ACCEPTED: 'Accepted',
  RISK_ACCEPTED: 'Risk Accepted',
  IN_PROGRESS: 'In Progress',
};

function formatEnumLabel(label) {
  if (!label) return 'N/A';
  return ENUM_LABELS[label] || label;
}

const CHART_COLORS = [
  '#00D4FF',
  '#7C4DFF',
  '#FF9100',
  '#00E676',
  '#FF1744',
  '#FFD600',
  '#E040FB',
  '#18FFFF',
  '#FF6E40',
  '#76FF03',
  '#448AFF',
  '#FFAB40',
  '#FF4081',
  '#69F0AE',
  '#B388FF',
];

/* ─────────────────── Custom Recharts Tooltip ─────────────────── */
function GlassTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <Box
      sx={{
        backgroundColor: 'rgba(17, 24, 39, 0.92)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 2,
        px: 2,
        py: 1.2,
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}
    >
      {label && (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
          {label}
        </Typography>
      )}
      {payload.map((entry, idx) => (
        <Typography key={idx} variant="body2" sx={{ color: entry.color || '#E2E8F0', fontWeight: 600 }}>
          {formatEnumLabel(entry.name)}: {entry.value}
        </Typography>
      ))}
    </Box>
  );
}

/* ─────────────────── Animated Counter ─────────────────── */
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

/* ─────────────────── KPI Stat Card ─────────────────── */
function KpiCard({ title, value, icon, color, delay = 0 }) {
  return (
    <Card
      className="fade-in-up"
      sx={{
        animationDelay: `${delay}ms`,
        position: 'relative',
        overflow: 'hidden',
        minHeight: 130,
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography
              variant="caption"
              sx={{ color: 'text.secondary', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.68rem' }}
            >
              {title}
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 800, color, mt: 0.5 }}>
              <AnimatedNumber value={value} />
            </Typography>
          </Box>
          <Box
            sx={{
              p: 1.2,
              borderRadius: 2,
              background: alpha(color, 0.12),
              display: 'flex',
            }}
          >
            {React.cloneElement(icon, { sx: { fontSize: 26, color } })}
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

/* ─────────────────── Chart Card Wrapper ─────────────────── */
function ChartCard({ title, icon, children, delay = 0, sx: sxProp = {} }) {
  return (
    <Card className="fade-in-up" sx={{ animationDelay: `${delay}ms`, height: '100%', ...sxProp }}>
      <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 2.5 }}>
          {icon && React.cloneElement(icon, { sx: { color: '#00D4FF', fontSize: 22 } })}
          <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1rem' }}>
            {title}
          </Typography>
        </Box>
        <Box sx={{ flex: 1, minHeight: 0 }}>{children}</Box>
      </CardContent>
    </Card>
  );
}

/* ─────────────────── Severity Badge ─────────────────── */
function SeverityBadge({ severity }) {
  const color = SEVERITY_COLORS[severity] || '#94A3B8';
  return (
    <Chip
      label={formatEnumLabel(severity)}
      size="small"
      sx={{
        fontWeight: 600,
        fontSize: '0.7rem',
        backgroundColor: alpha(color, 0.15),
        color,
        border: `1px solid ${alpha(color, 0.3)}`,
      }}
    />
  );
}

/* ─────────────────── Status Badge ─────────────────── */
function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || '#94A3B8';
  return (
    <Chip
      label={formatEnumLabel(status)}
      size="small"
      sx={{
        fontWeight: 600,
        fontSize: '0.7rem',
        backgroundColor: alpha(color, 0.12),
        color,
        border: `1px solid ${alpha(color, 0.25)}`,
      }}
    />
  );
}

/* ─────────────────── Pie / Donut Label ─────────────────── */
function renderDonutLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#E2E8F0" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE COMPONENT
   ═══════════════════════════════════════════════════════════════ */
export default function AnalyticsDashboardPage() {
  const [viewMode, setViewMode] = useState('GLOBAL');
  const [selectedAgencyId, setSelectedAgencyId] = useState('');
  const [selectedFileId, setSelectedFileId] = useState('');
  const [selectedSeverities, setSelectedSeverities] = useState([]);
  const [selectedStatuses, setSelectedStatuses] = useState([]);
  const [timeRange, setTimeRange] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [chartFilter, setChartFilter] = useState({ key: null, value: null });
  const [agencies, setAgencies] = useState([]);
  const [files, setFiles] = useState([]);
  const [allVulnerabilities, setAllVulnerabilities] = useState([]);

  const handleChartClick = (key, value) => {
    if (chartFilter.key === key && chartFilter.value === value) {
      setChartFilter({ key: null, value: null });
    } else {
      setChartFilter({ key, value });
    }
  };

  const handleExportCsv = () => {
    if (!tableVulns || tableVulns.length === 0) return;

    const headers = ['ID', 'Title', 'Severity', 'Status', 'CVSS', 'Date Found', 'Category', 'CWE', 'CVE', 'Asset', 'New or Repeat'];
    const escapeCsv = (str) => {
      if (str == null) return '';
      const text = String(str).replace(/"/g, '""');
      return `"${text}"`;
    };

    const rows = tableVulns.map(v => [
      escapeCsv(v.id),
      escapeCsv(v.title),
      escapeCsv(v.severity),
      escapeCsv(v.status),
      escapeCsv(v.cvss),
      escapeCsv(new Date(v.date).toLocaleDateString()),
      escapeCsv(v.category),
      escapeCsv(v.cwe),
      escapeCsv(v.cve),
      escapeCsv(v.asset),
      escapeCsv(v.new_or_repeat)
    ]);

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Security_Analytics_Export_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [agenciesRes, reportsRes, vulnsRes] = await Promise.all([
          api.get('/api/agencies'),
          api.get('/api/reports'),
          api.get('/api/analytics/vulnerabilities')
        ]);
        
        setAgencies((agenciesRes.data.agencies || []).map(a => ({ id: a.agency_id, name: a.agency_name })));
        setFiles((reportsRes.data.reports || []).map(r => ({
          id: r.report_id,
          name: r.original_filename,
          agencyId: r.agency?.agency_id,
          date: r.created_at
        })));
        setAllVulnerabilities(vulnsRes.data.data || []);
      } catch (err) {
        console.error("Failed to fetch analytics data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    setSelectedFileId('');
  }, [selectedAgencyId]);

  const filteredVulnerabilities = useMemo(() => {
    let vulns = [];
    if (viewMode === 'GLOBAL') {
      vulns = allVulnerabilities;
    } else if (viewMode === 'AGENCY') {
      vulns = allVulnerabilities.filter(v => v.agencyId === selectedAgencyId);
    } else if (viewMode === 'FILE') {
      vulns = allVulnerabilities.filter(v => v.fileId === selectedFileId);
    }

    const now = new Date();
    if (timeRange !== 'ALL') {
      const msPerDay = 1000 * 60 * 60 * 24;
      let days = 0;
      if (timeRange === '30_DAYS') days = 30;
      else if (timeRange === '6_MONTHS') days = 180;
      else if (timeRange === '1_YEAR') days = 365;
      const thresholdDate = new Date(now.getTime() - days * msPerDay).toISOString();
      vulns = vulns.filter(v => v.date >= thresholdDate);
    }

    if (selectedSeverities.length > 0) {
      vulns = vulns.filter(v => selectedSeverities.includes(v.severity));
    }
    if (selectedStatuses.length > 0) {
      vulns = vulns.filter(v => selectedStatuses.includes(v.status));
    }

    return vulns;
  }, [allVulnerabilities, viewMode, selectedAgencyId, selectedFileId, timeRange, selectedSeverities, selectedStatuses]);

  const aggregatedData = useMemo(() => {
    const total = filteredVulnerabilities.length;
    let openCount = 0;
    let closedCount = 0;
    let critCount = 0;
    let cvssSum = 0;
    
    const sevCounts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFORMATIONAL: 0 };
    const statCounts = { OPEN: 0, CLOSED: 0, ACCEPTED: 0, RISK_ACCEPTED: 0, IN_PROGRESS: 0 };
    const cvssRanges = Array.from({ length: 10 }, (_, i) => ({ range: `${i}.0-${i + 1}.0`, count: 0 }));
    const countsByMonth = {};
    const catCounts = {};
    const cweCounts = {};
    const cveCounts = {};
    const assetCounts = {};
    const nrCounts = { NEW: 0, REPEAT: 0 };
    
    let reportsSet = new Set();
    if (viewMode === 'GLOBAL') {
      reportsSet = new Set(files.map(f => f.id));
    } else if (viewMode === 'AGENCY') {
      reportsSet = new Set(files.filter(f => f.agencyId === selectedAgencyId).map(f => f.id));
    } else if (viewMode === 'FILE') {
      if (selectedFileId) reportsSet.add(selectedFileId);
    }

    filteredVulnerabilities.forEach(v => {
      if (['OPEN', 'IN_PROGRESS'].includes(v.status)) openCount++;
      if (['CLOSED', 'ACCEPTED', 'RISK_ACCEPTED'].includes(v.status)) closedCount++;
      if (v.severity === 'CRITICAL') critCount++;
      cvssSum += (v.cvss || 0);

      if (sevCounts[v.severity] !== undefined) sevCounts[v.severity]++;
      if (statCounts[v.status] !== undefined) statCounts[v.status]++;
      
      const cvssIdx = Math.min(Math.floor(v.cvss || 0), 9);
      cvssRanges[cvssIdx].count++;

      const d = new Date(v.date);
      const monthStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      countsByMonth[monthStr] = (countsByMonth[monthStr] || 0) + 1;

      catCounts[v.category] = (catCounts[v.category] || 0) + 1;
      cweCounts[v.cwe] = (cweCounts[v.cwe] || 0) + 1;
      cveCounts[v.cve] = (cveCounts[v.cve] || 0) + 1;
      assetCounts[v.asset] = (assetCounts[v.asset] || 0) + 1;

      if (nrCounts[v.new_or_repeat] !== undefined) nrCounts[v.new_or_repeat]++;
    });

    const avgCvss = total > 0 ? (cvssSum / total).toFixed(1) : 0;
    const summary = {
      total_vulnerabilities: total,
      open_vulnerabilities: openCount,
      closed_vulnerabilities: closedCount,
      critical_count: critCount,
      avg_cvss_score: avgCvss,
      reports_with_vulns: reportsSet.size
    };

    const severityDist = Object.entries(sevCounts).map(([severity, count]) => ({ severity, count })).filter(d => d.count > 0);
    const statusDist = Object.entries(statCounts).map(([status, count]) => ({ status, count })).filter(d => d.count > 0);
    const trend = Object.entries(countsByMonth).sort((a, b) => a[0].localeCompare(b[0])).map(([month, count]) => ({ month, count })).slice(-12);
    
    const sortByCount = (obj) => Object.entries(obj).map(([k, count]) => ({ key: k, count })).sort((a, b) => b.count - a.count).slice(0, 5);
    
    const categories = sortByCount(catCounts).map(d => ({ category: d.key, count: d.count }));
    const topCwe = sortByCount(cweCounts).map(d => ({ cwe_id: d.key, count: d.count }));
    const topCve = sortByCount(cveCounts).map(d => ({ cve_id: d.key, count: d.count }));
    const assets = sortByCount(assetCounts).map(d => ({ asset: d.key, count: d.count }));
    
    const newRepeat = Object.entries(nrCounts).map(([type, count]) => ({ type, count })).filter(d => d.count > 0);

    return {
      summary,
      severityDist,
      statusDist,
      cvssDist: cvssRanges,
      trend,
      categories,
      topCwe,
      topCve,
      assets,
      newRepeat
    };
  }, [filteredVulnerabilities, files, viewMode, selectedAgencyId, selectedFileId]);

  const { summary, severityDist, statusDist, cvssDist, trend, categories, topCwe, topCve, assets, newRepeat } = aggregatedData;

  const tableVulns = useMemo(() => {
    let vulns = [...filteredVulnerabilities];
    if (chartFilter.key && chartFilter.value) {
      vulns = vulns.filter(v => v[chartFilter.key] === chartFilter.value);
    }
    return vulns.sort((a, b) => a.date < b.date ? 1 : a.date > b.date ? -1 : 0);
  }, [filteredVulnerabilities, chartFilter]);

  const columns = [
    { field: 'title', headerName: 'Title', flex: 1, minWidth: 200, renderCell: (params) => (
      <Typography variant="body2" fontWeight={500} noWrap sx={{ fontSize: '0.8rem' }}>
        {params.value}
      </Typography>
    )},
    { field: 'severity', headerName: 'Severity', width: 130, renderCell: (params) => <SeverityBadge severity={params.value} /> },
    { field: 'status', headerName: 'Status', width: 130, renderCell: (params) => <StatusBadge status={params.value} /> },
    { field: 'cvss', headerName: 'CVSS', width: 90, type: 'number', renderCell: (params) => (
      <Typography
        variant="body2"
        sx={{
          fontWeight: 700,
          fontSize: '0.8rem',
          color: params.value >= 9 ? '#FF1744' : params.value >= 7 ? '#FF9100' : params.value >= 4 ? '#FFD600' : '#00E676',
        }}
      >
        {params.value != null ? params.value.toFixed(1) : '—'}
      </Typography>
    ) },
    { field: 'date', headerName: 'Date', width: 110, renderCell: (params) => new Date(params.value).toLocaleDateString() },
  ];

  /* ─── Loading skeleton ─── */
  if (loading) {
    return (
      <Box>
        <Skeleton variant="text" width={260} height={42} sx={{ mb: 1 }} />
        <Skeleton variant="text" width={380} height={24} sx={{ mb: 3 }} />
        <Grid container spacing={2.5} sx={{ mb: 3 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={4} lg={2} key={i}>
              <Skeleton variant="rounded" height={130} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
        <Grid container spacing={2.5}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Grid item xs={12} md={6} key={i}>
              <Skeleton variant="rounded" height={340} sx={{ borderRadius: 3 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  const handleTabChange = (event, newValue) => {
    setViewMode(newValue);
    if (newValue === 'GLOBAL') {
      setSelectedAgencyId('');
      setSelectedFileId('');
    }
  };

  const agencyFiles = files.filter(f => f.agencyId === selectedAgencyId);

  return (
    <Box>
      {/* ── Header ── */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3.5 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
            Security Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Vulnerability intelligence across all audited reports
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button 
            variant="contained" 
            startIcon={<Download />}
            onClick={handleExportCsv}
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.05)',
              color: 'text.primary',
              border: '1px solid rgba(255,255,255,0.1)',
              textTransform: 'none',
              fontWeight: 600,
              px: 2,
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 0.1)',
              }
            }}
          >
            Export CSV
          </Button>
          <Box sx={{ bgcolor: 'rgba(17, 24, 39, 0.4)', borderRadius: 2, p: 0.5, border: '1px solid rgba(255,255,255,0.05)' }}>
          <Tabs 
            value={viewMode} 
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            sx={{
              minHeight: 40,
              '& .MuiTab-root': { minHeight: 40, textTransform: 'none', fontWeight: 600, fontSize: '0.85rem' }
            }}
          >
            <Tab label="Global View" value="GLOBAL" />
            <Tab label="Agency View" value="AGENCY" />
            <Tab label="File / Report View" value="FILE" />
          </Tabs>
        </Box>
      </Box>
    </Box>

      {/* ── Filter Controls ── */}
      <Card sx={{ mb: 3.5, background: 'rgba(17, 24, 39, 0.4)', border: '1px solid rgba(255,255,255,0.05)' }}>
        <CardContent sx={{ display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}>
          
          {/* Global Advanced Filters */}
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Time Range</InputLabel>
            <Select value={timeRange} label="Time Range" onChange={(e) => setTimeRange(e.target.value)}>
              <MenuItem value="ALL">All Time</MenuItem>
              <MenuItem value="30_DAYS">Last 30 Days</MenuItem>
              <MenuItem value="6_MONTHS">Last 6 Months</MenuItem>
              <MenuItem value="1_YEAR">Last 1 Year</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Severity Filter</InputLabel>
            <Select
              multiple
              value={selectedSeverities}
              onChange={(e) => setSelectedSeverities(e.target.value)}
              input={<OutlinedInput label="Severity Filter" />}
              renderValue={(selected) => selected.join(', ')}
            >
              {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'].map((sev) => (
                <MenuItem key={sev} value={sev}>
                  <Checkbox checked={selectedSeverities.indexOf(sev) > -1} />
                  <ListItemText primary={sev} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Status Filter</InputLabel>
            <Select
              multiple
              value={selectedStatuses}
              onChange={(e) => setSelectedStatuses(e.target.value)}
              input={<OutlinedInput label="Status Filter" />}
              renderValue={(selected) => selected.join(', ')}
            >
              {['OPEN', 'CLOSED', 'ACCEPTED', 'RISK_ACCEPTED', 'IN_PROGRESS'].map((stat) => (
                <MenuItem key={stat} value={stat}>
                  <Checkbox checked={selectedStatuses.indexOf(stat) > -1} />
                  <ListItemText primary={stat} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Scope Filters */}
          {(viewMode === 'AGENCY' || viewMode === 'FILE') && (
            <>
              <Box sx={{ borderLeft: '1px solid rgba(255,255,255,0.1)', height: 32, mx: 1 }} />
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <InputLabel>Select Agency</InputLabel>
                <Select
                  value={selectedAgencyId}
                  label="Select Agency"
                  onChange={(e) => setSelectedAgencyId(e.target.value)}
                >
                  {agencies.map((agency) => (
                    <MenuItem key={agency.id} value={agency.id}>
                      {agency.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {viewMode === 'FILE' && (
                <FormControl size="small" sx={{ minWidth: 240 }} disabled={!selectedAgencyId}>
                  <InputLabel>Select File / Report</InputLabel>
                  <Select
                    value={selectedFileId}
                    label="Select File / Report"
                    onChange={(e) => setSelectedFileId(e.target.value)}
                  >
                    {agencyFiles.map((file) => (
                      <MenuItem key={file.id} value={file.id}>
                        {file.name} ({new Date(file.date).toLocaleDateString()})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ═══════ KPI SUMMARY CARDS ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 3.5 }}>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Total Vulns"
            value={summary?.total_vulnerabilities ?? 0}
            icon={<BugReport />}
            color="#00D4FF"
            delay={0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Open"
            value={summary?.open_vulnerabilities ?? 0}
            icon={<ErrorOutline />}
            color="#FF1744"
            delay={60}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Closed"
            value={summary?.closed_vulnerabilities ?? 0}
            icon={<CheckCircleOutline />}
            color="#00E676"
            delay={120}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Avg CVSS"
            value={summary?.avg_cvss_score ?? '—'}
            icon={<Speed />}
            color="#FF9100"
            delay={180}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Critical"
            value={summary?.critical_count ?? 0}
            icon={<GppBad />}
            color="#FF1744"
            delay={240}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KpiCard
            title="Reports Analyzed"
            value={summary?.reports_with_vulns ?? 0}
            icon={<Assessment />}
            color="#7C4DFF"
            delay={300}
          />
        </Grid>
      </Grid>

      {/* ═══════ ROW 1 — Severity Donut + Status Pie ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>
        {/* Severity Distribution Donut */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Severity Distribution" icon={<Shield />} delay={350}>
            {severityDist && severityDist.some((d) => d.count > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityDist}
                    dataKey="count"
                    nameKey="severity"
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={110}
                    paddingAngle={3}
                    labelLine={false}
                    label={renderDonutLabel}
                    animationBegin={0}
                    animationDuration={1000}
                    animationEasing="ease-out"
                  >
                    {severityDist.map((entry) => (
                      <Cell 
                        key={entry.severity} 
                        fill={SEVERITY_COLORS[entry.severity] || '#94A3B8'} 
                        stroke="none" 
                        onClick={() => handleChartClick('severity', entry.severity)}
                        style={{ cursor: 'pointer', opacity: chartFilter.value === entry.severity ? 1 : (chartFilter.value ? 0.3 : 1) }}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<GlassTooltip />} />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    iconSize={8}
                    formatter={(val) => <span style={{ color: '#94A3B8', fontSize: 12 }}>{val}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>

        {/* Status Distribution Pie */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Vulnerability Status" icon={<Layers />} delay={400}>
            {statusDist && statusDist.some((d) => d.count > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusDist}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={110}
                    paddingAngle={3}
                    labelLine={false}
                    label={renderDonutLabel}
                    animationBegin={0}
                    animationDuration={1000}
                    animationEasing="ease-out"
                  >
                    {statusDist.map((entry) => (
                      <Cell 
                        key={entry.status} 
                        fill={STATUS_COLORS[entry.status] || '#94A3B8'} 
                        stroke="none" 
                        onClick={() => handleChartClick('status', entry.status)}
                        style={{ cursor: 'pointer', opacity: chartFilter.value === entry.status ? 1 : (chartFilter.value ? 0.3 : 1) }}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<GlassTooltip />} />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    iconSize={8}
                    formatter={(val) => <span style={{ color: '#94A3B8', fontSize: 12 }}>{val}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>
      </Grid>

      {/* ═══════ ROW 2 — CVSS Histogram + Trend ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>
        {/* CVSS Distribution Histogram */}
        <Grid item xs={12} md={6}>
          <ChartCard title="CVSS Score Distribution" icon={<Speed />} delay={450}>
            {cvssDist && cvssDist.some((d) => d.count > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={cvssDist} barSize={28}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="range" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} />
                  <YAxis tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <Tooltip content={<GlassTooltip />} />
                  <Bar dataKey="count" name="Vulnerabilities" radius={[4, 4, 0, 0]} animationDuration={1000}>
                    {cvssDist.map((_, idx) => {
                      const colors = ['#00E676', '#00E676', '#69F0AE', '#FFD600', '#FFD600', '#FF9100', '#FF9100', '#FF1744', '#FF1744', '#D50000'];
                      return <Cell key={idx} fill={colors[idx]} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>

        {/* Vulnerability Trend (Area) */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Vulnerability Trend (12 Months)" icon={<TrendingUp />} delay={500}>
            {trend && trend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trend}>
                  <defs>
                    <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00D4FF" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#00D4FF" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} />
                  <YAxis tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <Tooltip content={<GlassTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="count"
                    name="Vulnerabilities"
                    stroke="#00D4FF"
                    strokeWidth={2.5}
                    fill="url(#trendGrad)"
                    dot={{ fill: '#00D4FF', r: 4, strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: '#00D4FF', stroke: '#0A0E17', strokeWidth: 2 }}
                    animationDuration={1200}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="No trend data available" />
            )}
          </ChartCard>
        </Grid>
      </Grid>

      {/* ═══════ ROW 3 — Categories + Top CWE ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>
        {/* Top Vulnerability Categories */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Top Vulnerability Categories" icon={<Category />} delay={550}>
            {categories && categories.length > 0 ? (
              <ResponsiveContainer width="100%" height={Math.max(300, categories.length * 32)}>
                <BarChart data={categories} layout="vertical" barSize={16} margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <YAxis
                    dataKey="category"
                    type="category"
                    width={160}
                    tick={{ fill: '#94A3B8', fontSize: 11 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
                    tickFormatter={(val) => (val.length > 22 ? `${val.substring(0, 22)}…` : val)}
                  />
                  <Tooltip content={<GlassTooltip />} />
                  <Bar dataKey="count" name="Count" radius={[0, 4, 4, 0]} animationDuration={1000}>
                    {categories.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>

        {/* Top CWE Weaknesses */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Top CWE Weaknesses" icon={<Shield />} delay={600}>
            {topCwe && topCwe.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topCwe} barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="cwe_id" tick={{ fill: '#94A3B8', fontSize: 10 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} angle={-30} textAnchor="end" height={60} />
                  <YAxis tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <Tooltip content={<GlassTooltip />} />
                  <Bar dataKey="count" name="Occurrences" radius={[4, 4, 0, 0]} animationDuration={1000}>
                    {topCwe.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>
      </Grid>

      {/* ═══════ ROW 4 — Top CVE + Affected Assets ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>
        {/* Top CVE IDs */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Top CVE IDs" icon={<GppBad />} delay={650}>
            {topCve && topCve.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topCve} barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="cve_id" tick={{ fill: '#94A3B8', fontSize: 9 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} angle={-35} textAnchor="end" height={70} />
                  <YAxis tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <Tooltip content={<GlassTooltip />} />
                  <Bar dataKey="count" name="Occurrences" radius={[4, 4, 0, 0]} animationDuration={1000}>
                    {topCve.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[(idx + 5) % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>

        {/* Most Affected Assets */}
        <Grid item xs={12} md={6}>
          <ChartCard title="Most Affected Assets" icon={<Storage />} delay={700}>
            {assets && assets.length > 0 ? (
              <ResponsiveContainer width="100%" height={Math.max(300, assets.length * 32)}>
                <BarChart data={assets} layout="vertical" barSize={16} margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: 'rgba(255,255,255,0.08)' }} allowDecimals={false} />
                  <YAxis
                    dataKey="asset"
                    type="category"
                    width={180}
                    tick={{ fill: '#94A3B8', fontSize: 10 }}
                    axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
                    tickFormatter={(val) => (val.length > 25 ? `${val.substring(0, 25)}…` : val)}
                  />
                  <Tooltip content={<GlassTooltip />} />
                  <Bar dataKey="count" name="Vulnerabilities" radius={[0, 4, 4, 0]} animationDuration={1000}>
                    {assets.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[(idx + 3) % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>
      </Grid>

      {/* ═══════ ROW 5 — New vs Repeat + Recent Vulns ═══════ */}
      <Grid container spacing={2.5} sx={{ mb: 2 }}>
        {/* New vs Repeat */}
        <Grid item xs={12} md={4}>
          <ChartCard title="New vs Repeat Findings" icon={<Repeat />} delay={750}>
            {newRepeat && newRepeat.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={newRepeat}
                    dataKey="count"
                    nameKey="type"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={95}
                    paddingAngle={4}
                    labelLine={false}
                    label={renderDonutLabel}
                    animationDuration={1000}
                  >
                    {newRepeat.map((_, idx) => (
                      <Cell key={idx} fill={idx === 0 ? '#00D4FF' : '#FF9100'} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip content={<GlassTooltip />} />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    iconSize={8}
                    formatter={(val) => <span style={{ color: '#94A3B8', fontSize: 12 }}>{val}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState />
            )}
          </ChartCard>
        </Grid>

        {/* Vulnerabilities DataGrid */}
        <Grid item xs={12} md={8}>
          <ChartCard 
            title={`Vulnerabilities ${chartFilter.value ? `(Filtered by ${chartFilter.value})` : ''}`} 
            icon={<BugReport />} 
            delay={800}
            sx={{
              '& .MuiDataGrid-root': {
                border: 'none',
                color: 'text.primary',
              },
              '& .MuiDataGrid-cell': {
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                display: 'flex',
                alignItems: 'center',
              },
              '& .MuiDataGrid-columnHeaders': {
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                backgroundColor: 'rgba(17, 24, 39, 0.4)',
              },
              '& .MuiDataGrid-footerContainer': {
                borderTop: '1px solid rgba(255,255,255,0.1)',
              },
              '& .MuiTablePagination-root': {
                color: 'text.secondary',
              },
              '& .MuiDataGrid-iconSeparator': {
                display: 'none',
              },
            }}
          >
            {tableVulns && tableVulns.length > 0 ? (
              <Box sx={{ height: 350, width: '100%' }}>
                <DataGrid
                  rows={tableVulns}
                  columns={columns}
                  pageSizeOptions={[5, 10, 25]}
                  initialState={{
                    pagination: { paginationModel: { pageSize: 5 } },
                  }}
                  disableRowSelectionOnClick
                />
              </Box>
            ) : (
              <EmptyState message="No vulnerabilities match the current filters" />
            )}
          </ChartCard>
        </Grid>
      </Grid>

    </Box>
  );
}

/* ─────────────────── Empty State ─────────────────── */
function EmptyState({ message = 'No data available' }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: 200,
        color: 'text.secondary',
      }}
    >
      <Typography variant="body2">{message}</Typography>
    </Box>
  );
}
