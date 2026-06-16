import React, { useState, useCallback } from 'react';
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
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Error as ErrorIcon,
  Description,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import api from '../api/axios';

function UploadReportPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

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
        const msg = err.response?.data?.detail || 'Upload failed. Please try again.';
        setError(msg);
        enqueueSnackbar(msg, { variant: 'error' });
      } finally {
        setUploading(false);
      }
    },
    [enqueueSnackbar]
  );

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

  return (
    <Box>
      <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
        Upload Report
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Upload PDF, DOCX, or TXT files for processing and validation
      </Typography>

      {/* Dropzone */}
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
              borderColor: isDragActive
                ? '#00D4FF'
                : isDragReject
                ? '#FF1744'
                : 'rgba(255,255,255,0.12)',
              background: isDragActive
                ? 'rgba(0, 212, 255, 0.05)'
                : 'rgba(0, 0, 0, 0.15)',
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
              {isDragActive
                ? 'Drop the file here'
                : 'Drag & drop a file here, or click to browse'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supported formats: PDF, DOCX, TXT — Max size: 50MB
            </Typography>
          </Paper>

          {/* Progress */}
          {uploading && (
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" fontWeight={500}>
                  Uploading...
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {progress}%
                </Typography>
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
            <Alert
              severity="error"
              sx={{ mt: 3, borderRadius: 2 }}
              icon={<ErrorIcon />}
            >
              {error}
            </Alert>
          )}

          {/* Result */}
          {result && (
            <Box sx={{ mt: 3 }}>
              <Alert
                severity="success"
                sx={{ mb: 3, borderRadius: 2 }}
                icon={<CheckCircle />}
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
                  <Chip
                    label={`Status: ${result.upload_status}`}
                    color="success"
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    label={`Validation: ${result.validation_status}`}
                    color="success"
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>

                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', mt: 2, fontFamily: 'monospace', wordBreak: 'break-all' }}
                >
                  SHA256: {result.sha256_hash}
                </Typography>
              </Paper>

              <Button
                variant="outlined"
                onClick={handleReset}
                sx={{ mt: 2 }}
              >
                Upload Another File
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default UploadReportPage;
