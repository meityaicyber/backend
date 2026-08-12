import React, { useMemo, useState } from 'react';
import { Box, Button, Card, CardContent, Checkbox, Chip, CircularProgress, FormControl, Grid, InputLabel, MenuItem, Select, TextField, Typography } from '@mui/material';
import { AutoAwesome, CloudUpload, Save } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import api from '../api/axios';

const sources = ['CERT-In', 'CISA', 'Microsoft', 'Cisco', 'NVD', 'Fortinet', 'Palo Alto', 'CrowdStrike', 'Kaspersky', 'Recorded Future', 'Security News', 'Other'];
const sourceTypes = ['Threat Advisory', 'Vulnerability Advisory', 'Security News', 'Incident Report', 'Vendor Bulletin', 'Threat Intelligence Feed', 'Research Paper', 'Blog'];
const sections = [
  ['Basic Information', [['title', 'Title'], ['summary', 'Summary', true], ['keywords', 'Keywords (comma-separated)', false, 'array'], ['language', 'Language']]],
  ['Threat Information', [['threat_type', 'Threat Type'], ['threat_name', 'Threat Name'], ['threat_actor', 'Threat Actor'], ['campaign_name', 'Campaign Name'], ['attack_vector', 'Attack Vector'], ['attack_stage', 'Attack Stage'], ['exploitation_status', 'Exploitation Status']]],
  ['Asset Information', [['vendor', 'Vendor'], ['product', 'Product'], ['product_version', 'Product Version'], ['operating_system', 'Operating System'], ['affected_assets', 'Affected Assets', false, 'array'], ['industry_targets', 'Industry Target', false, 'array']]],
  ['Vulnerability Information', [['cve_ids', 'CVE IDs', false, 'array'], ['cwe_ids', 'CWE IDs', false, 'array'], ['cvss_score', 'CVSS Score'], ['severity', 'Severity'], ['exploit_available', 'Exploit Available', false, 'boolean'], ['exploit_type', 'Exploit Type']]],
  ['Threat Intelligence', [['mitre_tactics', 'MITRE ATT&CK Tactics', false, 'array'], ['mitre_techniques', 'MITRE ATT&CK Techniques', false, 'array'], ['malware_family', 'Malware Family'], ['indicators_of_compromise', 'IOCs: IPs, domains, URLs, hashes, registry keys', true, 'json'], ['yara_rules', 'YARA Rules', true, 'json'], ['sigma_rules', 'Sigma Rules', true, 'json']]],
  ['Risk Assessment', [['business_impact', 'Business Impact', true], ['likelihood', 'Likelihood'], ['risk_level', 'Risk Level'], ['exploit_maturity', 'Exploit Maturity']]],
  ['Mitigation', [['patch_available', 'Patch Available', false, 'boolean'], ['patch_reference', 'Patch Reference', true], ['workaround', 'Workaround', true], ['recommended_actions', 'Recommended Actions', true, 'json']]],
  ['Compliance Mapping', [['nist_controls', 'NIST Controls', false, 'array'], ['iso27001_controls', 'ISO 27001 Controls', false, 'array'], ['cis_controls', 'CIS Controls', false, 'array'], ['certin_guidelines', 'CERT-In Guidance', false, 'array'], ['benchmark_category', 'Benchmark Category']]],
  ['Audit Knowledge', [['audit_questions', 'Audit Questions', true, 'json'], ['expected_controls', 'Expected Controls', true, 'json'], ['required_evidence', 'Required Evidence', true, 'json'], ['expected_artifacts', 'Expected Artifacts', true, 'json'], ['audit_priority', 'Audit Priority']]],
  ['AI Metadata', [['confidence_score', 'Extraction Confidence'], ['extraction_model', 'Extraction Model'], ['reviewed_by_analyst', 'Reviewed', false, 'boolean'], ['status', 'Status']]],
  ['Tags', [['tags', 'Auto-generated Tags', false, 'array']]],
];

const display = (value, type) => type === 'array' ? (value || []).join(', ') : type === 'json' ? JSON.stringify(value || (Array.isArray(value) ? [] : {}), null, 2) : value ?? '';
const parse = (value, type) => type === 'array' ? value.split(',').map(x => x.trim()).filter(Boolean) : type === 'json' ? JSON.parse(value || (value.includes('[') ? '[]' : '{}')) : value;

