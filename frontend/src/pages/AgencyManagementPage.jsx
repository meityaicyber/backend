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
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tooltip,
  Skeleton,
} from '@mui/material';
import { Add, Edit, Delete, Business } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useSnackbar } from 'notistack';
import api from '../api/axios';

function AgencyManagementPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editAgency, setEditAgency] = useState(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const fetchAgencies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/agencies', { params: { limit: 100 } });
      setAgencies(response.data.agencies);
    } catch {
      enqueueSnackbar('Failed to load agencies', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgencies();
  }, []);

  const handleOpenCreate = () => {
    setEditAgency(null);
    reset({ name: '', description: '' });
    setDialogOpen(true);
  };

  const handleOpenEdit = (agency) => {
    setEditAgency(agency);
    reset({
      name: agency.name,
      description: agency.description || '',
    });
    setDialogOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editAgency) {
        await api.put(`/api/agencies/${editAgency.agency_id}`, {
          name: data.name,
          description: data.description || null,
        });
        enqueueSnackbar('Agency updated', { variant: 'success' });
      } else {
        await api.post('/api/agencies', {
          name: data.name,
          description: data.description || null,
        });
        enqueueSnackbar('Agency created', { variant: 'success' });
      }
      setDialogOpen(false);
      fetchAgencies();
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Operation failed', { variant: 'error' });
    }
  };

  const handleDelete = async (agencyId) => {
    if (!window.confirm('Are you sure you want to delete this agency? This action cannot be undone.')) return;
    try {
      await api.delete(`/api/agencies/${agencyId}`);
      enqueueSnackbar('Agency deleted', { variant: 'success' });
      fetchAgencies();
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Delete failed', { variant: 'error' });
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
            Agency Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage system agencies
          </Typography>
        </Box>
        <Button
          id="btn-create-agency"
          variant="contained"
          startIcon={<Add />}
          onClick={handleOpenCreate}
        >
          Add Agency
        </Button>
      </Box>

      <Card className="fade-in-up">
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Agency Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 4 }).map((_, j) => (
                        <TableCell key={j}><Skeleton variant="text" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  agencies.map((a) => (
                    <TableRow
                      key={a.agency_id}
                      sx={{
                        transition: 'background 0.2s',
                        '&:hover': { backgroundColor: 'rgba(0,212,255,0.03)' },
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Business sx={{ color: 'text.secondary' }} />
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {a.name}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }} noWrap>
                          {a.description || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(a.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => handleOpenEdit(a)} sx={{ color: '#00D4FF' }}>
                            <Edit fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" onClick={() => handleDelete(a.agency_id)} sx={{ color: '#FF1744' }}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
                {!loading && agencies.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                      <Typography variant="body2" color="text.secondary">
                        No agencies found.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(17, 24, 39, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 3,
          },
        }}
      >
        <DialogTitle sx={{ fontWeight: 700 }}>
          {editAgency ? 'Edit Agency' : 'Create Agency'}
        </DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <TextField
              label="Agency Name"
              fullWidth
              {...register('name', { required: 'Required', minLength: { value: 2, message: 'Min 2 chars' } })}
              error={!!errors.name}
              helperText={errors.name?.message}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              {...register('description')}
            />
          </DialogContent>
          <DialogActions sx={{ p: 3, pt: 1 }}>
            <Button onClick={() => setDialogOpen(false)} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained">
              {editAgency ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}

export default AgencyManagementPage;
