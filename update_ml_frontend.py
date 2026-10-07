import re

with open(r'C:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Imports
old_imports = """import {
  Box, Card, CardContent, Grid, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, Skeleton, Tooltip, Alert,
  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, OutlinedInput
} from '@mui/material';"""
new_imports = """import {
  Box, Card, CardContent, Grid, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, Skeleton, Tooltip, Alert,
  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, OutlinedInput,
  Tabs, Tab
} from '@mui/material';"""
content = content.replace(old_imports, new_imports)

# Replace initial states and useEffect for ML
old_states = """export default function MLAnalyticsDashboardPage() {
  const [forecast, setForecast] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [prioritize, setPrioritize] = useState(null);
  const [loading, setLoading] = useState(true);"""
new_states = """export default function MLAnalyticsDashboardPage() {
  const [viewMode, setViewMode] = useState('GLOBAL');
  const [selectedAgencyId, setSelectedAgencyId] = useState('');
  const [selectedFileId, setSelectedFileId] = useState('');
  const [timeRange, setTimeRange] = useState('ALL');
  
  const [agencies, setAgencies] = useState([]);
  const [files, setFiles] = useState([]);

  const [forecast, setForecast] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [prioritize, setPrioritize] = useState(null);
  const [loading, setLoading] = useState(true);"""
content = content.replace(old_states, new_states)


# Replace useEffect logic
old_use_effect = """  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [fRes, cRes, aRes, pRes] = await Promise.allSettled([
          api.get('/api/ml/forecast?months=6'),
          api.get('/api/ml/clusters'),
          api.get('/api/ml/anomalies'),
          api.get('/api/ml/prioritize')
        ]);
        
        if (fRes.status === 'fulfilled') setForecast(fRes.value.data);
        if (cRes.status === 'fulfilled') setClusters(cRes.value.data);
        if (aRes.status === 'fulfilled') setAnomalies(aRes.value.data);
        if (pRes.status === 'fulfilled') setPrioritize(pRes.value.data);
      } catch (err) {
        setError('Failed to fetch ML analytics');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);"""
  
new_use_effect = """  useEffect(() => {
    const fetchDropdownData = async () => {
      try {
        const [agenciesRes, reportsRes] = await Promise.all([
          api.get('/api/agencies'),
          api.get('/api/reports')
        ]);
        setAgencies((agenciesRes.data.agencies || []).map(a => ({ id: a.agency_id, name: a.agency_name })));
        setFiles((reportsRes.data.reports || []).map(r => ({
          id: r.report_id,
          name: r.original_filename,
          agencyId: r.agency?.agency_id,
          date: r.created_at
        })));
      } catch (err) {
        console.error("Failed to fetch dropdown data", err);
      }
    };
    fetchDropdownData();
  }, []);

  useEffect(() => {
    setSelectedFileId('');
  }, [selectedAgencyId]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const queryParams = new URLSearchParams();
        if (viewMode === 'AGENCY' && selectedAgencyId) queryParams.append('agency_id', selectedAgencyId);
        if (viewMode === 'FILE' && selectedFileId) queryParams.append('report_id', selectedFileId);
        if (timeRange !== 'ALL') queryParams.append('time_range', timeRange);
        
        const qs = queryParams.toString();
        const qsPrefix = qs ? `&${qs}` : '';
        const qsAlone = qs ? `?${qs}` : '';

        const [fRes, cRes, aRes, pRes] = await Promise.allSettled([
          api.get(`/api/ml/forecast?months=6${qsPrefix}`),
          api.get(`/api/ml/clusters${qsAlone}`),
          api.get(`/api/ml/anomalies${qsAlone}`),
          api.get(`/api/ml/prioritize${qsAlone}`)
        ]);
        
        if (fRes.status === 'fulfilled') setForecast(fRes.value.data);
        if (cRes.status === 'fulfilled') setClusters(cRes.value.data);
        if (aRes.status === 'fulfilled') setAnomalies(aRes.value.data);
        if (pRes.status === 'fulfilled') setPrioritize(pRes.value.data);
      } catch (err) {
        setError('Failed to fetch ML analytics');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [viewMode, selectedAgencyId, selectedFileId, timeRange]);"""
content = content.replace(old_use_effect, new_use_effect)

# Pre-render state handlers
pre_render_find = """  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>"""
pre_render_replace = """  const handleTabChange = (event, newValue) => {
    setViewMode(newValue);
    if (newValue === 'GLOBAL') {
      setSelectedAgencyId('');
      setSelectedFileId('');
    }
  };

  const agencyFiles = files.filter(f => f.agencyId === selectedAgencyId);

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>"""
content = content.replace(pre_render_find, pre_render_replace)


# UI Changes
old_ui = """        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
            <InputLabel sx={{ color: 'text.secondary' }}>Unlock Widgets</InputLabel>
            <Select
              multiple
              value={visibleWidgets}
              onChange={(e) => setVisibleWidgets(e.target.value)}
              input={<OutlinedInput label="Unlock Widgets" />}
              renderValue={(selected) => `${selected.length} Widgets`}
            >
              {allWidgets.map((w) => (
                <MenuItem key={w.id} value={w.id}>
                  <Checkbox checked={visibleWidgets.indexOf(w.id) > -1} />
                  <ListItemText primary={w.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}"""
new_ui = """        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
            <InputLabel sx={{ color: 'text.secondary' }}>Unlock Widgets</InputLabel>
            <Select
              multiple
              value={visibleWidgets}
              onChange={(e) => setVisibleWidgets(e.target.value)}
              input={<OutlinedInput label="Unlock Widgets" />}
              renderValue={(selected) => `${selected.length} Widgets`}
            >
              {allWidgets.map((w) => (
                <MenuItem key={w.id} value={w.id}>
                  <Checkbox checked={visibleWidgets.indexOf(w.id) > -1} />
                  <ListItemText primary={w.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Box sx={{ bgcolor: 'rgba(17, 24, 39, 0.4)', borderRadius: 2, p: 0.5, border: '1px solid rgba(255,255,255,0.05)' }}>
            <Tabs 
              value={viewMode} 
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              sx={{
                minHeight: 40,
                '& .MuiTab-root': { minHeight: 40, textTransform: 'none', fontWeight: 600, fontSize: '0.85rem' }
              }}
            >
              <Tab label="Global View" value="GLOBAL" />
              <Tab label="Agency View" value="AGENCY" />
              <Tab label="File / Report View" value="FILE" />
            </Tabs>
          </Box>
        </Box>

        </Box>
      </Box>

      {/* ── Filter Controls ── */}
      <Card sx={{ mb: 3.5, background: 'rgba(17, 24, 39, 0.4)', border: '1px solid rgba(255,255,255,0.05)' }}>
        <CardContent sx={{ display: 'flex', gap: 3, alignItems: 'center', flexWrap: 'wrap' }}>
          
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Time Range</InputLabel>
            <Select value={timeRange} label="Time Range" onChange={(e) => setTimeRange(e.target.value)}>
              <MenuItem value="ALL">All Time</MenuItem>
              <MenuItem value="30_DAYS">Last 30 Days</MenuItem>
              <MenuItem value="6_MONTHS">Last 6 Months</MenuItem>
              <MenuItem value="1_YEAR">Last 1 Year</MenuItem>
            </Select>
          </FormControl>

          {/* Scope Filters */}
          {(viewMode === 'AGENCY' || viewMode === 'FILE') && (
            <>
              <Box sx={{ borderLeft: '1px solid rgba(255,255,255,0.1)', height: 32, mx: 1 }} />
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <InputLabel>Select Agency</InputLabel>
                <Select
                  value={selectedAgencyId}
                  label="Select Agency"
                  onChange={(e) => setSelectedAgencyId(e.target.value)}
                >
                  {agencies.map((agency) => (
                    <MenuItem key={agency.id} value={agency.id}>
                      {agency.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {viewMode === 'FILE' && (
                <FormControl size="small" sx={{ minWidth: 240 }} disabled={!selectedAgencyId}>
                  <InputLabel>Select File / Report</InputLabel>
                  <Select
                    value={selectedFileId}
                    label="Select File / Report"
                    onChange={(e) => setSelectedFileId(e.target.value)}
                  >
                    {agencyFiles.map((file) => (
                      <MenuItem key={file.id} value={file.id}>
                        {file.name} ({new Date(file.date).toLocaleDateString()})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}"""
content = content.replace(old_ui, new_ui)

with open(r'C:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