export default function KnowledgeRegistryPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [file, setFile] = useState(null); const [extracting, setExtracting] = useState(false); const [saving, setSaving] = useState(false);
  const [source, setSource] = useState({ source_name: '', source_type: '', source_url: '', publication_date: '' });
  const [record, setRecord] = useState(null);
  const sourceReady = file && source.source_name && source.source_type;
  const update = (key, value, type) => { try { setRecord(r => ({ ...r, [key]: parse(value, type) })); } catch { setRecord(r => ({ ...r, [key]: value })); } };
  const extract = async () => {
    if (!sourceReady) return; setExtracting(true);
    const data = new FormData(); data.append('file', file); Object.entries(source).forEach(([k, v]) => v && data.append(k, v));
    try { const res = await api.post('/api/knowledge-registry/extract', data); setRecord(res.data); enqueueSnackbar('Knowledge extracted. Review and edit before saving.', { variant: 'success' }); }
    catch (e) { enqueueSnackbar(e.response?.data?.detail || 'Extraction failed.', { variant: 'error' }); } finally { setExtracting(false); }
  };
  const save = async () => { setSaving(true); try { const res = await api.put(`/api/knowledge-registry/${record.knowledge_id}`, record); setRecord(res.data); enqueueSnackbar('Knowledge registry entry saved.', { variant: 'success' }); } catch { enqueueSnackbar('Could not save changes.', { variant: 'error' }); } finally { setSaving(false); } };
  return <Box>
    <Typography variant="h4" fontWeight={800} mb={1}>External Knowledge Registry</Typography>
    <Typography color="text.secondary" mb={3}>Upload a trusted external source. Qwen extracts the knowledge package; every generated field remains editable.</Typography>
    <Card sx={{ mb: 3 }}><CardContent><Typography variant="h6" mb={2}>1. Source Information <Chip size="small" label="Required inputs only" color="primary" /></Typography>
      <Grid container spacing={2}><Grid item xs={12} md={4}><Button component="label" variant="outlined" fullWidth startIcon={<CloudUpload />} sx={{ height: 56 }}>{file ? file.name : 'Upload PDF, DOCX, TXT, or HTML'}<input hidden type="file" accept=".pdf,.docx,.txt,.html,.htm" onChange={e => setFile(e.target.files[0])} /></Button></Grid>
        <Grid item xs={12} md={4}><FormControl fullWidth><InputLabel>Source Name *</InputLabel><Select label="Source Name *" value={source.source_name} onChange={e => setSource(s => ({...s, source_name:e.target.value}))}>{sources.map(x => <MenuItem key={x} value={x}>{x}</MenuItem>)}</Select></FormControl></Grid>
        <Grid item xs={12} md={4}><FormControl fullWidth><InputLabel>Source Type *</InputLabel><Select label="Source Type *" value={source.source_type} onChange={e => setSource(s => ({...s, source_type:e.target.value}))}>{sourceTypes.map(x => <MenuItem key={x} value={x}>{x}</MenuItem>)}</Select></FormControl></Grid>
        <Grid item xs={12} md={6}><TextField fullWidth label="Source URL" value={source.source_url} onChange={e => setSource(s => ({...s, source_url:e.target.value}))} /></Grid><Grid item xs={12} md={6}><TextField fullWidth type="date" label="Publication Date" InputLabelProps={{ shrink: true }} value={source.publication_date} onChange={e => setSource(s => ({...s, publication_date:e.target.value}))} /></Grid></Grid>
      <Button sx={{ mt: 2 }} variant="contained" disabled={!sourceReady || extracting} onClick={extract} startIcon={extracting ? <CircularProgress size={18} /> : <AutoAwesome />}>{extracting ? 'Extracting with Qwen…' : 'Extract & Review'}</Button>
    </CardContent></Card>
    {record && <><Typography variant="h6" mb={2}>2. Review extracted knowledge</Typography>{sections.map(([title, fields]) => <Card key={title} sx={{ mb: 2 }}><CardContent><Typography variant="h6" mb={2}>{title}</Typography><Grid container spacing={2}>{fields.map(([key,label,multiline,type]) => <Grid key={key} item xs={12} md={multiline ? 12 : 6}>{type === 'boolean' ? <Box sx={{ display:'flex', alignItems:'center', height:56 }}><Checkbox checked={Boolean(record[key])} onChange={e => setRecord(r => ({...r,[key]:e.target.checked}))}/><Typography>{label}</Typography></Box> : <TextField fullWidth label={label} multiline={Boolean(multiline || type === 'json')} minRows={multiline || type === 'json' ? 3 : undefined} value={display(record[key], type)} onChange={e => update(key,e.target.value,type)} />}</Grid>)}</Grid></CardContent></Card>)}
      <Button variant="contained" size="large" startIcon={saving ? <CircularProgress size={18} /> : <Save />} disabled={saving} onClick={save}>{saving ? 'Saving…' : 'Save reviewed knowledge'}</Button></>}
  </Box>;
}
