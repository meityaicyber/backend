import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box, Card, CardContent, Typography, LinearProgress, Alert, Chip, Paper, Button, Dialog, DialogTitle, DialogContent, DialogContentText, TextField, DialogActions, FormControl, InputLabel, Select, MenuItem, Tabs, Tab, RadioGroup, FormControlLabel, Radio, Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import {
  CloudUpload, CheckCircle, Error as ErrorIcon, Description, Lock as LockIcon, PlayArrow, Folder, TableChart, Autorenew, Pending, Cancel, Download
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
  const [batchMode, setBatchMode] = useState('sequential');
  
  // Array of { id, file, name, status, details }
  // Status: 'Pending' | 'Uploading' | 'Pipeline' | 'Success' | 'Failed'
  const [bulkFilesData, setBulkFilesData] = useState([]);
  
  const [bulkProgress, setBulkProgress] = useState(0);
  const [bulkTotal, setBulkTotal] = useState(0);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkFinished, setBulkFinished] = useState(false);
  const [bulkStartTime, setBulkStartTime] = useState(null);
  const [bulkEndTime, setBulkEndTime] = useState(null);
  const [generatingExcel, setGeneratingExcel] = useState(false);
  const [generatedExcelUrl, setGeneratedExcelUrl] = useState(null);

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

  // SINGLE UPLOAD (Keep existing logic unchanged...)
  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;
      const file = acceptedFiles[0];
      setError(''); setResult(null); setUploading(true); setProgress(0);

      const formData = new FormData();
      formData.append('file', file);
      if (selectedAgency) formData.append('agency_id', selectedAgency);

      try {
        const response = await api.post('/api/reports/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / (e.total || 1))),
        });
        setResult(response.data);
        enqueueSnackbar('File uploaded successfully!', { variant: 'success' });
      } catch (err) {
        const msg = err.response?.data?.detail;
        if (msg === 'PASSWORD_REQUIRED') {
          setPasswordRequired(true); setPendingFile(file);
        } else {
          setError(msg || 'Upload failed. Please try again.');
          enqueueSnackbar(msg || 'Upload failed', { variant: 'error' });
        }
      } finally {
        setUploading(false);
      }
    }, [enqueueSnackbar, selectedAgency]
  );

  const handlePasswordSubmit = async () => {
    if (!passwordInput || !pendingFile) return;
    setError(''); setUploading(true); setProgress(0);
    const formData = new FormData();
    formData.append('file', pendingFile);
    formData.append('file_password', passwordInput);
    if (selectedAgency) formData.append('agency_id', selectedAgency);

    try {
      const response = await api.post('/api/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / (e.total || 1))),
      });
      setResult(response.data);
      enqueueSnackbar('File unlocked and uploaded successfully!', { variant: 'success' });
      setPasswordRequired(false); setPasswordInput(''); setPendingFile(null);
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (msg === 'INVALID_PASSWORD') {
        setError('Incorrect password. Please try again.');
      } else {
        setError(msg || 'Upload failed. Please try again.');
        setPasswordRequired(false); setPasswordInput(''); setPendingFile(null);
      }
    } finally {
      setUploading(false);
    }
  };

  const handlePasswordCancel = () => {
    setPasswordRequired(false); setPasswordInput(''); setPendingFile(null);
    setError('Upload cancelled due to missing password.');
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop, accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 1, maxSize: 50 * 1024 * 1024, disabled: uploading,
  });

  const handleReset = () => { setResult(null); setError(''); setProgress(0); };

  // BULK UPLOAD
  const handleFolderSelect = (e) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files).filter(f => {
        const lowerName = f.name.toLowerCase();
        return lowerName.endsWith('.pdf') || lowerName.endsWith('.docx') || lowerName.endsWith('.doc');
      });
      setPdfFiles(filesArray);
      
      // Initialize table data
      const initialData = filesArray.map((f, i) => {
        const cleanName = (f.webkitRelativePath || f.name).split('/').pop().split('\\').pop();
        return {
          id: i,
          file: f,
          name: cleanName,
          status: 'Pending',
          details: '-'
        };
      });
      setBulkFilesData(initialData);
      setBulkFinished(false);
    }
  };

  const updateFileStatus = (id, status, details) => {
    setBulkFilesData(prev => prev.map(item => 
      item.id === id ? { ...item, status, details } : item
    ));
  };


  const handleGenerateMapping = async (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setGeneratingExcel(true);
    
    try {
      const files = Array.from(e.target.files);
      
      // Group files by their directory
      const directories = {};
      files.forEach(f => {
        const pathParts = (f.webkitRelativePath || f.name).split('/');
        pathParts.pop(); // remove filename
        const dirPath = pathParts.join('/');
        if (!directories[dirPath]) directories[dirPath] = [];
        directories[dirPath].push(f);
      });

      const mappingData = [];

      for (const dir in directories) {
        const dirFiles = directories[dir];
        const txtFiles = dirFiles.filter(f => f.name.toLowerCase().endsWith('.txt'));
        const reportFiles = dirFiles.filter(f => f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.docx'));

        if (txtFiles.length > 0 && reportFiles.length > 0) {
          // Read the first txt file as password
          const txtFile = txtFiles[0];
          const text = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(txtFile);
          });
          
          const password = text.trim();
          
          if (password) {
            reportFiles.forEach(rf => {
               mappingData.push({
                 "File Name": rf.name.substring(0, rf.name.lastIndexOf('.')) || rf.name,
                 "Password": password
               });
            });
          }
        }
      }

      if (mappingData.length === 0) {
        enqueueSnackbar('No valid password text files found in the folder structure.', { variant: 'warning' });
        setGeneratingExcel(false);
        return;
      }

      // Create Excel
      const worksheet = XLSX.utils.json_to_sheet(mappingData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Mapping");
      
      // Generate binary string
      const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      
      // Create download URL
      const url = URL.createObjectURL(blob);
      setGeneratedExcelUrl(url);
      
      // Auto-set as excel file
      const generatedFile = new File([blob], 'generated_mapping.xlsx', { type: blob.type });
      setExcelFile(generatedFile);
      
      enqueueSnackbar(`Generated mapping for ${mappingData.length} files successfully!`, { variant: 'success' });
    } catch (error) {
      console.error('Error generating mapping:', error);
      enqueueSnackbar('Failed to generate Excel mapping', { variant: 'error' });
    } finally {
      setGeneratingExcel(false);
      // Clear input so it can be clicked again
      e.target.value = null;
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
    setBulkTotal(pdfFiles.length);
    setBulkStartTime(Date.now());
    setBulkEndTime(null);

    // Reset status for all files to pending
    setBulkFilesData(prev => prev.map(item => ({...item, status: 'Pending', details: '-'})));

    const concurrency = batchMode === 'batch4' ? 4 : (batchMode === 'batch2' ? 2 : 1);
    let currentIndex = 0;

    const processNext = async () => {
      let localIndex;
      localIndex = currentIndex++;
      if (localIndex >= pdfFiles.length) return;
      
      const fileData = bulkFilesData[localIndex];
      const file = fileData.file;
      const cleanName = fileData.name;
      const baseName = cleanName.replace(/\.[^/.]+$/, "");
      const matchedPassword = passwordMap[baseName.toLowerCase()] || passwordMap[cleanName.toLowerCase()] || '';

      let reportId = null;

      try {
        updateFileStatus(localIndex, 'Uploading', 'Uploading to storage...');

        const formData = new FormData();
        formData.append('file', file, cleanName);
        if (selectedAgency) formData.append('agency_id', selectedAgency);
        if (matchedPassword) formData.append('file_password', matchedPassword);

        // 1. Upload
        const uploadRes = await api.post('/api/reports/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        reportId = uploadRes.data.report_id;

        // 2. Run Pipeline
        updateFileStatus(localIndex, 'Pipeline', 'Running AI Pipeline...');
        await api.post(`/api/reports/${reportId}/run-pipeline`);
        
        updateFileStatus(localIndex, 'Success', 'File saved and pipeline completed.');
      } catch (err) {
        const msg = err.response?.data?.detail || err.message || 'Operation Failed';
        
        if (reportId) {
          updateFileStatus(localIndex, 'Failed', `${msg} (Rolling back...)`);
          // Rollback: delete from system
          try {
             await api.delete(`/api/reports/${reportId}`);
             updateFileStatus(localIndex, 'Failed', `${msg}. File deleted from system.`);
          } catch(rollbackErr) {
             updateFileStatus(localIndex, 'Failed', `${msg}. Rollback failed: ${rollbackErr.message}`);
          }
        } else {
          updateFileStatus(localIndex, 'Failed', msg);
        }
      }
      
      setBulkProgress(prev => prev + 1);
      await processNext();
    };

    const workers = [];
    for (let i = 0; i < concurrency; i++) {
      workers.push(processNext());
    }
    
    await Promise.all(workers);
    
    setBulkEndTime(Date.now());
    setBulkRunning(false);
    setBulkFinished(true);
    enqueueSnackbar('Bulk processing completed', {variant: 'success'});
  };

  const renderStatusChip = (status) => {
    switch (status) {
      case 'Pending': return <Chip size="small" icon={<Pending />} label="Pending" color="default" />;
      case 'Uploading': return <Chip size="small" icon={<Autorenew sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />} label="Uploading" color="info" />;
      case 'Pipeline': return <Chip size="small" icon={<Autorenew sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />} label="Pipeline Running" color="primary" />;
      case 'Success': return <Chip size="small" icon={<CheckCircle />} label="Success" color="success" />;
      case 'Failed': return <Chip size="small" icon={<Cancel />} label="Failed" color="error" />;
      default: return <Chip size="small" label={status} />;
    }
  };

  const renderFinalReport = () => {
    if (!bulkFinished) return null;
    
    const successCount = bulkFilesData.filter(f => f.status === 'Success').length;
    const failedCount = bulkFilesData.filter(f => f.status === 'Failed').length;
    const timeTaken = bulkEndTime && bulkStartTime ? ((bulkEndTime - bulkStartTime) / 1000).toFixed(1) : 0;

    return (
      <Paper elevation={0} sx={{ mt: 4, p: 3, borderRadius: 2, background: 'rgba(0, 212, 255, 0.05)', border: '1px solid rgba(0, 212, 255, 0.2)' }}>
        <Typography variant="h6" fontWeight={700} gutterBottom sx={{ color: '#00D4FF', display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircle /> Bulk Processing Report
        </Typography>
        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap', mt: 2 }}>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>Total Files</Typography>
            <Typography variant="h4" fontWeight={700} sx={{ background: '-webkit-linear-gradient(45deg, #00D4FF, #00E676)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{bulkTotal}</Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>Successful</Typography>
            <Typography variant="h4" fontWeight={700} color="success.main">{successCount}</Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>Failed</Typography>
            <Typography variant="h4" fontWeight={700} color="error.main">{failedCount}</Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>Time Taken</Typography>
            <Typography variant="h4" fontWeight={700}>{timeTaken}s</Typography>
          </Box>
        </Box>
      </Paper>
    );
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
        Upload Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Upload single or bulk PDF or DOCX files for processing and validation
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Single Upload" />
          <Tab label="Bulk Upload" />
        </Tabs>
      </Box>

      {/* Common Agency Select */}
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
           {/* Same contents as before... */}
           <CardContent sx={{ p: 4 }}>
            <Paper {...getRootProps()} elevation={0} sx={{
                p: 6, textAlign: 'center', cursor: uploading ? 'not-allowed' : 'pointer',
                borderRadius: 3, border: '2px dashed', borderColor: isDragActive ? '#00D4FF' : isDragReject ? '#FF1744' : 'rgba(255,255,255,0.12)',
                background: isDragActive ? 'rgba(0, 212, 255, 0.05)' : 'rgba(0, 0, 0, 0.15)', transition: 'all 0.3s ease',
                '&:hover': { borderColor: 'rgba(0, 212, 255, 0.4)', background: 'rgba(0, 212, 255, 0.03)' },
              }}>
              <input {...getInputProps()} />
              <CloudUpload sx={{ fontSize: 64, color: isDragActive ? '#00D4FF' : 'text.secondary', mb: 2, filter: isDragActive ? 'drop-shadow(0 0 12px rgba(0,212,255,0.5))' : 'none' }} />
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>{isDragActive ? 'Drop the file here' : 'Drag & drop a file here, or click to browse'}</Typography>
              <Typography variant="body2" color="text.secondary">Supported formats: PDF, DOCX — Max size: 50MB</Typography>
            </Paper>

            {uploading && (
              <Box sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" fontWeight={500}>Uploading...</Typography>
                  <Typography variant="body2" color="text.secondary">{progress}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 4, backgroundColor: 'rgba(0, 212, 255, 0.1)', '& .MuiLinearProgress-bar': { background: 'linear-gradient(90deg, #00D4FF, #00E676)' } }} />
              </Box>
            )}

            {error && <Alert severity="error" sx={{ mt: 3, borderRadius: 2 }} icon={<ErrorIcon />}>{error}</Alert>}

            {result && (
              <Box sx={{ mt: 3 }}>
                <Alert severity={result.duplicate_status === 'PARTIAL_DUPLICATE' ? 'warning' : 'success'} sx={{ mb: 3, borderRadius: 2 }} icon={result.duplicate_status === 'PARTIAL_DUPLICATE' ? <ErrorIcon /> : <CheckCircle />}>
                  {result.message}
                </Alert>
                <Paper elevation={0} sx={{ p: 3, borderRadius: 2, background: 'rgba(0, 230, 118, 0.05)', border: '1px solid rgba(0, 230, 118, 0.15)' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Description sx={{ color: '#00E676', fontSize: 32 }} />
                    <Box>
                      <Typography variant="body1" fontWeight={600}>{result.original_filename}</Typography>
                      <Typography variant="caption" color="text.secondary">{(result.file_size / 1024).toFixed(1)} KB</Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label={`Status: ${result.upload_status}`} color="success" size="small" sx={{ fontWeight: 600 }} />
                    <Chip label={`Validation: ${result.validation_status}`} color="success" size="small" sx={{ fontWeight: 600 }} />
                  </Box>
                </Paper>
                <Button variant="outlined" onClick={handleReset} sx={{ mt: 2 }}>Upload Another File</Button>
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
                
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                  <Button variant="outlined" component="label" startIcon={<TableChart />}>
                    {excelFile ? excelFile.name : 'Select Excel File'}
                    <input type="file" accept=".xlsx, .xls, .csv" hidden onChange={(e) => setExcelFile(e.target.files[0])} disabled={bulkRunning} />
                  </Button>
                  <Typography variant="body2" color="text.secondary">OR</Typography>
                  <Button variant="contained" component="label" color="secondary" startIcon={generatingExcel ? <Autorenew sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} /> : <Autorenew />} disabled={bulkRunning || generatingExcel}>
                    {generatingExcel ? 'Generating...' : 'Auto-Generate from Folder'}
                    <input type="file" webkitdirectory="true" directory="true" multiple hidden onChange={handleGenerateMapping} disabled={bulkRunning || generatingExcel} />
                  </Button>
                  {generatedExcelUrl && (
                    <Button variant="text" color="info" startIcon={<Download />} component="a" href={generatedExcelUrl} download="mapping.xlsx">
                      Download Generated Excel
                    </Button>
                  )}
                </Box>

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
                  <input type="file" webkitdirectory="true" directory="true" multiple hidden onChange={handleFolderSelect} disabled={bulkRunning} />
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
                  <RadioGroup row value={batchMode} onChange={(e) => setBatchMode(e.target.value)}>
                    <FormControlLabel value="sequential" control={<Radio />} label="Sequential (1 by 1)" />
                    <FormControlLabel value="batch2" control={<Radio />} label="Batch of 2" />
                    <FormControlLabel value="batch4" control={<Radio />} label="Batch of 4" />
                  </RadioGroup>
                </FormControl>
              </Box>

              <Box>
                <Button variant="contained" color="primary" size="large" startIcon={<PlayArrow />} onClick={handleBulkLaunch} disabled={bulkRunning || pdfFiles.length === 0}>
                  {bulkRunning ? 'Running...' : 'Launch Bulk Processing'}
                </Button>
              </Box>

              {/* Progress and Detailed Tracking Table */}
              {(bulkRunning || bulkFinished || bulkFilesData.length > 0) && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Processed {bulkProgress} of {bulkTotal} files
                  </Typography>
                  <LinearProgress variant="determinate" value={bulkTotal > 0 ? (bulkProgress / bulkTotal) * 100 : 0} sx={{ height: 10, borderRadius: 5, mb: 3, backgroundColor: 'rgba(0, 212, 255, 0.1)', '& .MuiLinearProgress-bar': { background: 'linear-gradient(90deg, #00D4FF, #00E676)' } }} />
                  
                  <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.1)' }}>
                    <Table size="small">
                      <TableHead sx={{ background: 'rgba(255,255,255,0.05)' }}>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 600 }}>File Name</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Details</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {bulkFilesData.map((row) => (
                          <TableRow key={row.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                            <TableCell component="th" scope="row">
                              {row.name}
                            </TableCell>
                            <TableCell>{renderStatusChip(row.status)}</TableCell>
                            <TableCell sx={{ color: row.status === 'Failed' ? 'error.main' : 'text.secondary' }}>
                              {row.details}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  {renderFinalReport()}

                </Box>
              )}

            </Box>
          </CardContent>
        </Card>
      )}

      {/* Password Dialog for Single Upload */}
      <Dialog open={passwordRequired} onClose={handlePasswordCancel} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><LockIcon color="primary" /> Password Required</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>This file is encrypted. Please enter the password to unlock and upload it.</DialogContentText>
          <TextField autoFocus margin="dense" label="File Password" type="password" fullWidth variant="outlined" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handlePasswordSubmit()} error={error === 'Incorrect password. Please try again.'} helperText={error === 'Incorrect password. Please try again.' ? error : ''} />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handlePasswordCancel} color="inherit">Cancel, Download</Button>
          <Button onClick={handlePasswordSubmit} variant="contained" disabled={!passwordInput || uploading}>{uploading ? 'Unlocking...' : 'Unlock & Upload'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default UploadReportPage;
