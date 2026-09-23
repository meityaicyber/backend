import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  TextField,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  RadioGroup,
  FormControlLabel,
  Radio
} from '@mui/material';
import {
  CloudUpload,
  CheckCircle,
  Error as ErrorIcon,
  Description,
  Lock as LockIcon,
  PlayArrow,
  Folder,
  TableChart
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import api from '../api/axios';
import * as XLSX from 'xlsx';

function UploadReportPage() {
  const { enqueueSnackbar } = useSnackbar();
  
  // Shared state
  const [tabValue, setTabValue] = useState(0);
  const [agencies, setAgencies] = useState([]);
  const [selectedAgency, setSelectedAgency] = useState('');

  // Single Upload state
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [passwordInput, setPasswordInput] = useState('');
  const [pendingFile, setPendingFile] = useState(null);

  // Bulk Upload state
  const [excelFile, setExcelFile] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [batchMode, setBatchMode] = useState('sequential'); // 'sequential', 'batch2', 'batch4'
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkTotal, setBulkTotal] = useState(0);
  const [bulkFailed, setBulkFailed] = useState([]);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkFinished, setBulkFinished] = useState(false);

  useEffect(() => {
    const fetchAgencies = async () => {
      try {
        const response = await api.get('/api/agencies', { params: { limit: 100 } });
        setAgencies(response.data.agencies || []);
      } catch (err) {
        enqueueSnackbar('Failed to load agencies', { variant: 'error' });
      }
    };
    fetchAgencies();
  }, [enqueueSnackbar]);

  // SINGLE UPLOAD
  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setError('');
      setResult(null);
      setUploading(true);
      setProgress(0);

      const formData = new FormData();
      formData.append('file', file);
      if (selectedAgency) {
        formData.append('agency_id', selectedAgency);
      }

      try {
        const response = await api.post('/api/reports/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const pct = Math.round((e.loaded * 100) / (e.total || 1));
            setProgress(pct);
          },
        });

        setResult(response.data);
        enqueueSnackbar('File uploaded successfully!', { variant: 'success' });
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'PASSWORD_REQUIRED') {
          setPasswordRequired(true);
          setPendingFile(file);
        } else {
          setError(msg || 'Upload failed. Please try again.');
          enqueueSnackbar(msg || 'Upload failed', { variant: 'error' });
        }
      } finally {
        setUploading(false);
      }
    },
    [enqueueSnackbar, selectedAgency]
  );

  const handlePasswordSubmit = async () => {
    if (!passwordInput || !pendingFile) return;

    setError('');
    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', pendingFile);
    formData.append('file_password', passwordInput);
    if (selectedAgency) {
      formData.append('agency_id', selectedAgency);
    }

    try {
      const response = await api.post('/api/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded * 100) / (e.total || 1));
          setProgress(pct);
        },
      });

      setResult(response.data);
      enqueueSnackbar('File unlocked and uploaded successfully!', { variant: 'success' });
      setPasswordRequired(false);
      setPasswordInput('');
      setPendingFile(null);
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg === 'INVALID_PASSWORD') {
        setError('Incorrect password. Please try again.');
      } else {
        setError(msg || 'Upload failed. Please try again.');
        setPasswordRequired(false);
        setPasswordInput('');
        setPendingFile(null);
      }
    } finally {
      setUploading(false);
    }
  };

  const handlePasswordCancel = () => {
    setPasswordRequired(false);
    setPasswordInput('');
    setPendingFile(null);
    setError('Upload cancelled due to missing password.');
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    disabled: uploading,
  });

  const handleReset = () => {
    setResult(null);
    setError('');
    setProgress(0);
  };

  // BULK UPLOAD
  const handleFolderSelect = (e) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files).filter(f => 
        f.name.toLowerCase().endsWith('.pdf') || 
        f.name.toLowerCase().endsWith('.docx') || 
        f.name.toLowerCase().endsWith('.txt')
      );
      setPdfFiles(filesArray);
    }
  };

  const handleBulkLaunch = async () => {
    if (pdfFiles.length === 0) {
      enqueueSnackbar('Please select a folder with valid files first', {variant: 'warning'});
      return;
    }

    let passwordMap = {};
    if (excelFile) {
      try {
        const data = await excelFile.arrayBuffer();
        const workbook = XLSX.read(data);
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const rows = XLSX.utils.sheet_to_json(sheet);
        
        rows.forEach(row => {
          const auditKey = Object.keys(row).find(k => {
            const low = k.toLowerCase();
            return low.includes('audit') || low.includes('no') || low.includes('id') || low.includes('unique') || low.includes('file');
          });
          const passKey = Object.keys(row).find(k => {
            const low = k.toLowerCase();
            return low.includes('pass') || low.includes('pwd');
          });
          
          if (auditKey && row[auditKey]) {
            passwordMap[String(row[auditKey]).toLowerCase()] = passKey ? row[passKey] : '';
          }
        });
      } catch (err) {
        enqueueSnackbar('Failed to parse Excel file', {variant: 'error'});
        return;
      }
    }

    setBulkRunning(true);
    setBulkFinished(false);
    setBulkProgress(0);
    setBulkFailed([]);
    setBulkTotal(pdfFiles.length);

    let failedList = [];
    const concurrency = batchMode === 'batch4' ? 4 : (batchMode === 'batch2' ? 2 : 1);
    let currentIndex = 0;

    const processNext = async () => {
      let localIndex;
      localIndex = currentIndex++;
      if (localIndex >= pdfFiles.length) return;
      
      const file = pdfFiles[localIndex];
      const baseName = file.name.replace(/\.[^/.]+$/, "");
      const matchedPassword = passwordMap[baseName.toLowerCase()] || passwordMap[file.name.toLowerCase()] || '';

      try {
        const formData = new FormData();
        formData.append('file', file);
        if (selectedAgency) {
          formData.append('agency_id', selectedAgency);
        }
        if (matchedPassword) {
          formData.append('file_password', matchedPassword);
        }

        const uploadRes = await api.post('/api/reports/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const reportId = uploadRes.data.report_id;

        await api.post(`/api/reports/${reportId}/run-pipeline`);
        
      } catch (err) {
        const msg = err.response?.data?.detail || err.message || 'Upload/Pipeline Failed';
        failedList.push({ file: file.name, error: msg });
        setBulkFailed([...failedList]);
      }
      
      setBulkProgress(prev => prev + 1);
      await processNext();
    };

    const workers = [];
    for (let i = 0; i < concurrency; i++) {
      workers.push(processNext());
    }
    
    await Promise.all(workers);
    
    setBulkRunning(false);
    setBulkFinished(true);
    enqueueSnackbar('Bulk processing completed', {variant: 'success'});
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
        Upload Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Upload single or bulk PDF, DOCX, or TXT files for processing and validation
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Single Upload" />
          <Tab label="Bulk Upload" />
        </Tabs>
      </Box>

      {/* Common Agency Select (Optional) */}
      <Box sx={{ mb: 4, maxWidth: 400 }}>
        <FormControl fullWidth variant="outlined">
          <InputLabel id="agency-select-label">Select Agency (Optional)</InputLabel>
          <Select
            labelId="agency-select-label"
            value={selectedAgency}
            onChange={(e) => setSelectedAgency(e.target.value)}
            label="Select Agency (Optional)"
            disabled={uploading || bulkRunning}
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {agencies.map((agency) => (
              <MenuItem key={agency.agency_id} value={agency.agency_id}>
                {agency.agency_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* --- SINGLE UPLOAD TAB --- */}
      {tabValue === 0 && (
        <Card className="fade-in-up">
          <CardContent sx={{ p: 4 }}>
            <Paper
              {...getRootProps()}
              elevation={0}
              sx={{
                p: 6,
                textAlign: 'center',
                cursor: uploading ? 'not-allowed' : 'pointer',
                borderRadius: 3,
                border: '2px dashed',
                borderColor: isDragActive ? '#00D4FF' : isDragReject ? '#FF1744' : 'rgba(255,255,255,0.12)',
                background: isDragActive ? 'rgba(0, 212, 255, 0.05)' : 'rgba(0, 0, 0, 0.15)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: 'rgba(0, 212, 255, 0.4)',
                  background: 'rgba(0, 212, 255, 0.03)',
                },
              }}
            >
              <input {...getInputProps()} />
              <CloudUpload
                sx={{
                  fontSize: 64,
                  color: isDragActive ? '#00D4FF' : 'text.secondary',
                  mb: 2,
                  transition: 'all 0.3s',
                  filter: isDragActive ? 'drop-shadow(0 0 12px rgba(0,212,255,0.5))' : 'none',
                }}
              />
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                {isDragActive ? 'Drop the file here' : 'Drag & drop a file here, or click to browse'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supported formats: PDF, DOCX, TXT — Max size: 50MB
              </Typography>
            </Paper>

            {/* Progress */}
            {uploading && (
              <Box sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" fontWeight={500}>Uploading...</Typography>
                  <Typography variant="body2" color="text.secondary">{progress}%</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={progress}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(90deg, #00D4FF, #00E676)',
                      borderRadius: 4,
                    },
                  }}
                />
              </Box>
            )}

            {/* Error */}
            {error && (
              <Alert severity="error" sx={{ mt: 3, borderRadius: 2 }} icon={<ErrorIcon />}>
                {error}
              </Alert>
            )}

            {/* Result */}
            {result && (
              <Box sx={{ mt: 3 }}>
                <Alert
                  severity={result.duplicate_status === 'PARTIAL_DUPLICATE' ? 'warning' : 'success'}
                  sx={{ mb: 3, borderRadius: 2 }}
                  icon={result.duplicate_status === 'PARTIAL_DUPLICATE' ? <ErrorIcon /> : <CheckCircle />}
                >
                  {result.message}
                </Alert>

                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: 2,
                    background: 'rgba(0, 230, 118, 0.05)',
                    border: '1px solid rgba(0, 230, 118, 0.15)',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Description sx={{ color: '#00E676', fontSize: 32 }} />
                    <Box>
                      <Typography variant="body1" fontWeight={600}>
                        {result.original_filename}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(result.file_size / 1024).toFixed(1)} KB
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label={`Status: ${result.upload_status}`} color="success" size="small" sx={{ fontWeight: 600 }} />
                    <Chip label={`Validation: ${result.validation_status}`} color="success" size="small" sx={{ fontWeight: 600 }} />
                  </Box>
                </Paper>

                <Button variant="outlined" onClick={handleReset} sx={{ mt: 2 }}>
                  Upload Another File
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* --- BULK UPLOAD TAB --- */}
      {tabValue === 1 && (
        <Card className="fade-in-up">
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              
              <Box>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  1. Excel Mapping (Optional)
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Upload an Excel file containing audit numbers and passwords.
                </Typography>
                <Button variant="outlined" component="label" startIcon={<TableChart />}>
                  {excelFile ? excelFile.name : 'Select Excel File'}
                  <input
                    type="file"
                    accept=".xlsx, .xls, .csv"
                    hidden
                    onChange={(e) => setExcelFile(e.target.files[0])}
                    disabled={bulkRunning}
                  />
                </Button>
              </Box>

              <Box>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  2. Select Report Folder
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Select the folder containing the bulk PDF/Word reports.
                </Typography>
                <Button variant="outlined" component="label" startIcon={<Folder />}>
                  Select Folder
                  <input
                    type="file"
                    webkitdirectory="true"
                    directory="true"
                    multiple
                    hidden
                    onChange={handleFolderSelect}
                    disabled={bulkRunning}
                  />
                </Button>
                {pdfFiles.length > 0 && (
                  <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                    {pdfFiles.length} valid files found.
                  </Typography>
                )}
              </Box>

              <Box>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  3. Batch Processing Mode
                </Typography>
                <FormControl component="fieldset" disabled={bulkRunning}>
                  <RadioGroup
                    row
                    value={batchMode}
                    onChange={(e) => setBatchMode(e.target.value)}
                  >
                    <FormControlLabel value="sequential" control={<Radio />} label="Sequential (1 by 1)" />
                    <FormControlLabel value="batch2" control={<Radio />} label="Batch of 2" />
                    <FormControlLabel value="batch4" control={<Radio />} label="Batch of 4" />
                  </RadioGroup>
                </FormControl>
              </Box>

              <Box>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={<PlayArrow />}
                  onClick={handleBulkLaunch}
                  disabled={bulkRunning || pdfFiles.length === 0}
                >
                  {bulkRunning ? 'Running...' : 'Launch Bulk Processing'}
                </Button>
              </Box>

              {(bulkRunning || bulkFinished) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Processed {bulkProgress} of {bulkTotal} files
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={bulkTotal > 0 ? (bulkProgress / bulkTotal) * 100 : 0}
                    sx={{
                      height: 10,
                      borderRadius: 5,
                      backgroundColor: 'rgba(0, 212, 255, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        background: 'linear-gradient(90deg, #00D4FF, #00E676)',
                      },
                    }}
                  />
                </Box>
              )}

              {bulkFailed.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" color="error" fontWeight={600} sx={{ mb: 1 }}>
                    Failed Files ({bulkFailed.length})
                  </Typography>
                  <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto', p: 2, borderColor: 'error.main', bgcolor: 'rgba(255,0,0,0.05)' }}>
                    {bulkFailed.map((f, i) => (
                      <Typography key={i} variant="body2" color="error" sx={{ mb: 0.5 }}>
                        <strong>{f.file}:</strong> {f.error}
                      </Typography>
                    ))}
                  </Paper>
                </Box>
              )}

            </Box>
          </CardContent>
        </Card>
      )}

      {/* Password Dialog for Single Upload */}
      <Dialog open={passwordRequired} onClose={handlePasswordCancel} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LockIcon color="primary" /> Password Required
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            This file is encrypted. Please enter the password to unlock and upload it.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="File Password"
            type="password"
            fullWidth
            variant="outlined"
            value={passwordInput}
            onChange={(e) => setPasswordInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handlePasswordSubmit()}
            error={error === 'Incorrect password. Please try again.'}
            helperText={error === 'Incorrect password. Please try again.' ? error : ''}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handlePasswordCancel} color="inherit">Cancel</Button>
          <Button onClick={handlePasswordSubmit} variant="contained" disabled={!passwordInput || uploading}>
            {uploading ? 'Unlocking...' : 'Unlock & Upload'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default UploadReportPage;
