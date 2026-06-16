import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
} from '@mui/material';
import {
  Search,
  Visibility,
  Download,
  Delete,
  Description,
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
                  <TableCell>Uploader</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <TableCell key={j}>
                          <Skeleton variant="text" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : reports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
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
                          <Box>
                            <Typography variant="body2" fontWeight={600} noWrap sx={{ maxWidth: 250 }}>
                              {report.original_filename}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {report.file_extension.toUpperCase()}
                            </Typography>
                          </Box>
                        </Box>
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
                        <Typography variant="body2" color="text.secondary">
                          {new Date(report.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/reports/${report.report_id}`)}
                            sx={{ color: '#00D4FF' }}
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            onClick={() => handleDownload(report.report_id, report.original_filename)}
                            sx={{ color: '#00E676' }}
                          >
                            <Download fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {isAdmin() && (
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDelete(report.report_id)}
                              sx={{ color: '#FF1744' }}
                            >
                              <Delete fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
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
    </Box>
  );
}

export default ReportsPage;
