import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  Build,
  CloudUpload,
  Rule,
  Score,
} from '@mui/icons-material';
import api from '../api/axios';

const ruleConfig = [
  { key: 'benchmark_rules', label: 'Benchmark Rules', required: true },
  { key: 'scoring_rules', label: 'Scoring Rules', required: true },
  { key: 'recommendation_rules', label: 'Recommendation Rules', required: true },
  { key: 'methodology_rules', label: 'Methodology Rules', required: true },
  { key: 'scoring_weights', label: 'Scoring Weights', required: true },
  { key: 'thresholds', label: 'Thresholds', required: true },
];

function BenchmarkManagementPage() {
  const [error, setError] = useState('');
  const [downloadMessage, setDownloadMessage] = useState('');
  const [benchmarkName, setBenchmarkName] = useState('Audit Quality Benchmark');
  const [version, setVersion] = useState('');
  const [changeSummary, setChangeSummary] = useState('');
  const [currentVersion, setCurrentVersion] = useState('0.0');
  const [selectedFiles, setSelectedFiles] = useState({});
  const fileInputRefs = useRef({});

  useEffect(() => {
    const loadCurrentVersion = async () => {
      try {
        const response = await api.get('/api/offline-update/current-version');
        setCurrentVersion(response?.data?.version || '0.0');
      } catch {
        setCurrentVersion('0.0');
      }
    };

    loadCurrentVersion();
  }, []);

  const handleFileSelection = (key, event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setSelectedFiles((current) => ({ ...current, [key]: file }));
    setError('');
    setDownloadMessage('');
    event.target.value = '';
  };

  const handleGeneratePackage = async () => {
    setError('');
    setDownloadMessage('');

    if (!benchmarkName.trim()) {
      setError('Benchmark name is required.');
      return;
    }

    if (!version.trim()) {
      setError('Version number is required.');
      return;
    }

    const requestedVersion = version.trim();
    const currentMajorMinor = currentVersion?.replace(/^v/i, '').trim();
    const currentParts = currentMajorMinor.split('.').map((part) => Number.parseInt(part, 10) || 0);
    const targetParts = requestedVersion.replace(/^v/i, '').split('.').map((part) => Number.parseInt(part, 10) || 0);

    const targetTuple = [targetParts[0] || 0, targetParts[1] || 0];
    const currentTuple = [currentParts[0] || 0, currentParts[1] || 0];
    const isLater = targetTuple[0] > currentTuple[0] || (targetTuple[0] === currentTuple[0] && targetTuple[1] > currentTuple[1]);

    if (!isLater) {
      setError(`Version must be greater than the current active benchmark version ${currentVersion}.`);
      return;
    }

    const missing = ruleConfig.filter((rule) => !selectedFiles[rule.key]);
    if (missing.length) {
      setError('Upload all six JSON files before generating the package.');
      return;
    }

    const formData = new FormData();
    formData.append('benchmark_name', benchmarkName.trim());
    formData.append('version', requestedVersion);
    formData.append('change_summary', changeSummary.trim());

    ruleConfig.forEach((rule) => {
      formData.append(rule.key, selectedFiles[rule.key]);
    });

    try {
      const response = await api.post('/api/offline-update/build-package', formData, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `AQB_Update_v${requestedVersion}.zip`;
      link.click();
      window.URL.revokeObjectURL(url);
      setDownloadMessage(`AQB_Update_v${requestedVersion}.zip downloaded successfully.`);
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Unable to generate the offline package.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            Generate Package
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Build a new offline benchmark package from uploaded JSON rule payloads. The payload is generated here and applied only when you import it in Offline Update.
          </Typography>
        </Box>
        <Chip
          label={`Current Active Version: ${currentVersion}`}
          sx={{ background: 'rgba(0, 212, 255, 0.12)', color: '#00D4FF', borderRadius: 1 }}
        />
      </Box>

      {error && <Alert severity="error">{error}</Alert>}
      {downloadMessage && <Alert severity="success">{downloadMessage}</Alert>}

      <Paper sx={{ p: 3, borderRadius: 3, background: 'rgba(15, 23, 42, 0.78)' }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Benchmark Name"
              value={benchmarkName}
              onChange={(event) => setBenchmarkName(event.target.value)}
              size="small"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Version"
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              placeholder="e.g. 2.3"
              size="small"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Change Summary"
              value={changeSummary}
              onChange={(event) => setChangeSummary(event.target.value)}
              multiline
              minRows={3}
              size="small"
            />
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={2}>
        {ruleConfig.map((rule) => (
          <Grid item xs={12} md={6} lg={4} key={rule.key}>
            <Card sx={{ height: '100%', background: 'rgba(15, 23, 42, 0.78)', borderRadius: 3 }}>
              <CardContent>
                <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                  <Box sx={{ width: 38, height: 38, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0, 212, 255, 0.12)', color: '#00D4FF' }}>
                    {rule.key === 'benchmark_rules' ? <Rule fontSize="small" /> : <Score fontSize="small" />}
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      {rule.label}
                    </Typography>
                    <Chip
                      size="small"
                      label={rule.required ? 'Required' : 'Optional'}
                      sx={{ mt: 0.5, background: 'rgba(0, 230, 118, 0.12)', color: '#7CFFB2', borderRadius: 1 }}
                    />
                  </Box>
                </Stack>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {selectedFiles[rule.key]?.name || 'No file selected yet'}
                </Typography>

                <input
                  ref={(element) => {
                    fileInputRefs.current[rule.key] = element;
                  }}
                  type="file"
                  accept="application/json,.json"
                  hidden
                  onChange={(event) => handleFileSelection(rule.key, event)}
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<CloudUpload />}
                  onClick={() => fileInputRefs.current[rule.key]?.click()}
                  sx={{ textTransform: 'none' }}
                >
                  Upload {rule.label}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<Build />}
          onClick={handleGeneratePackage}
          sx={{
            background: 'linear-gradient(135deg, #00D4FF, #7C4DFF)',
            textTransform: 'none',
            px: 2.5,
          }}
        >
          Generate Package
        </Button>
      </Box>
    </Box>
  );
}

export default BenchmarkManagementPage;
