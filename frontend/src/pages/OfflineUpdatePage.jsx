import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import {
  CheckCircleOutline,
  FileUpload,
  History,
  SystemUpdateAlt,
  Undo,
  Verified,
} from '@mui/icons-material';
import api from '../api/axios';

const stepIcons = {
  'Import Package': <FileUpload fontSize="small" />,
  'Verify Package': <Verified fontSize="small" />,
  Install: <SystemUpdateAlt fontSize="small" />,
  Rollback: <Undo fontSize="small" />,
  'Update History': <History fontSize="small" />,
};

const defaultSteps = [
  {
    title: 'Import Package',
    description: 'Upload the package archive from an offline media source.',
    status: 'Ready',
  },
  {
    title: 'Verify Package',
    description: 'Validate checksum, signature, and package integrity before install.',
    status: 'Pending',
  },
  {
    title: 'Install',
    description: 'Apply the approved version with staged deployment controls.',
    status: 'Pending',
  },
  {
    title: 'Update History',
    description: 'Review package events, install trace, and rollback record.',
    status: 'Tracked',
  },
];

function OfflineUpdatePage() {
  const [steps, setSteps] = useState(defaultSteps);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [workingStep, setWorkingStep] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [packageInfo, setPackageInfo] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [installProgress, setInstallProgress] = useState([]);
  const [backups, setBackups] = useState([]);
  const [rollbackVersion, setRollbackVersion] = useState('');

  const loadHistory = async () => {
    const response = await api.get('/offline/history');
    setHistory(Array.isArray(response?.data?.history) ? response.data.history : []);
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [stepsResponse, historyResponse, backupsResponse] = await Promise.all([
          api.get('/api/offline-update/steps'),
          api.get('/offline/history'),
          api.get('/offline/backups'),
        ]);

        const workflowSteps = (Array.isArray(stepsResponse?.data?.steps) ? stepsResponse.data.steps : defaultSteps)
          .filter((step) => step.title !== 'Rollback');
        const workflowHistory = Array.isArray(historyResponse?.data?.history) ? historyResponse.data.history : [];
        const availableBackups = Array.isArray(backupsResponse?.data?.versions) ? backupsResponse.data.versions : [];

        setSteps(workflowSteps.map((step) => ({ ...step, title: step.title })));
        setHistory(workflowHistory);
        setBackups(availableBackups);
      } catch (err) {
        setError('Unable to load offline update workflow information.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const activeStep = useMemo(() => {
    if (verificationResult?.overall_status === 'VERIFIED') {
      return 2;
    }
    if (packageInfo) {
      return 1;
    }
    return 0;
  }, [packageInfo, verificationResult]);

  const canRunStep = (title) => {
    if (title === 'Import Package') return true;
    if (title === 'Verify Package') return Boolean(packageInfo);
    if (title === 'Install') return verificationResult?.overall_status === 'VERIFIED';
    return true;
  };

  const updateStepStatus = (title, status, description = '') => {
    setSteps((current) =>
      current.map((item) =>
        item.title === title
          ? {
              ...item,
              status,
              description: description || item.description,
            }
          : item
      )
    );
  };

  const handleImportPackage = async () => {
    if (!selectedFile) {
      setError('Choose an AQB update package before importing.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    setWorkingStep('Import Package');
    setError('');

    try {
      const response = await api.post('/offline/import', formData);

      setPackageInfo(response.data);
      setVerificationResult(null);
      setInstallProgress([]);
      updateStepStatus('Import Package', 'Completed', response.data.package_name || 'Package imported successfully.');
      updateStepStatus('Verify Package', 'Ready', 'Verification can now proceed.');
      await loadHistory();
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Unable to import the package.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setWorkingStep('');
    }
  };

  const handleVerifyPackage = async () => {
    if (!packageInfo) {
      setError('Import a package before verifying it.');
      return;
    }

    const formData = new FormData();
    formData.append('session_id', packageInfo.session_id);
    formData.append('package_id', packageInfo.package_id);

    setWorkingStep('Verify Package');
    setError('');

    try {
      const response = await api.post('/offline/verify', {
        session_id: packageInfo.session_id,
        package_id: packageInfo.package_id,
      });

      setVerificationResult(response.data);
      updateStepStatus('Verify Package', 'Verified', 'Manifest, checksum, signature, and malware checks passed.');
      updateStepStatus('Install', 'Queued', 'The package is ready to be installed.');
      await loadHistory();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail?.errors ? detail.errors.join(' | ') : 'Verification failed.');
    } finally {
      setWorkingStep('');
    }
  };

  const handleInstallPackage = async () => {
    if (!packageInfo || !verificationResult?.overall_status) {
      setError('Verify the package before starting installation.');
      return;
    }

    const formData = new FormData();
    formData.append('session_id', packageInfo.session_id);
    formData.append('package_id', packageInfo.package_id);

    setWorkingStep('Install');
    setError('');

    try {
      const response = await api.post('/offline/install', {
        session_id: packageInfo.session_id,
        package_id: packageInfo.package_id,
      });

      setInstallProgress(response.data.progress || []);
      updateStepStatus('Install', response.data.status, response.data.message);
      await loadHistory();
      await loadBackups();
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Installation failed.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setWorkingStep('');
    }
  };

  const handleRollback = async () => {
    if (!rollbackVersion) {
      setError('Select a backup version before rollback.');
      return;
    }

    setWorkingStep('Rollback');
    setError('');

    try {
      const response = await api.post('/offline/rollback', { version: rollbackVersion });
      await loadHistory();
      await loadBackups();
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Rollback failed.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setWorkingStep('');
    }
  };

  const loadBackups = async () => {
    const response = await api.get('/offline/backups');
    setBackups(Array.isArray(response?.data?.versions) ? response.data.versions : []);
  };

  const handleHistoryRefresh = async () => {
    await loadHistory();
    await loadBackups();
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
            Offline Update
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage package import, verification, installation, and deployment history. Rollback is available separately.
          </Typography>
        </Box>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={24} sx={{ color: '#00D4FF' }} />
          <Typography>Loading offline update workflow…</Typography>
        </Box>
      ) : (
        <>
          <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
            <Stepper alternativeLabel activeStep={activeStep}>
              {steps.map((step) => (
                <Step key={step.title}>
                  <StepLabel>{step.title}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Paper>

          <Grid container spacing={2}>
            {steps.map((step) => {
              const disabled = !canRunStep(step.title) || workingStep !== '';
              return (
                <Grid item xs={12} md={6} lg={4} key={step.title}>
                  <Card sx={{ height: '100%', background: 'rgba(15, 23, 42, 0.78)', borderRadius: 3 }}>
                    <CardContent>
                      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                        <Box
                          sx={{
                            width: 38,
                            height: 38,
                            borderRadius: 2,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'rgba(0, 212, 255, 0.12)',
                            color: '#00D4FF',
                          }}
                        >
                          {stepIcons[step.title] || <History fontSize="small" />}
                        </Box>
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                            {step.title}
                          </Typography>
                          <Chip
                            size="small"
                            label={step.status}
                            sx={{ mt: 0.5, background: 'rgba(0, 230, 118, 0.12)', color: '#7CFFB2', borderRadius: 1 }}
                          />
                        </Box>
                      </Stack>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {step.description}
                      </Typography>

                      {step.title === 'Import Package' && (
                        <Stack spacing={1.5}>
                          <TextField
                            type="file"
                            size="small"
                            InputLabelProps={{ shrink: true }}
                            onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                          />
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<FileUpload />}
                            onClick={handleImportPackage}
                            disabled={disabled}
                          >
                            Import Package
                          </Button>
                        </Stack>
                      )}

                      {step.title === 'Verify Package' && (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<Verified />}
                          onClick={handleVerifyPackage}
                          disabled={disabled}
                        >
                          Verify Package
                        </Button>
                      )}

                      {step.title === 'Install' && (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<SystemUpdateAlt />}
                          onClick={handleInstallPackage}
                          disabled={disabled}
                        >
                          Install Update
                        </Button>
                      )}

                      {step.title === 'Update History' && (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<History />}
                          onClick={handleHistoryRefresh}
                          disabled={disabled}
                        >
                          Refresh History
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>

          <Card sx={{ background: 'rgba(15, 23, 42, 0.78)', borderRadius: 3 }}>
            <CardContent>
              <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                <Box
                  sx={{
                    width: 38,
                    height: 38,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'rgba(255, 167, 38, 0.12)',
                    color: '#FFB74D',
                  }}
                >
                  <Undo fontSize="small" />
                </Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    Rollback
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reactivate a previous benchmark version from the registry.
                  </Typography>
                </Box>
              </Stack>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <FormControl size="small" sx={{ minWidth: 220 }}>
                  <InputLabel>Registry Version</InputLabel>
                  <Select
                    label="Registry Version"
                    value={rollbackVersion}
                    onChange={(event) => setRollbackVersion(event.target.value)}
                  >
                    {backups.map((version) => (
                      <MenuItem key={version} value={version}>
                        {version}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant="outlined"
                  startIcon={<Undo />}
                  onClick={handleRollback}
                  disabled={workingStep !== '' || !backups.length || !rollbackVersion}
                >
                  Rollback
                </Button>
              </Stack>
            </CardContent>
          </Card>

          {packageInfo && (
            <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
              <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
                Package Summary
              </Typography>
              <List>
                <ListItem disableGutters>
                  <ListItemText primary="Package Name" secondary={packageInfo.package_name} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Package ID" secondary={packageInfo.package_id} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Version" secondary={packageInfo.version} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Created Date" secondary={packageInfo.created_date} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Status" secondary={packageInfo.status} />
                </ListItem>
              </List>
            </Paper>
          )}

          {verificationResult && (
            <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
              <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
                Verification Summary
              </Typography>
              <List>
                <ListItem disableGutters>
                  <ListItemText primary="Manifest PASS" secondary={verificationResult.manifest_pass ? 'PASS' : 'FAIL'} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Checksum PASS" secondary={verificationResult.checksum_pass ? 'PASS' : 'FAIL'} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Signature PASS" secondary={verificationResult.signature_pass ? 'PASS' : 'FAIL'} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Malware PASS" secondary={verificationResult.malware_pass ? 'PASS' : 'FAIL'} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Overall" secondary={verificationResult.overall_status} />
                </ListItem>
              </List>
            </Paper>
          )}

          {installProgress.length > 0 && (
            <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
              <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
                Installation Progress
              </Typography>
              <List>
                {installProgress.map((item) => (
                  <ListItem key={item} disableGutters>
                    <ListItemIcon sx={{ minWidth: 36, color: '#00D4FF' }}>
                      <CheckCircleOutline />
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
            <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
              Workflow Checklist
            </Typography>
            <List>
              {steps.map((step) => (
                <ListItem key={step.title} disableGutters>
                  <ListItemIcon sx={{ minWidth: 36, color: '#00D4FF' }}>
                    <CheckCircleOutline />
                  </ListItemIcon>
                  <ListItemText primary={step.title} secondary={step.description} />
                </ListItem>
              ))}
            </List>
          </Paper>

          <Paper sx={{ p: 2.5, borderRadius: 3, background: 'rgba(15, 23, 42, 0.75)' }}>
            <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 700 }}>
              Update History
            </Typography>
            <List>
              {history.map((item) => (
                <ListItem key={`${item.id ?? item.package_id}-${item.install_time ?? item.version}`} disableGutters>
                  <ListItemIcon sx={{ minWidth: 36, color: '#00D4FF' }}>
                    <History />
                  </ListItemIcon>
                  <ListItemText
                    primary={`${item.package_name || item.package_id || 'Package'} • ${item.status || item.version || 'Unknown'}`}
                    secondary={`${item.remarks || item.package_name || 'History entry'}${item.installed_by ? ` • ${item.installed_by}` : ''}`}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </>
      )}
    </Box>
  );
}

export default OfflineUpdatePage;
