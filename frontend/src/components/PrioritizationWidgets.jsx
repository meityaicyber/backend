import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, TableContainer, Table, TableHead, TableRow, TableCell, TableBody, Chip, Drawer, Divider, LinearProgress, Alert, Paper } from '@mui/material';
import { Reorder, CheckCircle, HourglassEmpty, Block, Info, PieChart as PieChartIcon, Shield } from '@mui/icons-material';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const COLORS = ['#FF1744', '#FF9100', '#FFEA00', '#00E676', '#9E9E9E'];
const LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'];

const glassStyle = {
  backgroundColor: 'rgba(30, 41, 59, 0.7)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.05)',
  boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
};

export const PrioritizationDistribution = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', ...glassStyle }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <Shield sx={{ fontSize: 60, color: '#00E676', mb: 2, opacity: 0.8 }} />
          <Typography variant="h6" color="text.secondary">Inbox Zero</Typography>
        </CardContent>
      </Card>
    );
  }

  const counts = LEVELS.map(level => ({
    name: level,
    value: data.filter(d => d.priority_level === level).length
  })).filter(c => c.value > 0);

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', ...glassStyle }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <PieChartIcon sx={{ color: '#00D4FF' }} />
          <Typography variant="h6" fontWeight={700} color="#e2e8f0">Priority Distribution</Typography>
        </Box>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={counts} innerRadius={50} outerRadius={80} paddingAngle={5} dataKey="value" stroke="none">
              {counts.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[LEVELS.indexOf(entry.name)]} />
              ))}
            </Pie>
            <RechartsTooltip contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: 'none', borderRadius: 8, color: '#fff' }} itemStyle={{ color: '#fff' }} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export const PrioritizationTable = ({ data, meta }) => {
  const [selectedTask, setSelectedTask] = useState(null);

  const getChipColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const getStateIcon = (state) => {
    if (state === 'READY') return <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />;
    if (state === 'WAITING_FOR_RESOURCE') return <HourglassEmpty sx={{ color: 'warning.main', fontSize: 16 }} />;
    if (state === 'BLOCKED') return <Block sx={{ color: 'error.main', fontSize: 16 }} />;
    return <Info sx={{ color: 'info.main', fontSize: 16 }} />;
  };

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', ...glassStyle }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, p: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2, pb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Reorder sx={{ color: '#FF1744' }} />
              <Typography variant="h6" fontWeight={700} color="#e2e8f0">Action Queue</Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">{meta?.data_coverage}</Typography>
          </Box>
          <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ backgroundColor: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8' }}>Task</TableCell>
                  <TableCell sx={{ backgroundColor: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8' }}>Priority</TableCell>
                  <TableCell sx={{ backgroundColor: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8' }}>Score</TableCell>
                  <TableCell sx={{ backgroundColor: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8' }}>State</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data?.map((task) => (
                  <TableRow 
                    key={task.vuln_id} 
                    hover 
                    onClick={() => setSelectedTask(task)} 
                    sx={{ 
                      cursor: 'pointer', 
                      transition: 'all 0.2s',
                      '&:hover': { backgroundColor: 'rgba(0, 212, 255, 0.08) !important', boxShadow: 'inset 4px 0 0 #00D4FF' } 
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="body2" fontWeight={600} color="#f8fafc" noWrap sx={{ maxWidth: 220 }}>{task.title}</Typography>
                        <Typography variant="caption" color="#64748b" noWrap sx={{ maxWidth: 220 }}>
                          {task.agency_name} • {task.affected_assets_count} assets
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" label={task.priority_level} color={getChipColor(task.priority_level)} sx={{ fontWeight: 600, borderRadius: '4px' }} />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ width: 24, color: '#f8fafc' }}>{task.priority_score}</Typography>
                        <LinearProgress variant="determinate" value={task.priority_score} color={getChipColor(task.priority_level)} sx={{ width: 60, height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.1)' }} />
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStateIcon(task.state)}
                        <Typography variant="caption" color="#cbd5e1">{task.state.replace(/_/g, ' ')}</Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
                {!data?.length && (
                  <TableRow>
                    <TableCell colSpan={4} align="center" sx={{ py: 6 }}>
                      <Shield sx={{ fontSize: 40, color: '#00E676', mb: 1, opacity: 0.8 }} />
                      <Typography color="#94a3b8">Inbox Zero. All critical threats neutralized!</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Drawer anchor="right" open={Boolean(selectedTask)} onClose={() => setSelectedTask(null)} PaperProps={{ sx: { width: 450, backgroundColor: '#0f172a', color: '#f8fafc', borderLeft: '1px solid rgba(255,255,255,0.1)' } }}>
        {selectedTask && (
          <Box sx={{ p: 4 }}>
            <Box sx={{ mb: 3 }}>
              <Chip label={selectedTask.priority_level} color={getChipColor(selectedTask.priority_level)} sx={{ mb: 2, fontWeight: 700 }} />
              <Typography variant="h5" fontWeight={800} gutterBottom>{selectedTask.title}</Typography>
              <Typography variant="body2" color="#94a3b8">Agency: {selectedTask.agency_name}</Typography>
            </Box>
            
            <Paper sx={{ p: 2, mb: 3, backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 2 }}>
              <Typography variant="overline" color="#00D4FF">Score Breakdown ({selectedTask.priority_score}/100)</Typography>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={[
                  { subject: 'Impact', A: selectedTask.impact_score, fullMark: 100 },
                  { subject: 'Urgency', A: selectedTask.urgency_score, fullMark: 100 },
                  { subject: 'Resource', A: selectedTask.resource_score || 0, fullMark: 100 },
                ]}>
                  <PolarGrid stroke="rgba(255,255,255,0.2)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#cbd5e1', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Score" dataKey="A" stroke="#00D4FF" fill="#00D4FF" fillOpacity={0.5} />
                  <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', color: '#fff' }} />
                </RadarChart>
              </ResponsiveContainer>
            </Paper>

            <Divider sx={{ my: 3, borderColor: 'rgba(255,255,255,0.1)' }} />
            
            <Typography variant="overline" color="#00D4FF" gutterBottom>Scheduling Status</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2, p: 1.5, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
              {getStateIcon(selectedTask.state)}
              <Box>
                <Typography variant="body2" fontWeight={700}>{selectedTask.state.replace(/_/g, ' ')}</Typography>
                <Typography variant="caption" color="#94a3b8">{selectedTask.state_reason}</Typography>
              </Box>
            </Box>

            <Divider sx={{ my: 3, borderColor: 'rgba(255,255,255,0.1)' }} />
            
            <Typography variant="overline" color="#00D4FF" gutterBottom>System Notes</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
              {selectedTask.explanation?.notes.length > 0 ? (
                selectedTask.explanation.notes.map((note, idx) => (
                  <Alert key={idx} severity="info" variant="outlined" sx={{ color: '#cbd5e1', borderColor: 'rgba(255,255,255,0.2)', '& .MuiAlert-icon': { color: '#00D4FF' } }}>
                    {note}
                  </Alert>
                ))
              ) : (
                <Typography variant="body2" color="#64748b">No special system notes.</Typography>
              )}
            </Box>
          </Box>
        )}
      </Drawer>
    </>
  );
};
