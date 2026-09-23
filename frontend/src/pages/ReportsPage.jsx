import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Tooltip,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
  Collapse,
  Divider,
  LinearProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Search,
  Visibility,
  Download,
  Delete,
  Description,
  RocketLaunch,
  CheckCircle,
  HourglassTop,
  Close,
  ExpandMore,
  ExpandLess,
  Shield,
  BugReport,
  Security,
  Warning,
  TipsAndUpdates,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';

const statusColor = {
  UPLOADED: 'info',
  VALIDATED: 'success',
  REJECTED: 'error',
  QUARANTINED: 'warning',
};

const extIcon = {
  '.pdf': '📄',
  '.docx': '📝',
  '.txt': '📃',
};

const severityColor = {
  CRITICAL: '#FF1744',
  HIGH: '#FF9100',
  MEDIUM: '#FFD600',
  LOW: '#00E676',
};

const riskLevelGradient = {
  CRITICAL: 'linear-gradient(135deg, #FF1744 0%, #D50000 100%)',
  HIGH: 'linear-gradient(135deg, #FF9100 0%, #FF6D00 100%)',
  MEDIUM: 'linear-gradient(135deg, #FFD600 0%, #FFAB00 100%)',
  LOW: 'linear-gradient(135deg, #00E676 0%, #00C853 100%)',
};

