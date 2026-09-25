import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/ReportsPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Summary calculation
old_summary_calc = """  const execSummary = results.executive_summary || {};
  const vulnsArray = results.detailed_observations || [];
  const compliance = results.compliance || {};
  const recommendations = results.recommendations || [];
  
  let riskLevel = 'LOW';
  const crit = execSummary.critical_count || 0;
  const high = execSummary.high_count || 0;
  const med = execSummary.medium_count || 0;
  const low = execSummary.low_count || 0;
  
  if (crit > 0) riskLevel = 'CRITICAL';
  else if (high > 0) riskLevel = 'HIGH';
  else if (med > 0) riskLevel = 'MEDIUM';"""

new_summary_calc = """  const execSummary = results.executive_summary || {};
  const vulnsArray = results.detailed_observations || [];
  const compliance = results.compliance || {};
  const recommendations = results.recommendations || [];
  
  const crit = vulnsArray.filter(v => (v.severity || '').toUpperCase() === 'CRITICAL').length;
  const high = vulnsArray.filter(v => (v.severity || '').toUpperCase() === 'HIGH').length;
  const med = vulnsArray.filter(v => (v.severity || '').toUpperCase() === 'MEDIUM').length;
  const low = vulnsArray.filter(v => (v.severity || '').toUpperCase() === 'LOW').length;
  const totalVulns = vulnsArray.length;
  
  let riskLevel = 'LOW';
  if (crit > 0) riskLevel = 'CRITICAL';
  else if (high > 0) riskLevel = 'HIGH';
  else if (med > 0) riskLevel = 'MEDIUM';"""

content = content.replace(old_summary_calc, new_summary_calc)

# Replace total count
content = content.replace('{execSummary.total_detailed_observations || 0}', '{totalVulns}')

old_vuln_block = re.search(r'<Box sx=\{\{ pl: 1, pr: 1 \}\}>\s*\{\(vulnsArray\)\.map\(\(v, i\) => \([\s\S]*?<\/Box>\s*\)\)\}\s*<\/Box>', content).group(0)

new_vuln_block = """
            <Box sx={{ pl: 1, pr: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {(vulnsArray).map((v, i) => (
                <Box
                  key={v.finding_id || i}
                  sx={{
                    p: 2.5,
                    borderRadius: 3,
                    border: `1px solid ${severityColor[v.severity] || '#aaa'}40`,
                    bgcolor: 'rgba(0,0,0,0.2)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <Box sx={{ position: 'absolute', top: 0, left: 0, width: 4, height: '100%', bgcolor: severityColor[v.severity] || '#aaa' }} />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5, pl: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                      <Typography variant="h6" fontWeight={700} sx={{ color: '#fff' }}>
                        {v.title}
                      </Typography>
                      <Chip label={v.severity} size="small" sx={{ fontWeight: 800, fontSize: '0.65rem', bgcolor: `${severityColor[v.severity] || '#aaa'}25`, color: severityColor[v.severity] || '#aaa', borderRadius: 1 }} />
                      {v.status && <Chip label={v.status} size="small" sx={{ fontWeight: 600, fontSize: '0.65rem', bgcolor: 'rgba(255,255,255,0.1)', color: '#ddd', borderRadius: 1 }} />}
                      {v.new_or_repeat && <Chip label={v.new_or_repeat} size="small" sx={{ fontWeight: 600, fontSize: '0.65rem', bgcolor: 'rgba(255,255,255,0.1)', color: '#ddd', borderRadius: 1 }} />}
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {v.cvss_score && (
                        <Chip label={`CVSS: ${v.cvss_score}`} size="small" sx={{ fontWeight: 700, bgcolor: 'rgba(0,212,255,0.15)', color: '#00D4FF' }} />
                      )}
                      {v.reported_epss_score && (
                        <Chip label={`EPSS: ${v.reported_epss_score}`} size="small" sx={{ fontWeight: 700, bgcolor: 'rgba(156,39,176,0.15)', color: '#E1BEE7' }} />
                      )}
                    </Box>
                  </Box>

                  <Box sx={{ pl: 1 }}>
                    {v.finding_id && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5, fontFamily: 'monospace' }}>
                        ID: {v.finding_id}
                      </Typography>
                    )}
                    
                    <Typography variant="body2" sx={{ color: '#ccc', mb: 2, lineHeight: 1.6 }}>
                      {v.observation_description}
                    </Typography>

                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2, mb: 2, p: 2, bgcolor: 'rgba(0,0,0,0.3)', borderRadius: 2 }}>
                      {v.impact_level && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">IMPACT LEVEL</Typography>
                          <Typography variant="body2" color="#fff">{v.impact_level}</Typography>
                        </Box>
                      )}
                      {v.likelihood_level && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">LIKELIHOOD</Typography>
                          <Typography variant="body2" color="#fff">{v.likelihood_level}</Typography>
                        </Box>
                      )}
                      {v.cve_id && v.cve_id.length > 0 && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">CVE IDs</Typography>
                          <Typography variant="body2" color="#fff" sx={{fontFamily: 'monospace'}}>{v.cve_id.join(', ')}</Typography>
                        </Box>
                      )}
                      {v.cwe && v.cwe.length > 0 && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">CWE</Typography>
                          <Typography variant="body2" color="#fff" sx={{fontFamily: 'monospace'}}>{v.cwe.join(', ')}</Typography>
                        </Box>
                      )}
                      {v.affected_asset && v.affected_asset.length > 0 && (
                        <Box>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">AFFECTED ASSETS</Typography>
                          <Typography variant="body2" color="#fff">{v.affected_asset.join(', ')}</Typography>
                        </Box>
                      )}
                      {v.cvss_vector && (
                        <Box sx={{ gridColumn: '1 / -1' }}>
                          <Typography variant="caption" color="text.secondary" fontWeight={600} display="block">CVSS VECTOR</Typography>
                          <Typography variant="body2" color="#fff" sx={{fontFamily: 'monospace'}}>{v.cvss_vector}</Typography>
                        </Box>
                      )}
                    </Box>

                    {v.severity_rationale && (
                      <Box sx={{ mb: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" gutterBottom>SEVERITY RATIONALE</Typography>
                        <Typography variant="body2" color="#ccc">{v.severity_rationale}</Typography>
                      </Box>
                    )}
                    
                    {v.impact && (
                      <Box sx={{ mb: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" gutterBottom>IMPACT</Typography>
                        <Typography variant="body2" color="#ccc">{v.impact}</Typography>
                      </Box>
                    )}

                    {v.likely_root_cause && (
                      <Box sx={{ mb: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" gutterBottom>ROOT CAUSE</Typography>
                        <Typography variant="body2" color="#ccc">{v.likely_root_cause}</Typography>
                      </Box>
                    )}

                    {v.preconditions && (
                      <Box sx={{ mb: 1.5 }}>
                        <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" gutterBottom>PRECONDITIONS</Typography>
                        <Typography variant="body2" color="#ccc">{v.preconditions}</Typography>
                      </Box>
                    )}

                    {v.recommendation && (
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(0, 230, 118, 0.05)', borderLeft: '3px solid #00E676', borderRadius: '0 4px 4px 0', mt: 2 }}>
                        <Typography variant="caption" sx={{ color: '#00E676', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <TipsAndUpdates fontSize="small" /> RECOMMENDATION
                        </Typography>
                        <Typography variant="body2" color="#ddd">{v.recommendation}</Typography>
                      </Box>
                    )}
                  </Box>
                </Box>
              ))}
            </Box>
"""

content = content.replace(old_vuln_block, new_vuln_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
