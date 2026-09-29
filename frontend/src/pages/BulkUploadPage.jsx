import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box, Card, CardContent, Typography, LinearProgress, Alert, Button, 
  Paper, IconButton, Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, TextField, MenuItem, Select, FormControl, InputLabel, Chip,
  Autocomplete
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { CloudUpload, Refresh, PlayArrow, Stop, Cancel, Error as ErrorIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function BulkUploadPage() {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  
  // Job State
  const [activeJob, setActiveJob] = useState(null);
  const [jobId, setJobId] = useState(() => localStorage.getItem('activeBulkUploadJobId') || null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  
  // Table State
  const [items, setItems] = useState([]);
  const [rowCount, setRowCount] = useState(0);
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 50 });
  
  // Dialogs State
  const [passwordDialogItem, setPasswordDialogItem] = useState(null);
  const [passwordInput, setPasswordInput] = useState('');
  
  const [mappingDialogItem, setMappingDialogItem] = useState(null);
  const [selectedMapping, setSelectedMapping] = useState(null);
  const [allAgencies, setAllAgencies] = useState([]);

  // Polling ref
  const pollingRef = useRef(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Fetch all agencies for fallback mapping
  useEffect(() => {
    const fetchAgencies = async () => {
      try {
        const res = await api.get('/api/agencies', { params: { skip: 0, limit: 100 } });
        setAllAgencies(res.data.agencies || []);
      } catch (err) {
        console.error("Failed to load agencies", err);
      }
    };
    fetchAgencies();
  }, []);

  const fetchJobData = async (currentJobId) => {
    try {
      const res = await api.get(`/api/bulk-upload/jobs/${currentJobId}`);
      
      // If this is the initial load (activeJob is null) and the job is already fully processed,
      // clear it out so the user gets a fresh upload screen. We keep COMPLETED_WITH_ERRORS
      // so they can still review failed/pending items.
      if (!activeJob && ['COMPLETED', 'FAILED', 'CANCELLED'].includes(res.data.status)) {
        setJobId(null);
        setActiveJob(null);
        setItems([]);
        localStorage.removeItem('activeBulkUploadJobId');
        return;
      }
      
      setActiveJob(res.data);
      if (['COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED', 'CANCELLED'].includes(res.data.status)) {
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      }
    } catch (err) {
      console.error(err);
      if (err.response?.status === 404) {
        setJobId(null);
        setActiveJob(null);
        localStorage.removeItem('activeBulkUploadJobId');
      }
    }
  };

    useEffect(() => {
    if (jobId) {
      localStorage.setItem('activeBulkUploadJobId', jobId);
      if (!activeJob) {
        fetchJobData(jobId);
      }
    } else {
      localStorage.removeItem('activeBulkUploadJobId');
    }
  }, [jobId]);

  const fetchItemsData = async (currentJobId, page, pageSize) => {
    try {
      // API expects 1-based page, DataGrid uses 0-based
      const res = await api.get(`/api/bulk-upload/jobs/${currentJobId}/items`, {
        params: { page: page + 1, page_size: pageSize }
      });
      setItems(res.data.items || []);
      setRowCount(res.data.total || 0);
    } catch (err) {
      console.error(err);
    }
  };

  // Poll job data every 3 seconds if active
  useEffect(() => {
    if (jobId && activeJob && !['COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED', 'CANCELLED'].includes(activeJob.status)) {
      if (!pollingRef.current) {
        pollingRef.current = setInterval(() => {
          fetchJobData(jobId);
          fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
        }, 3000);
      }
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
  }, [jobId, activeJob, paginationModel]);

  // Handle pagination changes
  useEffect(() => {
    if (jobId) {
      fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
    }
  }, [paginationModel, jobId]);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // 1. Create Job
      const jobRes = await api.post('/api/bulk-upload/jobs', { total_files: acceptedFiles.length });
      const newJobId = jobRes.data.id;
      setJobId(newJobId);
      setActiveJob(jobRes.data);
      
      // 2. Upload in Chunks of 20
      const chunkSize = 20;
      for (let i = 0; i < acceptedFiles.length; i += chunkSize) {
        const chunk = acceptedFiles.slice(i, i + chunkSize);
        const formData = new FormData();
        chunk.forEach(f => {
            formData.append('files', f);
            // react-dropzone adds 'path' containing the relative folder structure
            formData.append('paths', f.path || f.name);
        });
        
        await api.post(`/api/bulk-upload/jobs/${newJobId}/files`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setUploadProgress(Math.round(((i + chunk.length) / acceptedFiles.length) * 100));
      }
      
      enqueueSnackbar(`Successfully uploaded ${acceptedFiles.length} files to server.`, { variant: 'success' });
      
    } catch (err) {
      enqueueSnackbar('Failed to upload files', { variant: 'error' });
      console.error(err);
    } finally {
      setIsUploading(false);
      setUploadProgress(100);
      if (jobId) {
        fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
      }
    }
  }, [enqueueSnackbar, jobId, paginationModel]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    disabled: isUploading || activeJob?.status === 'PROCESSING'
  });

  const handleStartJob = async () => {
    if (!jobId) return;
    try {
      await api.post(`/api/bulk-upload/jobs/${jobId}/start`);
      enqueueSnackbar('Job started', { variant: 'success' });
      fetchJobData(jobId);
      fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
    } catch (err) {
      enqueueSnackbar('Failed to start job', { variant: 'error' });
    }
  };

  const handleCancelJob = async () => {
    if (!jobId) return;
    try {
      await api.post(`/api/bulk-upload/jobs/${jobId}/cancel`);
      enqueueSnackbar('Job cancelled', { variant: 'warning' });
      fetchJobData(jobId);
    } catch (err) {
      enqueueSnackbar('Failed to cancel job', { variant: 'error' });
    }
  };

  const handleRetryFailed = async () => {
    if (!jobId) return;
    try {
      await api.post(`/api/bulk-upload/jobs/${jobId}/retry-failed`);
      enqueueSnackbar('Retrying transient failures', { variant: 'info' });
      fetchJobData(jobId);
    } catch (err) {
      enqueueSnackbar('Failed to retry', { variant: 'error' });
    }
  };

  const submitPassword = async () => {
    if (!passwordDialogItem || !passwordInput) return;
    try {
      await api.post(`/api/bulk-upload/items/${passwordDialogItem.id}/retry`, {
        password: passwordInput
      });
      enqueueSnackbar('Password submitted. Item retrying inline.', { variant: 'success' });
      setPasswordDialogItem(null);
      setPasswordInput('');
      fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Failed to apply password', { variant: 'error' });
    }
  };

  const submitMapping = async () => {
    if (!mappingDialogItem || !selectedMapping) return;
    try {
      await api.post(`/api/bulk-upload/items/${mappingDialogItem.id}/retry`, {
        agency_id: selectedMapping
      });
      enqueueSnackbar('Agency mapped. Item queued for processing.', { variant: 'success' });
      setMappingDialogItem(null);
      setSelectedMapping(null);
      fetchItemsData(jobId, paginationModel.page, paginationModel.pageSize);
    } catch (err) {
      enqueueSnackbar(err.response?.data?.detail || 'Failed to map agency', { variant: 'error' });
    }
  };

  const columns = [
    { field: 'filename', headerName: 'File Name', flex: 1, minWidth: 200 },
    { 
      field: 'extracted_agency_name', 
      headerName: 'Agency', 
      flex: 1, 
      minWidth: 150,
      renderCell: (params) => {
        if (params.row.status === 'AGENCY_REVIEW_REQUIRED') {
          return (
            <Button size="small" variant="outlined" color="warning" onClick={() => setMappingDialogItem(params.row)}>
              Map Agency
            </Button>
          );
        }
        return params.value || '-';
      }
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 200,
      renderCell: (params) => {
        let color = 'default';
        if (params.value === 'COMPLETED') color = 'success';
        else if (params.value === 'FAILED' || params.value === 'DUPLICATE') color = 'error';
        else if (params.value.includes('REQUIRED')) color = 'warning';
        else if (params.value === 'PROCESSING') color = 'primary';
        
        return <Chip label={params.value} color={color} size="small" />;
      }
    },
    { 
      field: 'error_code', 
      headerName: 'Message', 
      flex: 1, 
      minWidth: 200,
      renderCell: (params) => {
        if (params.row.status === 'PASSWORD_REQUIRED') {
          return (
            <Button size="small" variant="outlined" onClick={() => setPasswordDialogItem(params.row)}>
              Provide Password
            </Button>
          );
        }
        return params.row.processing_error || '-';
      }
    },
  ];

  return (
    <Box>
      <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>Bulk Upload Reports</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Upload up to 1000 reports simultaneously. They will be processed in the background automatically mapping to their respective agencies.
      </Typography>

      {/* Upload Area */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Paper
            {...getRootProps()}
            elevation={0}
            sx={{
              p: 6, textAlign: 'center', cursor: isUploading ? 'wait' : 'pointer',
              border: '2px dashed',
              borderColor: isDragActive ? '#00D4FF' : 'rgba(255,255,255,0.12)',
              background: isDragActive ? 'rgba(0, 212, 255, 0.05)' : 'rgba(0, 0, 0, 0.15)',
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6">Drag & drop multiple files, or click to select</Typography>
            <Typography variant="body2" color="text.secondary">Select folder via browser picker or drop multiple files.</Typography>
          </Paper>

          {isUploading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>Uploading to server... {uploadProgress}%</Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Job Progress */}
      {activeJob && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Job Progress: {activeJob.status}</Typography>
              <Box>
                {activeJob.status === 'CREATED' && (
                  <Button variant="contained" color="primary" startIcon={<PlayArrow />} onClick={handleStartJob} sx={{ mr: 1 }}>
                    Start Processing
                  </Button>
                )}
                {['QUEUED', 'PROCESSING', 'SCANNING'].includes(activeJob.status) && (
                  <Button variant="outlined" color="error" startIcon={<Stop />} onClick={handleCancelJob}>
                    Cancel Job
                  </Button>
                )}
                {['COMPLETED_WITH_ERRORS', 'FAILED', 'COMPLETED'].includes(activeJob.status) && activeJob.failed_files > 0 && (
                  <Button variant="outlined" color="primary" startIcon={<Refresh />} onClick={handleRetryFailed}>
                    Retry Transient Failures
                  </Button>
                )}
                {['COMPLETED', 'COMPLETED_WITH_ERRORS'].includes(activeJob.status) && (
                  <Button variant="contained" color="success" onClick={() => navigate('/reports')} sx={{ ml: 1 }}>
                    View Uploaded Reports
                  </Button>
                )}
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip label={`Total: ${activeJob.total_files}`} />
              <Chip label={`Completed: ${activeJob.completed_files}`} color="success" />
              <Chip label={`Queued/Proc: ${activeJob.queued_files + activeJob.processing_files}`} color="primary" />
              <Chip label={`Failed: ${activeJob.failed_files}`} color="error" />
              <Chip label={`Duplicates: ${activeJob.duplicate_files}`} color="error" />
              <Chip label={`Needs Review: ${activeJob.needs_review_files}`} color="warning" />
            </Box>
            
            <LinearProgress 
              variant="determinate" 
              value={(activeJob.completed_files + activeJob.failed_files + activeJob.duplicate_files) / (activeJob.total_files || 1) * 100} 
            />
          </CardContent>
        </Card>
      )}

      {/* Items Table */}
      {jobId && (
        <Card>
          <CardContent>
            <DataGrid
              rows={items}
              columns={columns}
              rowCount={rowCount}
              paginationMode="server"
              paginationModel={paginationModel}
              onPaginationModelChange={setPaginationModel}
              pageSizeOptions={[20, 50, 100]}
              autoHeight
              disableRowSelectionOnClick
            />
          </CardContent>
        </Card>
      )}

      {/* Password Dialog */}
      <Dialog open={!!passwordDialogItem} onClose={() => setPasswordDialogItem(null)}>
        <DialogTitle>Provide File Password</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {passwordDialogItem?.filename} requires a password to decrypt.
          </DialogContentText>
          <TextField
            autoFocus margin="dense" label="Password" type="password" fullWidth
            value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordDialogItem(null)}>Cancel</Button>
          <Button onClick={submitPassword} variant="contained">Decrypt & Retry</Button>
        </DialogActions>
      </Dialog>

      {/* Mapping Dialog */}
      <Dialog open={!!mappingDialogItem} onClose={() => setMappingDialogItem(null)} fullWidth maxWidth="sm">
        <DialogTitle>Map Agency</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Could not confidently map '{mappingDialogItem?.extracted_agency_name || 'unknown'}' to an agency. 
            Please select the correct one from the candidates or leave blank to cancel.
          </DialogContentText>
          <Autocomplete
            options={allAgencies}
            getOptionLabel={(option) => {
              // Highlight suggested candidates
              const isCandidate = mappingDialogItem?.candidate_matches?.some(c => c.agency_id === option.agency_id);
              const conf = isCandidate ? mappingDialogItem.candidate_matches.find(c => c.agency_id === option.agency_id).score : null;
              return `${option.agency_name} (${option.agency_code})${conf ? ` - ML Confidence: ${Math.round(conf * 100)}%` : ''}`;
            }}
            value={allAgencies.find(a => a.agency_id === selectedMapping) || null}
            onChange={(_, newValue) => setSelectedMapping(newValue ? newValue.agency_id : null)}
            renderInput={(params) => <TextField {...params} label="Select Agency" />}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMappingDialogItem(null)}>Cancel</Button>
          <Button onClick={submitMapping} variant="contained" disabled={!selectedMapping}>Save & Retry</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
