import React, { useEffect, useState } from 'react';
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
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Skeleton,
} from '@mui/material';
import { Search, Security } from '@mui/icons-material';
import api from '../api/axios';

const actionColors = {
  FILE_UPLOAD: 'primary',
  FILE_DELETE: 'error',
  USER_LOGIN: 'success',
  USER_CREATE: 'info',
};

function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        const params = { skip: page * rowsPerPage, limit: rowsPerPage };
        if (actionFilter) params.action = actionFilter;

        const response = await api.get('/api/audit-logs', { params });
        setLogs(response.data.logs);
        setTotal(response.data.total);
      } catch (err) {
        console.error('Failed to fetch audit logs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [page, rowsPerPage, actionFilter]);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
            Audit Logs
          </Typography>
          <Typography variant="body2" color="text.secondary">
            System activity and security event tracking
          </Typography>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Action Filter</InputLabel>
          <Select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(0);
            }}
            label="Action Filter"
          >
            <MenuItem value="">All Actions</MenuItem>
            <MenuItem value="FILE_UPLOAD">File Upload</MenuItem>
            <MenuItem value="FILE_DELETE">File Delete</MenuItem>
            <MenuItem value="USER_LOGIN">User Login</MenuItem>
            <MenuItem value="USER_CREATE">User Create</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Card className="fade-in-up">
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Action</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 5 }).map((_, j) => (
                        <TableCell key={j}><Skeleton variant="text" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                      <Security sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography color="text.secondary">No audit logs found</Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow
                      key={log.log_id}
                      sx={{
                        transition: 'background 0.2s',
                        '&:hover': { backgroundColor: 'rgba(0,212,255,0.03)' },
                      }}
                    >
                      <TableCell>
                        <Chip
                          label={log.action}
                          color={actionColors[log.action] || 'default'}
                          size="small"
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {log.username || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.status}
                          color={log.status === 'SUCCESS' ? 'success' : 'error'}
                          variant="outlined"
                          size="small"
                          sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          noWrap
                          sx={{ maxWidth: 300, fontFamily: 'monospace', fontSize: '0.75rem' }}
                        >
                          {log.details ? JSON.stringify(log.details).substring(0, 80) : '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(log.created_at).toLocaleString()}
                        </Typography>
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
            rowsPerPageOptions={[10, 25, 50]}
            sx={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}
          />
        </CardContent>
      </Card>
    </Box>
  );
}

export default AuditLogsPage;