/* ──────────── Pipeline Results Dialog ──────────── */
function PipelineResultsDialog({ open, onClose, results, reportName }) {
  const [tabValue, setTabValue] = useState(0);
  const [expandedSections, setExpandedSections] = useState({
    vulnerabilities: true,
    compliance: false,
    recommendations: false,
  });

  if (!results) return null;

  const toggleSection = (section) =>
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));

  const execSummary = results.executive_summary || {};
  const vulnsArray = results.vulnerabilities || [];
  const compliance = results.compliance || {};
  const recommendations = results.recommendations || [];
  
  let riskLevel = 'LOW';
  const crit = execSummary.critical_count || 0;
  const high = execSummary.high_count || 0;
  const med = execSummary.medium_count || 0;
  const low = execSummary.low_count || 0;
  
  if (crit > 0) riskLevel = 'CRITICAL';
  else if (high > 0) riskLevel = 'HIGH';
  else if (med > 0) riskLevel = 'MEDIUM';

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          background: 'linear-gradient(145deg, rgba(17,25,40,0.97) 0%, rgba(12,17,29,0.99) 100%)',
          border: '1px solid rgba(0,212,255,0.12)',
          backdropFilter: 'blur(20px)',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pb: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Security sx={{ color: '#00D4FF', fontSize: 28 }} />
          <Box>
            <Typography variant="h6" fontWeight={700}>
              AI Pipeline Results
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {reportName}
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: 'text.secondary' }}>
          <Close />
        </IconButton>
      </DialogTitle>

      <Tabs
        value={tabValue}
        onChange={(e, v) => setTabValue(v)}
        sx={{ px: 3, borderBottom: 1, borderColor: 'rgba(255,255,255,0.1)', mb: 1 }}
        textColor="inherit"
        indicatorColor="primary"
      >
        <Tab label="Overview" sx={{ color: '#fff', fontWeight: 600 }} />
        <Tab label="Full JSON" sx={{ color: '#fff', fontWeight: 600 }} />
        <Tab label="Vulnerabilities" sx={{ color: '#fff', fontWeight: 600 }} />
      </Tabs>

      <DialogContent sx={{ pt: 1, minHeight: 400 }}>
        {tabValue === 0 && (
          <Box>
        {/* ── Risk Score Card ── */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            mb: 3,
            flexWrap: 'wrap',
          }}
        >
          <Box
            sx={{
              flex: '1 1 200px',
              p: 2.5,
              borderRadius: 2.5,
              background: riskLevelGradient[riskLevel] || riskLevelGradient.MEDIUM,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: -20,
                right: -20,
                width: 100,
                height: 100,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.1)',
              }}
            />
            <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>
              Overall Risk Score
            </Typography>
            <Typography variant="h4" fontWeight={800} sx={{ color: '#fff', mt: 1 , background: '-webkit-linear-gradient(45deg, #00D4FF, #00E676)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'}}>
              {execSummary.summary_text || riskLevel}
            </Typography>
            <Chip
              label={riskLevel}
              size="small"
              sx={{
                mt: 0.5,
                fontWeight: 700,
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: '#fff',
                fontSize: '0.7rem',
              }}
            />
          </Box>

          <Box
            sx={{
              flex: '1 1 200px',
              p: 2.5,
              borderRadius: 2.5,
              background: 'rgba(0,212,255,0.06)',
              border: '1px solid rgba(0,212,255,0.1)',
            }}
          >
            <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600 }}>
              Vulnerabilities Summary
            </Typography>
            <Typography variant="h3" fontWeight={800} sx={{ color: '#00D4FF' }}>
              {execSummary.total_vulnerabilities || 0}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
              {crit > 0 && (
                <Chip label={`${crit} Critical`} size="small" sx={{ fontSize: '0.65rem', fontWeight: 600, bgcolor: 'rgba(255,23,68,0.15)', color: '#FF1744' }} />
              )}
              {high > 0 && (
                <Chip label={`${high} High`} size="small" sx={{ fontSize: '0.65rem', fontWeight: 600, bgcolor: 'rgba(255,145,0,0.15)', color: '#FF9100' }} />
              )}
              {med > 0 && (
                <Chip label={`${med} Medium`} size="small" sx={{ fontSize: '0.65rem', fontWeight: 600, bgcolor: 'rgba(255,214,0,0.15)', color: '#FFD600' }} />
              )}
              {low > 0 && (
                <Chip label={`${low} Low`} size="small" sx={{ fontSize: '0.65rem', fontWeight: 600, bgcolor: 'rgba(0,230,118,0.15)', color: '#00E676' }} />
              )}
            </Box>
          </Box>

          {/* Confidence Box Removed as not present in masterjson */}
        </Box>

        {/* ── Vulnerabilities Details ── */}
        <Box sx={{ mb: 2 }}>
          <Box
            onClick={() => toggleSection('vulnerabilities')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              p: 1.5,
              borderRadius: 2,
              '&:hover': { bgcolor: 'rgba(0,212,255,0.04)' },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BugReport sx={{ color: '#FF9100', fontSize: 20 }} />
              <Typography variant="subtitle1" fontWeight={700}>
                Vulnerability Details
              </Typography>
            </Box>
            {expandedSections.vulnerabilities ? <ExpandLess /> : <ExpandMore />}
          </Box>
          <Collapse in={expandedSections.vulnerabilities}>
            <Box sx={{ pl: 1, pr: 1 }}>
              {(vulnsArray).map((v, i) => (
                <Box
                  key={v.id || i}
                  sx={{
                    p: 2,
                    mb: 1,
                    borderRadius: 2,
                    border: `1px solid ${severityColor[v.severity]}22`,
                    bgcolor: `${severityColor[v.severity]}08`,
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={v.severity}
                        size="small"
                        sx={{
                          fontWeight: 700,
                          fontSize: '0.6rem',
                          bgcolor: `${severityColor[v.severity]}20`,
                          color: severityColor[v.severity],
                          minWidth: 70,
                        }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        {v.id}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      CVSS: {v.cvss_score || 'N/A'}
                    </Typography>
                  </Box>
                  <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                    {v.vulnerability_title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    📍 {v.detailed_observation}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255,255,255,0.04)', my: 1 }} />

        {/* ── Compliance Results ── */}
        <Box sx={{ mb: 2 }}>
          <Box
            onClick={() => toggleSection('compliance')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              p: 1.5,
              borderRadius: 2,
              '&:hover': { bgcolor: 'rgba(0,212,255,0.04)' },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Shield sx={{ color: '#00D4FF', fontSize: 20 }} />
              <Typography variant="subtitle1" fontWeight={700}>
                Compliance Results
              </Typography>
            </Box>
            {expandedSections.compliance ? <ExpandLess /> : <ExpandMore />}
          </Box>
          <Collapse in={expandedSections.compliance}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, p: 1 }}>
              {Object.entries(compliance).map(([framework, data]) => {
                const statusColorMap = {
                  COMPLIANT: '#00E676',
                  PARTIALLY_COMPLIANT: '#FFD600',
                  NON_COMPLIANT: '#FF1744',
                };
                const color = statusColorMap[data.status] || '#aaa';
                return (
                  <Box
                    key={framework}
                    sx={{
                      flex: '1 1 180px',
                      p: 2,
                      borderRadius: 2,
                      border: `1px solid ${color}22`,
                      bgcolor: `${color}06`,
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>
                      {framework}
                    </Typography>
                    <Chip
                      label={data.status.replace(/_/g, ' ')}
                      size="small"
                      sx={{
                        fontWeight: 600,
                        fontSize: '0.6rem',
                        bgcolor: `${color}18`,
                        color,
                        mb: 1,
                      }}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Score: <b>{data.score}</b>
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Gaps: <b>{data.gaps_identified}</b>
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={data.score}
                      sx={{
                        mt: 1,
                        height: 4,
                        borderRadius: 2,
                        bgcolor: `${color}10`,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 2,
                          bgcolor: color,
                        },
                      }}
                    />
                  </Box>
                );
              })}
            </Box>
          </Collapse>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255,255,255,0.04)', my: 1 }} />

        {/* ── Recommendations ── */}
        <Box>
          <Box
            onClick={() => toggleSection('recommendations')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              p: 1.5,
              borderRadius: 2,
              '&:hover': { bgcolor: 'rgba(0,212,255,0.04)' },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TipsAndUpdates sx={{ color: '#FFD600', fontSize: 20 }} />
              <Typography variant="subtitle1" fontWeight={700}>
                Recommendations
              </Typography>
            </Box>
            {expandedSections.recommendations ? <ExpandLess /> : <ExpandMore />}
          </Box>
          <Collapse in={expandedSections.recommendations}>
            <Box sx={{ pl: 1, pr: 1 }}>
              {recommendations.map((rec, i) => (
                <Box
                  key={i}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 1.5,
                    p: 1.5,
                    mb: 0.5,
                    borderRadius: 2,
                    '&:hover': { bgcolor: 'rgba(255,214,0,0.04)' },
                  }}
                >
                  <Box
                    sx={{
                      minWidth: 24,
                      height: 24,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #FFD600, #FFAB00)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: '#000',
                      mt: 0.2,
                    }}
                  >
                    {i + 1}
                  </Box>
                  <Typography variant="body2">{rec}</Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        </Box>

        {/* ── Pipeline Metadata ── */}
        <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Typography variant="caption" color="text.secondary">
              Pipeline ID: <code>{results.pipeline_id}</code>
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Processed: {new Date(results.analysis_timestamp).toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Duration: {results.processing_time_seconds}s
            </Typography>
          </Box>
        </Box>
        </Box>
        )}
        {tabValue === 1 && (
          <Box sx={{ p: 2, bgcolor: 'rgba(0,0,0,0.5)', borderRadius: 2, overflowX: 'auto', maxHeight: 600, overflowY: 'auto' }}>
            <pre style={{ margin: 0, color: '#00D4FF', fontSize: '0.85rem' }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </Box>
        )}

        {tabValue === 2 && (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>ID</TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>Severity</TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>Title</TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>Location</TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>CVSS</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(vulnsArray).map((v) => (
                  <TableRow key={v.id}>
                    <TableCell sx={{ fontFamily: 'monospace', color: '#fff' }}>{v.id}</TableCell>
                    <TableCell>
                      <Chip
                        label={v.severity}
                        size="small"
                        sx={{
                          bgcolor: `${severityColor[v.severity] || '#aaa'}20`,
                          color: severityColor[v.severity] || '#aaa',
                          fontWeight: 700,
                          fontSize: '0.65rem'
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ fontWeight: 600, color: '#fff' }}>{v.vulnerability_title}</TableCell>
                    <TableCell sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>{v.detailed_observation}</TableCell>
                    <TableCell sx={{ color: '#fff' }}>{v.cvss_score || 'N/A'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
    </Dialog>
  );
}

/* ──────────── Reports Page ──────────── */
function ReportsPage() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [searchDebounce, setSearchDebounce] = useState('');

  // Pipeline state
  const [pipelineStatus, setPipelineStatus] = useState({}); // { [reportId]: 'idle' | 'processing' | 'completed' | 'error' }
  const [pipelineResults, setPipelineResults] = useState({}); // { [reportId]: {...results} }
  const [confirmDialog, setConfirmDialog] = useState({ open: false, report: null });
  const [resultsDialog, setResultsDialog] = useState({ open: false, reportId: null, reportName: '' });

  useEffect(() => {
    const timer = setTimeout(() => setSearchDebounce(search), 400);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      try {
        const params = {
          skip: page * rowsPerPage,
          limit: rowsPerPage,
        };
        if (searchDebounce) params.search = searchDebounce;

        const response = await api.get('/api/reports', { params });
        setReports(response.data.reports);
        setTotal(response.data.total);
      } catch (err) {
        enqueueSnackbar('Failed to load reports', { variant: 'error' });
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, [page, rowsPerPage, searchDebounce, enqueueSnackbar]);

  const handleDownload = async (reportId, filename) => {
    try {
      const response = await api.get(`/api/reports/${reportId}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      enqueueSnackbar('Download failed', { variant: 'error' });
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await api.delete(`/api/reports/${reportId}`);
      enqueueSnackbar('Report deleted', { variant: 'success' });
      setReports((prev) => prev.filter((r) => r.report_id !== reportId));
      setTotal((prev) => prev - 1);
    } catch {
      enqueueSnackbar('Delete failed', { variant: 'error' });
    }
  };

  /* ── Pipeline Handlers ── */
  const openConfirmDialog = (report) => {
    setConfirmDialog({ open: true, report });
  };

  const closeConfirmDialog = () => {
    setConfirmDialog({ open: false, report: null });
  };

  const handleRunPipeline = async () => {
    const report = confirmDialog.report;
    if (!report) return;
    closeConfirmDialog();

    const reportId = report.report_id;
    setPipelineStatus((prev) => ({ ...prev, [reportId]: 'processing' }));

    try {
      const response = await api.post(`/api/reports/${reportId}/run-pipeline`);
      setPipelineResults((prev) => ({ ...prev, [reportId]: response.data }));
      setPipelineStatus((prev) => ({ ...prev, [reportId]: 'completed' }));
      enqueueSnackbar('AI Pipeline completed successfully!', { variant: 'success' });
    } catch (err) {
      setPipelineStatus((prev) => ({ ...prev, [reportId]: 'error' }));
      const detail = err.response?.data?.detail || 'Pipeline failed';
      enqueueSnackbar(`Pipeline error: ${detail}`, { variant: 'error' });
    }
  };

  const openResultsDialog = (reportId, reportName) => {
    setResultsDialog({ open: true, reportId, reportName });
  };

  const closeResultsDialog = () => {
    setResultsDialog({ open: false, reportId: null, reportName: '' });
  };

  const handleViewResults = async (report) => {
    try {
      const response = await api.get(`/api/reports/${report.report_id}/results`);
      setPipelineResults((prev) => ({ ...prev, [report.report_id]: response.data }));
      setPipelineStatus((prev) => ({ ...prev, [report.report_id]: 'completed' }));
      openResultsDialog(report.report_id, report.original_filename);
    } catch (err) {
      if (err.response?.status === 404) {
        enqueueSnackbar('No pipeline results found for this report.', { variant: 'info' });
      } else {
        enqueueSnackbar('Failed to load results.', { variant: 'error' });
      }
    }
  };

  const renderPipelineChip = (report) => {
    const status = pipelineStatus[report.report_id];

    if (status === 'processing') {
      return (
        <Chip
          icon={<HourglassTop sx={{ fontSize: 14, animation: 'spin 1.5s linear infinite', '@keyframes spin': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } } }} />}
          label="Processing"
          size="small"
          sx={{
            fontWeight: 600,
            fontSize: '0.7rem',
            bgcolor: 'rgba(0,212,255,0.12)',
            color: '#00D4FF',
            border: '1px solid rgba(0,212,255,0.25)',
            animation: 'pulse 2s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1 },
              '50%': { opacity: 0.6 },
            },
          }}
        />
      );
    }

    if (status === 'completed') {
      return (
        <Chip
          icon={<CheckCircle sx={{ fontSize: 14 }} />}
          label="Completed"
          size="small"
          onClick={() => openResultsDialog(report.report_id, report.original_filename)}
          sx={{
            fontWeight: 600,
            fontSize: '0.7rem',
            bgcolor: 'rgba(0,230,118,0.12)',
            color: '#00E676',
            border: '1px solid rgba(0,230,118,0.25)',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              bgcolor: 'rgba(0,230,118,0.2)',
              transform: 'scale(1.05)',
            },
          }}
        />
      );
    }

    if (status === 'error') {
      return (
        <Chip
          icon={<Warning sx={{ fontSize: 14 }} />}
          label="Failed"
          size="small"
          sx={{
            fontWeight: 600,
            fontSize: '0.7rem',
            bgcolor: 'rgba(255,23,68,0.12)',
            color: '#FF1744',
            border: '1px solid rgba(255,23,68,0.25)',
          }}
        />
      );
    }

    return (
      <Typography variant="caption" color="text.secondary">
        —
      </Typography>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
            Reports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {total} reports in total
          </Typography>
        </Box>
      </Box>

      {/* Search */}
      <TextField
        id="reports-search"
        placeholder="Search reports by filename..."
        size="small"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        sx={{ mb: 3, width: { xs: '100%', sm: 360 } }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search sx={{ color: 'text.secondary' }} />
            </InputAdornment>
          ),
        }}
      />

      {/* Table */}
      <Card className="fade-in-up">
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>File</TableCell>
                  <TableCell>Agency</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Uploader</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Pipeline</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 9 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton variant="text" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : reports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 6 }}>
                      <Description sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography color="text.secondary">No reports found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  reports.map((report) => (
                    <TableRow
                      key={report.report_id}
                      sx={{
                        transition: 'background 0.2s',
                        '&:hover': { backgroundColor: 'rgba(0,212,255,0.03)' },
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography fontSize="1.2rem">
                            {extIcon[report.file_extension] || '📄'}
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body2" fontWeight={600} noWrap sx={{ maxWidth: 250 }}>
                                {report.original_filename}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {report.file_extension.toUpperCase()}
                              </Typography>
                            </Box>
                            {/* Hashes */}
                            <Box sx={{ display: 'flex', flexDirection: 'column', mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>
                                SHA256: {report.sha256_hash.substring(0, 16)}...
                              </Typography>
                              {report.simhash && (
                                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>
                                  SimHash: {report.simhash}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {report.agency?.agency_name || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {report.partial_duplicate ? (
                          <Link
                            to={`/reports/${report.partial_duplicate.original_report_id}`}
                            style={{ textDecoration: 'none' }}
                          >
                            <Chip
                              label="Partial Duplicate"
                              size="small"
                              color="warning"
                              variant="outlined"
                              sx={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.7rem' }}
                            />
                          </Link>
                        ) : (
                          <Chip
                            label="Original"
                            size="small"
                            color="success"
                            variant="outlined"
                            sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {report.uploader_username || '—'}
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
                        {renderPipelineChip(report)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(report.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<Security fontSize="small" />}
                            onClick={() => handleViewResults(report)}
                            sx={{ color: '#FFD600', borderColor: 'rgba(255,214,0,0.5)', '&:hover': { borderColor: '#FFD600', bgcolor: 'rgba(255,214,0,0.1)' }, textTransform: 'none', px: 1, py: 0.25 }}
                          >
                            AI Results
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<Visibility fontSize="small" />}
                            onClick={() => navigate(`/reports/${report.report_id}`)}
                            sx={{ color: '#00D4FF', borderColor: 'rgba(0,212,255,0.5)', '&:hover': { borderColor: '#00D4FF', bgcolor: 'rgba(0,212,255,0.1)' }, textTransform: 'none', px: 1, py: 0.25 }}
                          >
                            View
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<Download fontSize="small" />}
                            onClick={() => handleDownload(report.report_id, report.original_filename)}
                            sx={{ color: '#00E676', borderColor: 'rgba(0,230,118,0.5)', '&:hover': { borderColor: '#00E676', bgcolor: 'rgba(0,230,118,0.1)' }, textTransform: 'none', px: 1, py: 0.25 }}
                          >
                            Download
                          </Button>
                          {isAdmin() && (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<Delete fontSize="small" />}
                              onClick={() => handleDelete(report.report_id)}
                              sx={{ color: '#FF1744', borderColor: 'rgba(255,23,68,0.5)', '&:hover': { borderColor: '#FF1744', bgcolor: 'rgba(255,23,68,0.1)' }, textTransform: 'none', px: 1, py: 0.25 }}
                            >
                              Delete
                            </Button>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[5, 10, 25, 50]}
            sx={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}
          />
        </CardContent>
      </Card>

      {/* ── Confirmation Dialog ── */}
      <Dialog
        open={confirmDialog.open}
        onClose={closeConfirmDialog}
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'linear-gradient(145deg, rgba(17,25,40,0.97) 0%, rgba(12,17,29,0.99) 100%)',
            border: '1px solid rgba(0,212,255,0.12)',
            backdropFilter: 'blur(20px)',
            minWidth: 400,
          },
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <RocketLaunch sx={{ color: '#AB47BC' }} />
          <Typography variant="h6" fontWeight={700}>
            Run AI Pipeline
          </Typography>
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: 'text.secondary', mb: 2 }}>
            Are you sure you want to run the AI analysis pipeline on this report?
          </DialogContentText>
          {confirmDialog.report && (
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                bgcolor: 'rgba(0,212,255,0.04)',
                border: '1px solid rgba(0,212,255,0.08)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Description sx={{ color: '#00D4FF', fontSize: 20 }} />
                <Typography variant="body2" fontWeight={600}>
                  {confirmDialog.report.original_filename}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                Report ID: <code>{confirmDialog.report.report_id}</code>
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                Size: {(confirmDialog.report.file_size / 1024).toFixed(1)} KB • {confirmDialog.report.file_extension.toUpperCase()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            onClick={closeConfirmDialog}
            sx={{ color: 'text.secondary', fontWeight: 600 }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleRunPipeline}
            variant="contained"
            startIcon={<RocketLaunch />}
            sx={{
              background: 'linear-gradient(135deg, #AB47BC, #7B1FA2)',
              fontWeight: 700,
              px: 3,
              '&:hover': {
                background: 'linear-gradient(135deg, #CE93D8, #AB47BC)',
              },
            }}
          >
            Run Pipeline
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Results Dialog ── */}
      <PipelineResultsDialog
        open={resultsDialog.open}
        onClose={closeResultsDialog}
        results={pipelineResults[resultsDialog.reportId]}
        reportName={resultsDialog.reportName}
      />
    </Box>
  );
}

export default ReportsPage;
