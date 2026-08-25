import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Card, CardContent, Tabs, Tab, CircularProgress,
  Grid, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Paper, TextField, MenuItem, Select, Dialog, DialogTitle,
  DialogContent, DialogActions, Button, Fade
} from '@mui/material';
import {
  Assessment, EmojiEvents, Science, Timeline, VerifiedUser, Security, BugReport
} from '@mui/icons-material';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid, Legend
} from 'recharts';

const fetchData = async (url) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.statusText}`);
  return await response.json();
};

const CyberCard = ({ children, color = '#00D4FF', glow = false, ...props }) => (
  <Card 
    sx={{ 
      bgcolor: 'rgba(10, 14, 23, 0.7)', 
      backdropFilter: 'blur(10px)',
      border: `1px solid ${glow ? color : 'rgba(255,255,255,0.1)'}`,
      boxShadow: glow ? `0 0 15px ${color}33` : 'none',
      color: '#fff',
      transition: 'all 0.3s ease',
      '&:hover': {
        borderColor: color,
        boxShadow: `0 0 20px ${color}40`,
        transform: 'translateY(-2px)'
      },
      ...props.sx 
    }}
  >
    {children}
  </Card>
);

export default function PerformanceMonitoringPage() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({});

  useEffect(() => {
    const loadAll = async () => {
      try {
        const [ranking, scores, dataset, models, versions, tests] = await Promise.all([
          fetchData('/data/ranking_summary.json'),
          fetchData('/data/organisation_scores.json'),
          fetchData('/data/sample_dataset.json'),
          fetchData('/data/comparison_summary.json'),
          fetchData('/data/version_registry.json'),
          fetchData('/data/test_report.json')
        ]);
        setData({ ranking, scores, dataset, models, versions, tests });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadAll();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="60vh">
        <CircularProgress sx={{ color: '#00D4FF' }} size={60} thickness={4} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Typography color="error" variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BugReport /> Error loading authoritative data: {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Fade in timeout={800}>
      <Box p={4} sx={{ maxWidth: 1400, margin: '0 auto', minHeight: '100vh' }}>
        <Box display="flex" alignItems="center" gap={2} mb={1}>
          <Assessment sx={{ fontSize: 40, color: '#00D4FF', filter: 'drop-shadow(0 0 8px rgba(0,212,255,0.5))' }} />
          <Typography variant="h3" sx={{ 
            fontWeight: 900, 
            background: 'linear-gradient(135deg, #00D4FF, #00E676)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            letterSpacing: '1px'
          }}>
            Performance Monitoring
          </Typography>
        </Box>
        <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.6)', mb: 4, ml: 7 }}>
          Live authoritative analysis, continuous scoring, and model diagnostics.
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'rgba(255,255,255,0.1)', mb: 4 }}>
          <Tabs 
            value={tabValue} 
            onChange={(_, v) => setTabValue(v)} 
            variant="scrollable"
            scrollButtons="auto"
            sx={{ 
              '& .MuiTab-root': { color: 'rgba(255,255,255,0.5)', fontWeight: 600, fontSize: '0.95rem', textTransform: 'none' }, 
              '& .Mui-selected': { color: '#00D4FF !important' },
              '& .MuiTabs-indicator': { backgroundColor: '#00D4FF', height: 3, borderRadius: '3px 3px 0 0' }
            }}
          >
            <Tab icon={<Timeline fontSize="small" />} iconPosition="start" label="Overview" />
            <Tab icon={<EmojiEvents fontSize="small" />} iconPosition="start" label="Ranking" />
            <Tab icon={<Science fontSize="small" />} iconPosition="start" label="Model Comparison" />
            <Tab icon={<Security fontSize="small" />} iconPosition="start" label="Data Quality" />
            <Tab icon={<VerifiedUser fontSize="small" />} iconPosition="start" label="Versions" />
            <Tab icon={<BugReport fontSize="small" />} iconPosition="start" label="Acceptance Tests" />
          </Tabs>
        </Box>

        <Box sx={{ minHeight: 500 }}>
          {tabValue === 0 && <OverviewTab data={data} />}
          {tabValue === 1 && <RankingTab data={data} />}
          {tabValue === 2 && <ModelsTab data={data} />}
          {tabValue === 3 && <QualityTab data={data} />}
          {tabValue === 4 && <VersionsTab data={data} />}
          {tabValue === 5 && <TestsTab data={data} />}
        </Box>
      </Box>
    </Fade>
  );
}

function OverviewTab({ data }) {
  const { ranking, scores } = data;
  const validScores = scores.filter(s => s.assessment_status === 'assessable');
  const avgScore = validScores.reduce((acc, s) => acc + s.performance_score, 0) / validScores.length;
  const renewedCount = validScores.filter(s => s.renewal_prediction?.class === 'renewed').length;
  
  const pieData = [
    { name: 'Renewed', value: renewedCount, color: '#00E676' },
    { name: 'Not Renewed', value: validScores.length - renewedCount, color: '#FF3D00' },
  ];

  const bins = Array(10).fill(0);
  validScores.forEach(s => {
    const binIndex = Math.min(Math.floor(s.performance_score / 10), 9);
    bins[binIndex]++;
  });
  const distData = bins.map((count, i) => ({ range: `${i * 10}-${i * 10 + 9}`, count }));

  return (
    <Fade in timeout={500}>
      <Box>
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={3}>
            <CyberCard glow color="#00D4FF">
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Total Organisations</Typography>
                <Typography variant="h3" fontWeight="bold">{ranking.metadata.total_organisations}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <CyberCard color="#00E676">
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Assessable Entities</Typography>
                <Typography variant="h3" fontWeight="bold" color="#00E676">{ranking.metadata.assessable_organisations}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <CyberCard color="#B388FF">
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Mean Performance</Typography>
                <Typography variant="h3" fontWeight="bold" color="#B388FF">{avgScore.toFixed(1)}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <CyberCard color="#FF3D00" glow={scores.length > validScores.length}>
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.8, letterSpacing: 1 }}>Rejected / Unassessable</Typography>
                <Typography variant="h3" fontWeight="bold" color="#FF3D00">{scores.length - validScores.length}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
        </Grid>

        <Grid container spacing={4}>
          <Grid item xs={12} md={5}>
            <CyberCard>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2, fontWeight: 600 }}>Prediction Distribution</Typography>
                <Box height={320}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={70} outerRadius={100} label={{ fill: '#fff', fontSize: 12 }}>
                        {pieData.map((entry, index) => <Cell key={index} fill={entry.color} />)}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(10,14,23,0.9)', border: '1px solid #333', borderRadius: 8, color: '#fff' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} md={7}>
            <CyberCard>
              <CardContent>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2, fontWeight: 600 }}>Performance Score Histogram</Typography>
                <Box height={320}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distData} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="range" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 12 }} />
                      <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 12 }} />
                      <Tooltip 
                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                        contentStyle={{ backgroundColor: 'rgba(10,14,23,0.9)', border: '1px solid #00D4FF', borderRadius: 8, color: '#fff' }} 
                      />
                      <Bar dataKey="count" fill="url(#colorGlow)" radius={[4,4,0,0]} />
                      <defs>
                        <linearGradient id="colorGlow" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00D4FF" stopOpacity={1}/>
                          <stop offset="100%" stopColor="#0077FF" stopOpacity={0.6}/>
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </CyberCard>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  );
}

function RankingTab({ data }) {
  const { scores, dataset } = data;
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedOrg, setSelectedOrg] = useState(null);

  const filtered = scores.filter(s => {
    if (search && !s.organisation_id.toLowerCase().includes(search.toLowerCase())) return false;
    if (filter === 'renewed' && s.renewal_prediction?.class !== 'renewed') return false;
    if (filter === 'not_renewed' && s.renewal_prediction?.class !== 'not_renewed') return false;
    if (filter === 'borderline' && s.renewal_prediction?.boundary_status !== 'close_to_decision_boundary') return false;
    if (filter === 'not_assessable' && s.assessment_status !== 'not_assessable') return false;
    return true;
  });

  const getOrgDetails = (id) => {
    const s = scores.find(x => x.organisation_id === id);
    const f = dataset.data.find(x => x.organisation_id === id);
    setSelectedOrg({ score: s, feature: f });
  };

  return (
    <Fade in timeout={500}>
      <Box>
        <Box display="flex" gap={2} mb={3}>
          <TextField
            size="small"
            placeholder="Search Organisation ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ 
              width: 300,
              input: { color: '#fff' }, 
              bgcolor: 'rgba(0,0,0,0.3)', 
              borderRadius: 1,
              '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
              '&:hover fieldset': { borderColor: '#00D4FF !important' }
            }}
          />
          <Select
            size="small"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{ 
              color: '#fff', 
              bgcolor: 'rgba(0,0,0,0.3)',
              '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
              '&:hover fieldset': { borderColor: '#00D4FF !important' },
              '& .MuiSvgIcon-root': { color: '#fff' }
            }}
          >
            <MenuItem value="all">All Outcomes</MenuItem>
            <MenuItem value="renewed">Renewed (Predicted)</MenuItem>
            <MenuItem value="not_renewed">Not Renewed (Predicted)</MenuItem>
            <MenuItem value="borderline">Borderline Risk</MenuItem>
            <MenuItem value="not_assessable">Not Assessable</MenuItem>
          </Select>
        </Box>

        <TableContainer component={Paper} sx={{ bgcolor: 'rgba(10,14,23,0.7)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)', maxHeight: 650 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {['Rank', 'Organisation ID', 'Performance Score', 'AI Prediction', 'Probability', 'Risk Boundary'].map((head) => (
                  <TableCell key={head} sx={{ bgcolor: '#0b111e', color: '#00D4FF', fontWeight: 'bold', borderBottom: '2px solid rgba(0,212,255,0.3)' }}>
                    {head}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.slice(0, 100).map(s => (
                <TableRow key={s.organisation_id} hover sx={{ '&:hover': { bgcolor: 'rgba(0,212,255,0.05)' }, '& td': { borderBottom: '1px solid rgba(255,255,255,0.05)' } }}>
                  <TableCell sx={{ color: '#fff', fontWeight: 'bold', fontFamily: 'monospace' }}>{s.rank ?? '-'}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => getOrgDetails(s.organisation_id)} sx={{ color: '#fff', textTransform: 'none', '&:hover': { color: '#00D4FF', textDecoration: 'underline' } }}>
                      {s.organisation_id}
                    </Button>
                  </TableCell>
                  <TableCell sx={{ color: '#fff', fontFamily: 'monospace', fontSize: '1.1rem' }}>{s.performance_score.toFixed(2)}</TableCell>
                  <TableCell>
                    {s.assessment_status === 'not_assessable' ? (
                      <Chip label="N/A" size="small" sx={{ bgcolor: 'rgba(255,255,255,0.1)', color: '#ccc', fontWeight: 600 }} />
                    ) : (
                      <Chip 
                        label={s.renewal_prediction.class.toUpperCase()} 
                        size="small" 
                        sx={{ 
                          bgcolor: s.renewal_prediction.class === 'renewed' ? 'rgba(0,230,118,0.15)' : 'rgba(255,61,0,0.15)', 
                          color: s.renewal_prediction.class === 'renewed' ? '#00E676' : '#FF3D00',
                          border: `1px solid ${s.renewal_prediction.class === 'renewed' ? '#00E676' : '#FF3D00'}`,
                          fontWeight: 700 
                        }} 
                      />
                    )}
                  </TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)', fontFamily: 'monospace' }}>{s.renewal_prediction?.probability.toFixed(3) ?? '-'}</TableCell>
                  <TableCell>
                    {s.renewal_prediction?.boundary_status === 'close_to_decision_boundary' && (
                      <Chip label="Borderline" size="small" sx={{ bgcolor: 'rgba(255,193,7,0.15)', color: '#FFC107', border: '1px solid #FFC107', fontWeight: 600 }} />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Detail Dialog */}
        <Dialog open={!!selectedOrg} onClose={() => setSelectedOrg(null)} maxWidth="md" fullWidth PaperProps={{ sx: { bgcolor: '#0b111e', border: '1px solid #00D4FF', color: '#fff', backgroundImage: 'none' } }}>
          <DialogTitle sx={{ borderBottom: '1px solid rgba(0,212,255,0.3)', pb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Assessment sx={{ color: '#00D4FF' }} />
            <Typography variant="h5" fontWeight="bold">Entity Inspection: {selectedOrg?.score.organisation_id}</Typography>
          </DialogTitle>
          <DialogContent sx={{ mt: 3 }}>
            {selectedOrg && (
              <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                  <Typography variant="overline" sx={{ color: '#00D4FF', mb: 2, display: 'block', fontSize: '1rem', letterSpacing: 1 }}>Feature Vector</Typography>
                  <Box sx={{ bgcolor: 'rgba(0,0,0,0.3)', p: 2, borderRadius: 2, border: '1px solid rgba(255,255,255,0.1)' }}>
                    {Object.entries(selectedOrg.feature.features).map(([key, val]) => (
                      <Box key={key} display="flex" justifyContent="space-between" mb={1.5} sx={{ borderBottom: '1px dashed rgba(255,255,255,0.1)', pb: 1 }}>
                        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </Typography>
                        <Typography variant="body2" fontFamily="monospace" sx={{ color: val === null ? '#FF3D00' : '#fff', fontWeight: 600 }}>
                          {val === null ? 'NULL (Missing)' : typeof val === 'object' ? JSON.stringify(val) : String(val)}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="overline" sx={{ color: '#00E676', mb: 2, display: 'block', fontSize: '1rem', letterSpacing: 1 }}>Computed Output</Typography>
                  <Box sx={{ bgcolor: 'rgba(0,230,118,0.05)', p: 3, borderRadius: 2, border: '1px solid rgba(0,230,118,0.2)', mb: 3 }}>
                    <Typography variant="body2" sx={{ opacity: 0.7 }}>Final Score</Typography>
                    <Typography variant="h2" mb={1} color="#00E676" fontWeight="bold">{selectedOrg.score.performance_score.toFixed(2)}</Typography>
                    <Typography variant="body2" sx={{ opacity: 0.7 }}>Global Rank: <strong>#{selectedOrg.score.rank}</strong></Typography>
                  </Box>
                  
                  <Typography variant="overline" sx={{ color: '#aaa', mb: 1, display: 'block' }}>Traceability Metadata</Typography>
                  <Box sx={{ bgcolor: 'rgba(0,0,0,0.3)', p: 2, borderRadius: 2 }}>
                    {Object.entries(selectedOrg.score.provenance).map(([key, val]) => (
                      <Box key={key} display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2" sx={{ opacity: 0.6 }}>{key.replace(/_/g, ' ')}</Typography>
                        <Typography variant="body2" fontFamily="monospace" color="#00D4FF">{val}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Grid>
              </Grid>
            )}
          </DialogContent>
          <DialogActions sx={{ borderTop: '1px solid rgba(255,255,255,0.1)', p: 2 }}>
            <Button onClick={() => setSelectedOrg(null)} variant="outlined" sx={{ color: '#fff', borderColor: 'rgba(255,255,255,0.3)' }}>Close Window</Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Fade>
  );
}

function ModelsTab({ data }) {
  const chartData = Object.entries(data.models).map(([model, metrics]) => ({
    name: model.replace(/_/g, ' ').toUpperCase(),
    accuracy: Number(metrics.accuracy.toFixed(3)),
    macro_f1: Number(metrics.macro_f1.toFixed(3)),
    isProduction: model === 'gradient_boosting'
  }));

  return (
    <Fade in timeout={500}>
      <Box>
        <CyberCard sx={{ mb: 4 }} glow color="#B388FF">
          <CardContent>
            <Typography variant="h6" sx={{ color: '#fff', mb: 3, fontWeight: 600 }}>Classification Engine Performance</Typography>
            <Box height={450}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" tick={{ fill: '#fff', fontSize: 13 }} />
                  <YAxis domain={[0, 1]} stroke="rgba(255,255,255,0.5)" />
                  <Tooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }} 
                    contentStyle={{ backgroundColor: 'rgba(10,14,23,0.9)', border: '1px solid #B388FF', borderRadius: 8, color: '#fff' }} 
                  />
                  <Legend wrapperStyle={{ paddingTop: 20 }} />
                  <Bar dataKey="accuracy" name="Accuracy" fill="#00D4FF" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="macro_f1" name="Macro F1" fill="#B388FF" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </CardContent>
        </CyberCard>
      </Box>
    </Fade>
  );
}

function QualityTab({ data }) {
  const { scores } = data;
  const notAssessable = scores.filter(s => s.assessment_status === 'not_assessable');
  return (
    <Fade in timeout={500}>
      <Box>
        <CyberCard color="#FF3D00">
          <CardContent>
            <Typography variant="h6" sx={{ color: '#FF3D00', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Security /> Dropped / Unassessable Organisations
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
              Entities with excessive missing data (&gt;{2} features missing) are automatically rejected by the pipeline to prevent hallucinated scores.
            </Typography>
            <TableContainer sx={{ bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: '#fff', borderBottom: '1px solid rgba(255,61,0,0.3)', fontWeight: 'bold' }}>Organisation ID</TableCell>
                    <TableCell sx={{ color: '#fff', borderBottom: '1px solid rgba(255,61,0,0.3)', fontWeight: 'bold' }}>Missing Count</TableCell>
                    <TableCell sx={{ color: '#fff', borderBottom: '1px solid rgba(255,61,0,0.3)', fontWeight: 'bold' }}>Missing Feature Keys</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {notAssessable.map(s => (
                    <TableRow key={s.organisation_id} sx={{ '& td': { borderBottom: '1px solid rgba(255,255,255,0.05)' } }}>
                      <TableCell sx={{ color: '#fff', fontFamily: 'monospace' }}>{s.organisation_id}</TableCell>
                      <TableCell>
                        <Chip label={s.missing_features.length} sx={{ bgcolor: 'rgba(255,61,0,0.2)', color: '#FF3D00', fontWeight: 'bold', border: '1px solid #FF3D00' }} size="small" />
                      </TableCell>
                      <TableCell sx={{ color: '#aaa', fontFamily: 'monospace' }}>{s.missing_features.join(', ')}</TableCell>
                    </TableRow>
                  ))}
                  {notAssessable.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} sx={{ color: '#00E676', textAlign: 'center', py: 4 }}>
                        Clean dataset! No records were dropped.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </CyberCard>
      </Box>
    </Fade>
  );
}

function VersionsTab({ data }) {
  return (
    <Fade in timeout={500}>
      <Box>
        <Typography variant="h5" sx={{ color: '#fff', mb: 1, fontWeight: 'bold' }}>Immutable Configuration History</Typography>
        <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.6)', mb: 4 }}>
          Cryptographic ledger of all schema, weight, and model changes.
        </Typography>
        
        <Box sx={{ borderLeft: '2px solid rgba(0,212,255,0.3)', ml: 2, pl: 4, py: 2 }}>
          {data.versions.history.slice().reverse().map((entry, i) => (
            <Box key={i} sx={{ position: 'relative', mb: 5 }}>
              <Box sx={{ 
                position: 'absolute', width: 14, height: 14, borderRadius: '50%', 
                bgcolor: '#0b111e', border: '3px solid #00D4FF', left: -41, top: 4,
                boxShadow: '0 0 10px #00D4FF'
              }} />
              <Typography variant="caption" sx={{ color: '#00D4FF', letterSpacing: 1, fontWeight: 600 }}>
                {new Date(entry.timestamp).toLocaleString()}
              </Typography>
              <CyberCard sx={{ mt: 1, p: 2 }}>
                <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>{entry.change}</Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)', mb: 2 }}>
                  Approved by: <strong style={{ color: '#fff' }}>{entry.approver}</strong>
                </Typography>
                {entry.updated_components.map(c => (
                  <Box key={c.component} display="flex" gap={2} alignItems="center" sx={{ bgcolor: 'rgba(0,0,0,0.3)', p: 1, borderRadius: 1 }}>
                    <Chip label={c.component} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.1)', color: '#fff', fontFamily: 'monospace' }} />
                    <Typography variant="body2" sx={{ textDecoration: 'line-through', color: '#FF3D00' }}>v{c.old_version}</Typography>
                    <Typography variant="body2" sx={{ color: '#00E676', fontWeight: 'bold' }}>v{c.new_version}</Typography>
                  </Box>
                ))}
              </CyberCard>
            </Box>
          ))}
        </Box>
      </Box>
    </Fade>
  );
}

function TestsTab({ data }) {
  const { summary, tests } = data.tests;
  return (
    <Fade in timeout={500}>
      <Box>
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} md={3}>
            <CyberCard>
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Automated Assertions</Typography>
                <Typography variant="h3" fontWeight="bold">{summary.total}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} md={3}>
            <CyberCard color="#00E676">
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Tests Passed</Typography>
                <Typography variant="h3" fontWeight="bold" color="#00E676">{summary.passed}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} md={3}>
            <CyberCard color={summary.failed > 0 ? "#FF3D00" : "#00E676"} glow={summary.failed > 0}>
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Tests Failed</Typography>
                <Typography variant="h3" fontWeight="bold" color={summary.failed > 0 ? "#FF3D00" : "#00E676"}>{summary.failed || 0}</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
          <Grid item xs={12} md={3}>
            <CyberCard color="#B388FF">
              <CardContent>
                <Typography variant="overline" sx={{ opacity: 0.7, letterSpacing: 1 }}>Execution Duration</Typography>
                <Typography variant="h3" fontWeight="bold" color="#B388FF">{(summary.duration || 0).toFixed(2)}s</Typography>
              </CardContent>
            </CyberCard>
          </Grid>
        </Grid>
        
        <CyberCard>
          <TableContainer sx={{ maxHeight: 600 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ bgcolor: '#0b111e', color: '#fff', borderBottom: '2px solid rgba(255,255,255,0.1)' }}>Test Assertion Identity</TableCell>
                  <TableCell sx={{ bgcolor: '#0b111e', color: '#fff', borderBottom: '2px solid rgba(255,255,255,0.1)' }}>Status</TableCell>
                  <TableCell sx={{ bgcolor: '#0b111e', color: '#fff', borderBottom: '2px solid rgba(255,255,255,0.1)' }}>Compute Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tests.map(t => (
                  <TableRow key={t.nodeid} sx={{ '& td': { borderBottom: '1px solid rgba(255,255,255,0.05)' } }}>
                    <TableCell sx={{ color: '#fff', fontFamily: 'monospace' }}>{t.nodeid.split('::').pop()}</TableCell>
                    <TableCell>
                      {t.outcome === 'passed' ? (
                        <Chip label="PASS" size="small" sx={{ bgcolor: 'rgba(0,230,118,0.15)', color: '#00E676', border: '1px solid #00E676', fontWeight: 'bold' }} />
                      ) : (
                        <Chip label="FAIL" size="small" sx={{ bgcolor: 'rgba(255,61,0,0.15)', color: '#FF3D00', border: '1px solid #FF3D00', fontWeight: 'bold' }} />
                      )}
                    </TableCell>
                    <TableCell sx={{ color: '#aaa', fontFamily: 'monospace' }}>{(t.call?.duration || 0).toFixed(3)}s</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CyberCard>
      </Box>
    </Fade>
  );
}
