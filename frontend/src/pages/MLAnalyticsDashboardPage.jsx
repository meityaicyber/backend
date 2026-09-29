import React, { useEffect, useState } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
const ResponsiveGridLayout = WidthProvider(Responsive);
import {
  Box, Card, CardContent, Grid, Typography, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Chip, Skeleton, Tooltip, Alert,
  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, OutlinedInput
} from '@mui/material';
import {
  Timeline, Assessment, BubbleChart, ReportProblem, ErrorOutline
} from '@mui/icons-material';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import api from '../api/axios';

const GlassTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <Box sx={{
        background: 'rgba(10, 14, 23, 0.8)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(0, 212, 255, 0.2)',
        borderRadius: 2, p: 2,
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}>
        <Typography variant="subtitle2" sx={{ color: '#E2E8F0', mb: 1, fontWeight: 700 }}>{label}</Typography>
        {payload.map((entry, index) => (
          <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: entry.color }} />
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {entry.name}: <span style={{ color: '#fff', fontWeight: 600 }}>{entry.value}</span>
            </Typography>
          </Box>
        ))}
      </Box>
    );
  }
  return null;
};

export default function MLAnalyticsDashboardPage() {
  const [forecast, setForecast] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [prioritize, setPrioritize] = useState(null);
  const [loading, setLoading] = useState(true);

  const allWidgets = [
    { id: 'forecast', label: '6-Month Vulnerability Forecast' },
    { id: 'clustering', label: 'Agency Risk Clustering' },
    { id: 'topsis', label: 'Prioritized Action Queue' },
    { id: 'anomalies', label: 'Anomalous Agencies' }
  ];
  
  const [visibleWidgets, setVisibleWidgets] = useState(() => {
    const saved = localStorage.getItem('mlVisibleWidgets');
    return saved ? JSON.parse(saved) : allWidgets.map(w => w.id);
  });
  
  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem('mlLayouts');
    return saved ? JSON.parse(saved) : {
      lg: [
        { i: 'forecast', x: 0, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
        { i: 'clustering', x: 6, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
        { i: 'topsis', x: 0, y: 2, w: 7, h: 3, minW: 4, minH: 2 },
        { i: 'anomalies', x: 7, y: 2, w: 5, h: 3, minW: 3, minH: 2 }
      ]
    };
  });

  useEffect(() => {
    localStorage.setItem('mlVisibleWidgets', JSON.stringify(visibleWidgets));
  }, [visibleWidgets]);

  useEffect(() => {
    localStorage.setItem('mlLayouts', JSON.stringify(layouts));
  }, [layouts]);

  const [error, setError] = useState(null);

  useEffect(() => {
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
  }, []);

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" fontWeight={800} sx={{ mb: 4 }}>AI Risk Analytics</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}><Skeleton variant="rounded" height={300} sx={{ borderRadius: 3 }} /></Grid>
          <Grid item xs={12} md={6}><Skeleton variant="rounded" height={300} sx={{ borderRadius: 3 }} /></Grid>
          <Grid item xs={12}><Skeleton variant="rounded" height={400} sx={{ borderRadius: 3 }} /></Grid>
        </Grid>
      </Box>
    );
  }

  // Formatting Forecast Data
  let forecastData = [];
  if (forecast?.status === 'success') {
    const hist = forecast.historical.map(d => ({ date: d.date, actual: d.count }));
    const pred = forecast.forecast.map(d => ({ date: d.date, predicted: d.count }));
    const allDates = [...new Set([...hist.map(h=>h.date), ...pred.map(p=>p.date)])].sort();
    forecastData = allDates.map(date => {
      const h = hist.find(x => x.date === date);
      const p = pred.find(x => x.date === date);
      return { date, actual: h?.actual, predicted: p?.predicted };
    });
  }

  // Formatting Cluster Data
  let clusterData = [];
  if (clusters?.status === 'success') {
    clusterData = clusters.agencies.map(a => ({
      name: a.agency_name,
      cluster: a.cluster,
      x: a.metrics.total_reports,
      y: a.metrics.avg_cvss,
      z: a.metrics.severity_density
    }));
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Assessment sx={{ fontSize: 40, color: '#00D4FF' }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
          <Box>
            <Typography variant="h4" fontWeight={800}>AI Risk Analytics (Air-Gapped)</Typography>
            <Typography variant="body2" color="text.secondary">
              Mathematical Forecasting, Clustering, and Task Prioritization without external models
            </Typography>
          </Box>
          
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      
      {/*  CUSTOMIZABLE GRID LAYOUT  */}
      <ResponsiveGridLayout
        className="layout"
        layouts={Object.keys(layouts).reduce((acc, key) => ({
          ...acc,
          [key]: layouts[key].map(l => ({ ...l, static: !visibleWidgets.includes(l.i) }))
        }), {})}
        onLayoutChange={(currentLayout, allLayouts) => setLayouts(allLayouts)}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={170}
        draggableHandle=".MuiCardContent-root"
      >
    
        <div key="forecast">
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <Timeline sx={{ color: '#00D4FF' }} />
                <Typography variant="h6" fontWeight={700}>6-Month Vulnerability Forecast</Typography>
              </Box>
              {forecast?.status === 'insufficient_data' ? (
                <Alert severity="info">{forecast.message}</Alert>
              ) : (
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={forecastData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" />
                      <YAxis stroke="rgba(255,255,255,0.5)" />
                      <RechartsTooltip content={<GlassTooltip />} />
                      <Line type="monotone" dataKey="actual" name="Historical" stroke="#00E676" strokeWidth={3} dot={{r: 4}} />
                      <Line type="monotone" dataKey="predicted" name="Forecast (Prophet)" stroke="#7C4DFF" strokeWidth={3} strokeDasharray="5 5" dot={{r: 4}} />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </CardContent>
          </Card>
          </div>
        <div key="clustering">
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <BubbleChart sx={{ color: '#7C4DFF' }} />
                <Typography variant="h6" fontWeight={700}>Agency Risk Clustering (HDBSCAN)</Typography>
              </Box>
              {clusters?.status === 'insufficient_data' ? (
                <Alert severity="info">{clusters.message}</Alert>
              ) : (
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="x" type="number" name="Total Reports" stroke="rgba(255,255,255,0.5)" />
                      <YAxis dataKey="y" type="number" name="Avg CVSS" stroke="rgba(255,255,255,0.5)" />
                      <ZAxis dataKey="z" type="number" range={[50, 400]} name="Severity Density" />
                      <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Scatter name="Agencies" data={clusterData} fill="#00D4FF" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </CardContent>
          </Card>
          </div>
        <div key="topsis">
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ReportProblem sx={{ color: '#FF1744' }} />
                <Typography variant="h6" fontWeight={700}>Prioritized Action Queue (TOPSIS)</Typography>
              </Box>
              <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Vulnerability</TableCell>
                      <TableCell>CVSS</TableCell>
                      <TableCell>Days Open</TableCell>
                      <TableCell>Priority Score</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {prioritize?.data?.length === 0 ? (
                      <TableRow><TableCell colSpan={4} align="center">No open tasks</TableCell></TableRow>
                    ) : (
                      prioritize?.data?.slice(0, 8).map((task) => (
                        <TableRow key={task.vuln_id}>
                          <TableCell sx={{ maxWidth: 200 }}><Typography noWrap variant="body2">{task.title}</Typography></TableCell>
                          <TableCell>{task.cvss}</TableCell>
                          <TableCell>{task.days_open}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: '100%', height: 6, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 3 }}>
                                <Box sx={{ width: `${task.priority_score}%`, height: '100%', bgcolor: task.priority_score > 70 ? '#FF1744' : task.priority_score > 40 ? '#FF9100' : '#00E676', borderRadius: 3 }} />
                              </Box>
                              <Typography variant="caption">{task.priority_score}</Typography>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
          </div>
        <div key="anomalies">
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ErrorOutline sx={{ color: '#FF9100' }} />
                <Typography variant="h6" fontWeight={700}>Anomalous Agencies (Isolation Forest)</Typography>
              </Box>
              {anomalies?.status === 'insufficient_data' ? (
                <Alert severity="info">{anomalies.message}</Alert>
              ) : (
                <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Agency</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Score</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {anomalies?.data?.map((agency) => (
                        <TableRow key={agency.agency_id}>
                          <TableCell><Typography noWrap variant="body2">{agency.agency_name}</Typography></TableCell>
                          <TableCell>
                            {agency.is_anomaly ? (
                              <Chip size="small" label="Outlier" color="error" />
                            ) : (
                              <Chip size="small" label="Normal" color="success" />
                            )}
                          </TableCell>
                          <TableCell>{agency.anomaly_score.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
          </div>
      </ResponsiveGridLayout>
    </Box>
  );
}
