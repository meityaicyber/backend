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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Skeleton,
} from '@mui/material';
import { Add, Edit, Delete, Person } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { useSnackbar } from 'notistack';
import api from '../api/axios';

const ROLES = ['ADMIN', 'AUDITOR', 'REVIEWER'];

function UserManagementPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);

  const { control, register, handleSubmit, reset, formState: { errors } } = useForm();

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/users', { params: { limit: 100 } });
      setUsers(response.data.users);
    } catch {
      enqueueSnackbar('Failed to load users', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleOpenCreate = () => {
    setEditUser(null);
    reset({ username: '', email: '', password: '', full_name: '', roles: ['AUDITOR'] });
    setDialogOpen(true);
  };

  const handleOpenEdit = (user) => {
    setEditUser(user);
    reset({
      username: user.username,
      email: user.email,
      password: '',
      full_name: user.full_name || '',
      roles: user.roles,
    });
    setDialogOpen(true);
  };

  const onSubmit = async (data) => {
    try {
      if (editUser) {
        await api.put(`/api/users/${editUser.user_id}`, {
          email: data.email,
          full_name: data.full_name || null,
          roles: data.roles,
        });
        enqueueSnackbar('User updated', { variant: 'success' });
      } else {
        await api.post('/api/users', {
          username: data.username,
          email: data.email,
          password: data.password,
          full_name: data.full_name || null,
          roles: data.roles,
        });
        enqueueSnackbar('User created', { variant: 'success' });
      }
      setDialogOpen(false);
      fetchUsers();
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Operation failed', { variant: 'error' });
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;
    try {
      await api.delete(`/api/users/${userId}`);
      enqueueSnackbar('User deactivated', { variant: 'success' });
      fetchUsers();
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Delete failed', { variant: 'error' });
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
            User Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage system users and their roles
          </Typography>
        </Box>
        <Button
          id="btn-create-user"
          variant="contained"
          startIcon={<Add />}
          onClick={handleOpenCreate}
        >
          Add User
        </Button>
      </Box>

      <Card className="fade-in-up">
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Roles</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <TableCell key={j}><Skeleton variant="text" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  users.map((u) => (
                    <TableRow
                      key={u.user_id}
                      sx={{
                        transition: 'background 0.2s',
                        '&:hover': { backgroundColor: 'rgba(0,212,255,0.03)' },
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <Person sx={{ color: 'text.secondary' }} />
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {u.username}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {u.full_name || '—'}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {u.email}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {u.roles.map((r) => (
                            <Chip
                              key={r}
                              label={r}
                              size="small"
                              color={r === 'ADMIN' ? 'error' : r === 'AUDITOR' ? 'primary' : 'default'}
                              sx={{ fontWeight: 600, fontSize: '0.65rem' }}
                            />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={u.is_active ? 'Active' : 'Inactive'}
                          color={u.is_active ? 'success' : 'default'}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(u.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => handleOpenEdit(u)} sx={{ color: '#00D4FF' }}>
                            <Edit fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Deactivate">
                          <IconButton size="small" onClick={() => handleDelete(u.user_id)} sx={{ color: '#FF1744' }}>
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
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
          {editUser ? 'Edit User' : 'Create User'}
        </DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {!editUser && (
              <TextField
                label="Username"
                fullWidth
                {...register('username', { required: 'Required', minLength: { value: 3, message: 'Min 3 chars' } })}
                error={!!errors.username}
                helperText={errors.username?.message}
              />
            )}
            <TextField
              label="Email"
              fullWidth
              type="email"
              {...register('email', { required: 'Required' })}
              error={!!errors.email}
              helperText={errors.email?.message}
            />
            {!editUser && (
              <TextField
                label="Password"
                fullWidth
                type="password"
                {...register('password', { required: 'Required', minLength: { value: 8, message: 'Min 8 chars' } })}
                error={!!errors.password}
                helperText={errors.password?.message}
              />
            )}
            <TextField
              label="Full Name"
              fullWidth
              {...register('full_name')}
            />
            <Controller
              name="roles"
              control={control}
              rules={{ required: 'Select at least one role' }}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.roles}>
                  <InputLabel>Roles</InputLabel>
                  <Select
                    {...field}
                    multiple
                    label="Roles"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {selected.map((v) => (
                          <Chip key={v} label={v} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {ROLES.map((role) => (
                      <MenuItem key={role} value={role}>
                        {role}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </DialogContent>
          <DialogActions sx={{ p: 3, pt: 1 }}>
            <Button onClick={() => setDialogOpen(false)} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained">
              {editUser ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}

export default UserManagementPage;
