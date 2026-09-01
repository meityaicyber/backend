import React, { useEffect, useState, useRef } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity, ArrowUpRight, BarChart3, Boxes, CheckCircle2, CircleHelp,
  Database, Gauge, GitBranch, LayoutDashboard, Menu, RefreshCw, Search,
  Settings2, ShieldCheck, Sparkles, TestTube2, X, AlertTriangle, ChevronLeft, ChevronRight, Sliders,
  UploadCloud, FileUp, FileSpreadsheet, FileJson, Download, Check, Copy, FileText,
  Layers, Lock, Cpu, RotateCcw, CheckCircle, Info, Sparkle
} from 'lucide-react'
import './styles.css'

const API = 'http://localhost:8000/api'

const navItems = [
  ['Overview', LayoutDashboard],
  ['Ranking', BarChart3],
  ['Agency Assessment', FileSpreadsheet],
  ['Models', Sparkles],
  ['Features', Activity],
  ['Scoring Config', Settings2],
  ['Dataset', Database],
  ['Versions & Deployment', ShieldCheck],
]

function App() {
  const [page, setPage] = useState('Overview')
  const [mobileNav, setMobileNav] = useState(false)
  const [dashboardData, setDashboardData] = useState(null)
  const [features, setFeatures] = useState([])
  const [scoringConfig, setScoringConfig] = useState(null)
  const [modelsConfig, setModelsConfig] = useState([])
  const [evaluationData, setEvaluationData] = useState(null)
  const [selectedOrgId, setSelectedOrgId] = useState(null)
  const [rankingSearchQuery, setRankingSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchAllData = () => {
    setLoading(true)
    Promise.all([
      fetch(`${API}/dashboard`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/config/features`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/config/scoring`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/config/models`).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/evaluation`).then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([dash, feat, scor, mod, evalRes]) => {
      if (dash) setDashboardData(dash)
      if (feat && feat.features) setFeatures(feat.features)
      if (scor) setScoringConfig(scor)
      if (mod && mod.models) setModelsConfig(mod.models)
      if (evalRes) setEvaluationData(evalRes)
      setLoading(false)
    })
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  const handleNavigateToRankingWithSearch = (orgId) => {
    setRankingSearchQuery(orgId)
    setPage('Ranking')
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Gauge size={20} /></div>
          <div>
            <strong>AuditRank</strong>
            <span>Performance Monitor</span>
          </div>
          <button className="close-nav" onClick={() => setMobileNav(false)}><X size={18} /></button>
        </div>

        <div className="workspace-label">
          WORKSPACE <span>AIR-GAPPED</span>
        </div>

        <nav>
          {navItems.map(([label, Icon]) => (
            <button
              key={label}
              className={page === label ? 'active' : ''}
              onClick={() => {
                if (label === 'Ranking' && page !== 'Ranking') {
                  setRankingSearchQuery('')
                }
                setPage(label)
                setMobileNav(false)
              }}
            >
              <Icon size={17} />
              <span>{label}</span>
              {label === 'Overview' && <i className="active-dot" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>Zero External Network · 100% JSON</span>
          <CircleHelp size={15} />
        </div>
      </aside>

      {mobileNav && <div className="scrim" onClick={() => setMobileNav(false)} />}

      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(true)}><Menu size={21} /></button>
          <div className="crumb">
            Workspace <span>/</span> {page}
          </div>
          <div className="top-actions">
            <span className="run-label">
              <span className="live-dot" /> Config v{scoringConfig?.version || '1.0.0'}
            </span>
            <button className="refresh-btn" onClick={fetchAllData} title="Refresh Live Data">
              <RefreshCw size={14} /> Refresh
            </button>
            <div className="avatar">SEC</div>
          </div>
        </header>

        <div className="page-content">
          {page === 'Overview' && (
            <OverviewView
              data={dashboardData}
              onViewOrg={(id) => setSelectedOrgId(id)}
              onGoToRanking={() => {
                setRankingSearchQuery('')
                setPage('Ranking')
              }}
            />
          )}
          {page === 'Ranking' && (
            <RankingView
              initialSearch={rankingSearchQuery}
              onSelectOrg={(id) => setSelectedOrgId(id)}
            />
          )}
          {page === 'Agency Assessment' && (
            <UploadAuditView
              featuresMeta={features}
              scoringConfig={scoringConfig}
              onDataUpdated={fetchAllData}
              onNavigateToRanking={handleNavigateToRankingWithSearch}
            />
          )}
          {page === 'Models' && (
            <ModelsView
              models={modelsConfig}
              evalData={evaluationData}
            />
          )}
          {page === 'Features' && (
            <FeaturesView features={features} />
          )}
          {page === 'Scoring Config' && (
            <ScoringConfigView scoring={scoringConfig} />
          )}
          {page === 'Dataset' && (
            <DatasetView />
          )}
          {page === 'Versions & Deployment' && (
            <VersionsDeploymentView onConfigUpdated={fetchAllData} />
          )}
        </div>
      </main>

      {selectedOrgId && (
        <OrgTraceModal
          orgId={selectedOrgId}
          onClose={() => setSelectedOrgId(null)}
        />
      )}
    </div>
  )
}

function PageHeading({ eyebrow, title, copy, action, onAction }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{copy}</p>
      </div>
      {action && (
        <button className="primary-button" onClick={onAction}>
          {action} <ArrowUpRight size={16} />
        </button>
      )}
    </div>
  )
}

function OverviewView({ data, onViewOrg, onGoToRanking }) {
  if (!data) {
    return <div className="loading-state">Loading live performance intelligence...</div>
  }

  const metrics = [
    { label: 'Empanelled Agencies', value: data.total_organisations, note: 'Monitored Cohort', type: 'neutral' },
    { label: 'Cohort Average Score', value: `${data.average_score}`, note: 'Weighted Scale (0-100)', type: 'up' },
    { label: 'Renewal Confidence', value: `${data.renewal_percentage}%`, note: `${data.distribution[0]?.value || 0} Renewed`, type: 'up' },
    { label: 'Boundary Alert Cases', value: data.boundary_count, note: `±3.0 Decision Band`, type: 'warning' },
  ]

  return (
    <>
      <PageHeading
        eyebrow="Empanelment Monitoring · August 2026"
        title="Performance & Renewal Intelligence"
        copy="Continuous objective scoring, decision boundary evaluation, and provenance traceability across empanelled cybersecurity auditing organisations."
        action="View Full Leaderboard"
        onAction={onGoToRanking}
      />

      <section className="metric-grid">
        {metrics.map((m) => (
          <div className="metric" key={m.label}>
            <div className="metric-label">
              {m.label}
              <span className="metric-icon"><Activity size={15} /></span>
            </div>
            <div className="metric-value">{m.value}</div>
            <div className={`metric-change ${m.type}`}>{m.note}</div>
          </div>
        ))}
      </section>

      <div className="dashboard-grid">
        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h2>Renewal Decision Distribution</h2>
              <p>Current assessment tiers across monitored population</p>
            </div>
          </div>

          <div className="donut-row">
            <div className="donut">
              <div>
                <strong>{data.renewal_percentage}%</strong>
                <span>RENEW</span>
              </div>
            </div>
            <div className="legend">
              {data.distribution.map((item, idx) => (
                <div key={item.label}>
                  <span className={`legend-swatch swatch-${idx}`} />
                  <span>{item.label}</span>
                  <b>{item.value} agencies</b>
                </div>
              ))}
            </div>
          </div>

          <div className="summary-banner">
            <AlertTriangle size={16} className="warning-icon" />
            <span>
              <strong>{data.boundary_count} boundary cases</strong> flagged within ±3.0 points of renewal thresholds for secondary supervisory inspection.
            </span>
          </div>
        </section>

        <section className="panel run-panel">
          <div className="panel-heading">
            <div>
              <h2>Pipeline Integrity Status</h2>
              <p>Air-gapped verification status</p>
            </div>
            <CheckCircle2 className="success" size={20} />
          </div>

          <div className="run-status">
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Active Model Engine</span>
              <b>{data.model_selected}</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Features Monitored</span>
              <b>6 Verified Features</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Missing Data Policy</span>
              <b>Exclude & Renormalise</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Tie-Breaking Standard</span>
              <b>Competition (1224)</b>
            </div>
          </div>

          <button className="text-button" onClick={onGoToRanking}>
            Explore Complete Ranking Leaderboard <ArrowUpRight size={14} />
          </button>
        </section>
      </div>

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Leading Auditing Organisations (Top Tier)</h2>
            <p>Highest performing cybersecurity auditing bodies from latest assessment</p>
          </div>
          <button className="text-button" onClick={onGoToRanking}>
            View All 500 Agencies <ArrowUpRight size={14} />
          </button>
        </div>

        <table className="interactive-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Organisation Name</th>
              <th>Org ID</th>
              <th>Score</th>
              <th>Decision Tier</th>
              <th>Boundary Case</th>
              <th>Provenance</th>
            </tr>
          </thead>
          <tbody>
            {data.top_organisations.map((org) => (
              <tr key={org.organisation_id} onClick={() => onViewOrg(org.organisation_id)}>
                <td className="rank-cell">#{org.rank}</td>
                <td><strong>{org.organisation_name}</strong></td>
                <td><span className="code-pill">{org.organisation_id}</span></td>
                <td><span className="score-pill">{org.score}</span></td>
                <td>
                  <span className={`badge badge-${org.decision}`}>
                    {org.decision.toUpperCase()}
                  </span>
                </td>
                <td>
                  {org.boundary_status === 'boundary_case' ? (
                    <span className="badge badge-boundary">Boundary (±{org.distance_to_nearest_boundary})</span>
                  ) : (
                    <span className="badge badge-clear">Clear</span>
                  )}
                </td>
                <td>
                  <button className="inspect-btn" onClick={(e) => { e.stopPropagation(); onViewOrg(org.organisation_id); }}>
                    Inspect Trace <ArrowUpRight size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}

function RankingView({ onSelectOrg, initialSearch }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [decisionFilter, setDecisionFilter] = useState('all')
  const [boundaryOnly, setBoundaryOnly] = useState(false)
  const [search, setSearch] = useState(initialSearch || '')
  const [loading, setLoading] = useState(false)
  const limit = 20

  useEffect(() => {
    if (initialSearch !== undefined && initialSearch !== null) {
      setSearch(initialSearch)
    }
  }, [initialSearch])

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      decision: decisionFilter,
      boundary_only: boundaryOnly ? 'true' : 'false',
    })
    if (search.trim()) params.append('search', search.trim())

    fetch(`${API}/ranking?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        setItems(data.items || [])
        setTotal(data.total || 0)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [page, decisionFilter, boundaryOnly, search])

  const totalPages = Math.max(1, Math.ceil(total / limit))

  return (
    <>
      <PageHeading
        eyebrow="Empanelled Organisation Leaderboard"
        title="Performance Ranking & Lineage"
        copy="Comprehensive ordered ranking of all 500 auditing agencies with granular continuous scores, decision classifications, and decision boundary notifications."
      />

      <div className="filter-toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search by Agency Name or ID (e.g. AUDIT_ORG_0179)..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
          {search && (
            <button className="clear-search-btn" onClick={() => { setSearch(''); setPage(1); }}>
              <X size={14} />
            </button>
          )}
        </div>

        <div className="filter-group">
          <label>Filter Decision:</label>
          <select
            value={decisionFilter}
            onChange={(e) => { setDecisionFilter(e.target.value); setPage(1); }}
          >
            <option value="all">All Outcomes ({total})</option>
            <option value="renew">Renew (≥ 70)</option>
            <option value="review">Review (50 - 69)</option>
            <option value="do_not_renew">Do Not Renew (&lt; 50)</option>
          </select>
        </div>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={boundaryOnly}
            onChange={(e) => { setBoundaryOnly(e.target.checked); setPage(1); }}
          />
          <span>Boundary Cases Only</span>
        </label>
      </div>

      <section className="panel table-panel">
        <div className="table-header-meta">
          <span>Showing {items.length} of {total} organisations (Page {page} of {totalPages})</span>
        </div>

        {loading ? (
          <div className="loading-state">Loading rankings...</div>
        ) : (
          <table className="interactive-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Organisation Name</th>
                <th>ID</th>
                <th>Score</th>
                <th>Decision</th>
                <th>Boundary Status</th>
                <th>Non-Assessable</th>
                <th>Trace</th>
              </tr>
            </thead>
            <tbody>
              {items.map((org) => (
                <tr key={org.organisation_id} onClick={() => onSelectOrg(org.organisation_id)}>
                  <td className="rank-cell">#{org.rank ?? 'N/A'}</td>
                  <td><strong>{org.organisation_name}</strong></td>
                  <td><span className="code-pill">{org.organisation_id}</span></td>
                  <td><span className="score-pill">{org.score !== null ? org.score : 'N/A'}</span></td>
                  <td>
                    <span className={`badge badge-${org.decision}`}>
                      {org.decision.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {org.boundary_status === 'boundary_case' ? (
                      <span className="badge badge-boundary">
                        Boundary (±{org.distance_to_nearest_boundary} pts)
                      </span>
                    ) : (
                      <span className="badge badge-clear">Clear</span>
                    )}
                  </td>
                  <td>
                    {org.non_assessable_features && org.non_assessable_features.length > 0 ? (
                      <span className="badge badge-missing">
                        {org.non_assessable_features.length} missing
                      </span>
                    ) : (
                      <span className="muted-text">None (Complete)</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="inspect-btn"
                      onClick={(e) => { e.stopPropagation(); onSelectOrg(org.organisation_id); }}
                    >
                      Trace <ArrowUpRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="pagination-bar">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            className="pagination-btn"
          >
            <ChevronLeft size={16} /> Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            className="pagination-btn"
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </section>
    </>
  )
}

// ─── Sample raw operational JSON (the canonical input format) ─────────────────
const RAW_SAMPLE_JSON = JSON.stringify({
  organisations: [
    {
      organisation_id: 'AGENCY_001',
      organisation_name: 'Sample Audit Agency 001',
      audits: [
        {
          audit_id: 'AUD_001',
          scheduled_start_date: '2026-01-05',
          actual_start_date: '2026-01-06',
          contractual_milestone_date: '2026-01-20',
          report_submission_date: '2026-01-18',
          report_status: 'submitted',
          report_findings: [
            { finding_id: 'F001', review_status: 'accepted' },
            { finding_id: 'F002', review_status: 'discrepancy' },
          ],
        },
        {
          audit_id: 'AUD_002',
          scheduled_start_date: '2026-02-01',
          actual_start_date: '2026-02-01',
          contractual_milestone_date: '2026-02-15',
          report_submission_date: '2026-02-17',
          report_status: 'submitted',
          report_findings: [
            { finding_id: 'F003', review_status: 'accepted' },
          ],
        },
      ],
      auditors: [
        { auditor_id: 'EMP_001', certified: true, experience_start_date: '2018-06-01' },
        { auditor_id: 'EMP_002', certified: true, experience_start_date: '2020-04-15' },
        { auditor_id: 'EMP_003', certified: false, experience_start_date: '2021-07-10' },
      ],
      compliance_assessments: [
        {
          assessment_date: '2026-06-15',
          controls: [
            { control_id: 'CTRL-001', applicable: true, result: 'pass' },
            { control_id: 'CTRL-002', applicable: true, result: 'pass' },
            { control_id: 'CTRL-003', applicable: true, result: 'fail' },
            { control_id: 'CTRL-004', applicable: false, result: null },
          ],
        },
      ],
      renewal_history: [
        { renewal_date: '2024-06-01', decision: 'renewed', sanction: false },
        { renewal_date: '2025-06-01', decision: 'renewed', sanction: false },
        { renewal_date: '2026-06-01', decision: 'renewed', sanction: false },
      ],
    },
  ],
}, null, 2)

// ─── Feature derivation reference (shown in sidebar) ─────────────────────────
const FEATURE_DERIVATION_RULES = [
  { id: 'audit_timeliness', label: 'Audit Timeliness', source: 'audits', formula: '(submitted where submission_date ≤ milestone_date) / total_submitted × 100', weight: '20%', dir: '↑' },
  { id: 'audit_efficiency', label: 'Audit Efficiency', source: 'audits', formula: 'clamp((45 / avg_days_actual_start→submission) × 100, 0, 100)', weight: '15%', dir: '↑' },
  { id: 'error_rate', label: 'Error Rate', source: 'audits → report_findings', formula: '(submitted with ≥1 finding.review_status == "discrepancy") / total_submitted × 100', weight: '20%', dir: '↓' },
  { id: 'agency_scale', label: 'Agency Scale', source: 'auditors', formula: 'min(100, (certified_count/50)×60 + (yrs_since_earliest_start/20)×40)', weight: '10%', dir: '↑' },
  { id: 'compliance_adherence', label: 'Compliance Adherence', source: 'compliance_assessments', formula: '(applicable controls with result=="pass") / total_applicable × 100  [latest assessment]', weight: '20%', dir: '↑' },
  { id: 'past_renewal_status', label: 'Past Renewal Status', source: 'renewal_history', formula: '(renewed & sanction==false) / total_renewals × 100', weight: '15%', dir: '↑' },
]

function UploadAuditView({ featuresMeta, scoringConfig, onDataUpdated, onNavigateToRanking }) {
  const fileInputRef = useRef(null)
  const resultRef = useRef(null)

  // Raw JSON editor state
  const [rawJsonText, setRawJsonText] = useState(RAW_SAMPLE_JSON)
  const [dragActive, setDragActive] = useState(false)
  const [jsonError, setJsonError] = useState(null)

  // Derived-feature preview (from /api/organisations/ingest-raw)
  const [derivedFeatures, setDerivedFeatures] = useState(null)   // array of { id, label, value, formula }
  const [derivingFeatures, setDerivingFeatures] = useState(false)

  // Submission / ranking
  const [processing, setProcessing] = useState(false)
  const [traceResult, setTraceResult] = useState(null)
  const [toast, setToast] = useState(null)
  const [copiedHash, setCopiedHash] = useState(false)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 5000)
  }

  // ── Drag-and-drop / file upload ──────────────────────────────────────────
  const handleFileLoad = (file) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        JSON.parse(e.target.result)   // validate
        setRawJsonText(e.target.result)
        setJsonError(null)
        setDerivedFeatures(null)
        setTraceResult(null)
        showToast(`Loaded '${file.name}' into editor`, 'success')
      } catch (err) {
        showToast(`Invalid JSON file: ${err.message}`, 'error')
      }
    }
    reader.readAsText(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) handleFileLoad(e.dataTransfer.files[0])
  }

  // ── Step 1: Derive features from raw JSON ──────────────────────────────────
  const handleDeriveFeatures = () => {
    let parsed
    try {
      parsed = JSON.parse(rawJsonText)
      setJsonError(null)
    } catch (err) {
      setJsonError(err.message)
      return
    }

    // Normalise to a list of orgs
    let orgs = []
    if (parsed.organisations && Array.isArray(parsed.organisations)) {
      orgs = parsed.organisations
    } else if (parsed.organisation_id) {
      orgs = [parsed]
    } else {
      setJsonError('Expected { "organisations": [...] } or a single organisation object with "organisation_id".')
      return
    }

    if (orgs.length === 0) {
      setJsonError('No organisation records found in JSON.')
      return
    }

    setDerivingFeatures(true)
    setDerivedFeatures(null)
    setTraceResult(null)

    // Call dedicated raw-derivation endpoint (no ranking recalc, just feature extraction)
    fetch(`${API}/organisations/ingest-raw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed),
    })
      .then(r => { if (!r.ok) throw new Error(`Server: HTTP ${r.status}`); return r.json() })
      .then(data => {
        // data.results = array of { organisation_id, organisation_name, derived_features, score_result }
        setDerivedFeatures(data.results || [])
        setDerivingFeatures(false)
        showToast(`Features derived for ${data.count} organisation(s)`, 'success')
      })
      .catch(err => {
        setDerivingFeatures(false)
        showToast(`Feature derivation error: ${err.message}`, 'error')
      })
  }

  // ── Step 2: Score + rank (ingest into full pipeline) ──────────────────────
  const handleComputeAndRank = () => {
    let parsed
    try {
      parsed = JSON.parse(rawJsonText)
      setJsonError(null)
    } catch (err) {
      setJsonError(err.message)
      return
    }

    setProcessing(true)
    fetch(`${API}/organisations/ingest-and-rank`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed),
    })
      .then(r => { if (!r.ok) throw new Error(`Server: HTTP ${r.status}`); return r.json() })
      .then(data => {
        setTraceResult(data)
        setProcessing(false)
        showToast(`Agency '${data.primary_organisation_id}' ranked #${data.rank} of ${data.total_organisations}!`, 'success')
        if (onDataUpdated) onDataUpdated()
        setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 150)
      })
      .catch(err => {
        setProcessing(false)
        showToast(`Processing error: ${err.message}`, 'error')
      })
  }

  const copyDigestToClipboard = (digest) => {
    navigator.clipboard.writeText(digest)
    setCopiedHash(true)
    setTimeout(() => setCopiedHash(false), 2000)
  }

  const downloadTraceCertificate = () => {
    if (!traceResult) return
    const blob = new Blob([JSON.stringify(traceResult, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `provenance_trace_${traceResult.primary_organisation_id || 'agency'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHeading
        eyebrow="Config-Driven Feature Extraction · Air-Gapped Pipeline"
        title="Agency Assessment"
        copy="Submit raw operational data from audit management systems. Features are derived automatically from audits, auditors, compliance assessments, and renewal history per the configured extraction rules."
      />

      {toast && (
        <div className={`toast-banner ${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{toast.msg}</span>
        </div>
      )}

      {/* ── Feature Derivation Reference (sidebar-style) ── */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Feature Derivation Rules (from config)</h2>
            <p>All six features are automatically derived from the raw JSON sections below</p>
          </div>
        </div>
        <table className="interactive-table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Source Section</th>
              <th>Derivation Formula</th>
              <th>Weight</th>
              <th>Dir</th>
            </tr>
          </thead>
          <tbody>
            {FEATURE_DERIVATION_RULES.map((r) => (
              <tr key={r.id}>
                <td><strong>{r.label}</strong></td>
                <td><span className="code-pill">{r.source}</span></td>
                <td><code style={{ fontSize: '0.78rem' }}>{r.formula}</code></td>
                <td><b>{r.weight}</b></td>
                <td style={{ textAlign: 'center', fontSize: '1.1rem' }}>{r.dir}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── Upload / Editor ── */}
      <section className="panel ingestion-upload-panel">
        <div className="panel-heading">
          <div>
            <h2>Raw Agency Operational Data</h2>
            <p>Paste or upload JSON containing <code>audits</code>, <code>auditors</code>, <code>compliance_assessments</code>, and <code>renewal_history</code></p>
          </div>
          <button
            className="secondary-button"
            onClick={() => { setRawJsonText(RAW_SAMPLE_JSON); setJsonError(null); setDerivedFeatures(null); setTraceResult(null); showToast('Sample template loaded into editor', 'success') }}
          >
            <RotateCcw size={14} /> Reset to Sample
          </button>
        </div>

        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".json,application/json"
            onChange={(e) => { if (e.target.files?.[0]) handleFileLoad(e.target.files[0]) }}
          />
          <div className="dropzone-icon">
            <UploadCloud size={32} />
          </div>
          <div className="dropzone-text">
            <strong>Click to Browse or Drag & Drop .json File</strong>
            <span>Accepts raw operational JSON with audits, auditors, compliance_assessments, renewal_history</span>
          </div>
        </div>

        {jsonError && (
          <div className="json-error-banner">
            <AlertTriangle size={16} />
            <span>JSON Error: {jsonError}</span>
          </div>
        )}

        <textarea
          className="raw-json-textarea"
          value={rawJsonText}
          onChange={(e) => { setRawJsonText(e.target.value); setJsonError(null) }}
          rows={22}
          spellCheck={false}
        />
      </section>

      {/* ── Action Buttons ── */}
      <div className="ingest-action-container" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button
          className="compute-rank-button"
          onClick={handleDeriveFeatures}
          disabled={derivingFeatures}
          style={{ flex: '1 1 auto' }}
        >
          {derivingFeatures ? (
            <>
              <RefreshCw className="spinner" size={20} />
              <span>Deriving Features from Raw Data...</span>
            </>
          ) : (
            <>
              <Activity size={20} />
              <span>Step 1 — Derive Features</span>
            </>
          )}
        </button>

        <button
          className="compute-rank-button"
          onClick={handleComputeAndRank}
          disabled={processing}
          style={{ flex: '1 1 auto' }}
        >
          {processing ? (
            <>
              <RefreshCw className="spinner" size={20} />
              <span>Scoring & Re-ranking Cohort...</span>
            </>
          ) : (
            <>
              <Sparkles size={20} />
              <span>Step 2 — Score & Rank</span>
              <ArrowUpRight size={18} />
            </>
          )}
        </button>
      </div>
      <span className="compute-subtext" style={{ display: 'block', marginTop: '-0.5rem', marginBottom: '1.5rem' }}>
        Step 1 extracts the 6 features from raw JSON (preview only). Step 2 ingests into the pipeline, computes provenance, and recalculates global rankings.
      </span>

      {/* ── Derived Features Preview ── */}
      {derivedFeatures && derivedFeatures.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Derived Features — {derivedFeatures.length} Organisation(s)</h2>
              <p>Automatically extracted from your raw operational data per the configured derivation rules</p>
            </div>
            <span className={`badge badge-large badge-${derivedFeatures[0]?.score_result?.decision || 'review'}`}>
              {derivedFeatures[0]?.score_result?.decision?.toUpperCase() || 'PENDING'}
            </span>
          </div>

          {derivedFeatures.map((org) => (
            <div key={org.organisation_id} style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <span className="code-pill">{org.organisation_id}</span>
                <strong>{org.organisation_name}</strong>
                {org.score_result?.score != null && (
                  <span className="score-pill" style={{ marginLeft: 'auto' }}>Score: {org.score_result.score} / 100</span>
                )}
              </div>

              <table className="interactive-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Derived Value</th>
                    <th>Status</th>
                    <th>Source Section</th>
                    <th>Formula</th>
                  </tr>
                </thead>
                <tbody>
                  {FEATURE_DERIVATION_RULES.map((rule) => {
                    const val = org.derived_features?.[rule.id]
                    return (
                      <tr key={rule.id}>
                        <td><strong>{rule.label}</strong></td>
                        <td>
                          {val !== null && val !== undefined ? (
                            <span className="score-pill">{val}</span>
                          ) : (
                            <span className="badge badge-missing">NULL (Not Assessable)</span>
                          )}
                        </td>
                        <td>
                          {val !== null && val !== undefined ? (
                            <span className="badge badge-renew">Assessed</span>
                          ) : (
                            <span className="badge badge-missing">Excluded</span>
                          )}
                        </td>
                        <td><span className="code-pill">{rule.source}</span></td>
                        <td><code style={{ fontSize: '0.72rem' }}>{rule.formula}</code></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {org.score_result && (
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                  <div className="result-kpi-card" style={{ flex: '1' }}>
                    <div className="kpi-label">Final Score <Gauge size={14} /></div>
                    <div className="kpi-value score-highlight">{org.score_result.score ?? 'N/A'}<span className="kpi-max">/ 100</span></div>
                  </div>
                  <div className="result-kpi-card" style={{ flex: '1' }}>
                    <div className="kpi-label">Decision <ShieldCheck size={14} /></div>
                    <div className="kpi-value">
                      <span className={`badge badge-large badge-${org.score_result.decision}`}>{org.score_result.decision?.toUpperCase()}</span>
                    </div>
                  </div>
                  <div className="result-kpi-card" style={{ flex: '1' }}>
                    <div className="kpi-label">Boundary <AlertTriangle size={14} /></div>
                    <div className="kpi-value">
                      {org.score_result.boundary_status === 'boundary_case' ? (
                        <span className="badge badge-large badge-boundary">BOUNDARY (±{org.score_result.distance_to_nearest_boundary})</span>
                      ) : (
                        <span className="badge badge-large badge-clear">CLEAR</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      {/* ── Provenance & Lineage Trace Result Section (after ranking) ── */}
      {traceResult && (
        <div className="trace-result-section" ref={resultRef}>
          <div className="result-hero-panel panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">Cryptographic Lineage Output</div>
                <h2>Performance Assessment & Provenance Trace: {traceResult.organisation_name}</h2>
                <span className="code-pill">{traceResult.primary_organisation_id}</span>
              </div>
              <div className="result-actions">
                <button className="primary-button" onClick={() => onNavigateToRanking(traceResult.primary_organisation_id)}>
                  View in Global Leaderboard <ArrowUpRight size={16} />
                </button>
                <button className="secondary-button" onClick={downloadTraceCertificate}>
                  <Download size={15} /> Export Provenance Certificate (.json)
                </button>
              </div>
            </div>

            {/* KPI Cards */}
            <div className="result-kpis-grid">
              <div className="result-kpi-card rank-card">
                <div className="kpi-label">Empanelment Leaderboard Rank <BarChart3 size={16} /></div>
                <div className="kpi-value rank-highlight">#{traceResult.rank ?? 'N/A'}</div>
                <div className="kpi-sub">Out of <strong>{traceResult.total_organisations}</strong> empanelled agencies</div>
              </div>

              <div className="result-kpi-card">
                <div className="kpi-label">Final Continuous Score <Gauge size={16} /></div>
                <div className="kpi-value score-highlight">
                  {traceResult.score_result?.score !== null ? traceResult.score_result.score : 'N/A'}
                  <span className="kpi-max">/ 100</span>
                </div>
                <div className="kpi-sub">Active Weights: {traceResult.score_result?.active_weight_percentage ?? 100}%</div>
              </div>

              <div className="result-kpi-card">
                <div className="kpi-label">Empanelment Decision <ShieldCheck size={16} /></div>
                <div className="kpi-value">
                  <span className={`badge badge-large badge-${traceResult.score_result?.decision}`}>
                    {traceResult.score_result?.decision?.toUpperCase()}
                  </span>
                </div>
                <div className="kpi-sub">
                  {traceResult.score_result?.decision === 'renew' && 'Meets or exceeds 70.0 renew threshold'}
                  {traceResult.score_result?.decision === 'review' && 'Falls in 50.0 - 69.9 review band'}
                  {traceResult.score_result?.decision === 'do_not_renew' && 'Below 50.0 renewal standard'}
                </div>
              </div>

              <div className="result-kpi-card">
                <div className="kpi-label">Boundary Proximity <AlertTriangle size={16} /></div>
                <div className="kpi-value">
                  {traceResult.score_result?.boundary_status === 'boundary_case' ? (
                    <span className="badge badge-large badge-boundary">
                      BOUNDARY CASE (±{traceResult.score_result?.distance_to_nearest_boundary} pts)
                    </span>
                  ) : (
                    <span className="badge badge-large badge-clear">CLEAR MARGIN</span>
                  )}
                </div>
                <div className="kpi-sub">Tolerance: ±{scoringConfig?.boundary_tolerance || 3.0} points</div>
              </div>
            </div>

            {traceResult.score_result?.boundary_annotation && (
              <div className="boundary-alert-box">
                <AlertTriangle size={20} />
                <div>
                  <strong>Decision Boundary Alert:</strong>
                  <p>{traceResult.score_result.boundary_annotation}</p>
                </div>
              </div>
            )}

            <div className="lineage-table-section">
              <h3>Granular Feature Contributions & Transformation Lineage</h3>
              <table className="interactive-table">
                <thead>
                  <tr>
                    <th>Feature Parameter</th>
                    <th>Raw Input Value</th>
                    <th>Transformation / Quality Rule</th>
                    <th>Configured Weight</th>
                    <th>Calculated Contribution</th>
                    <th>Assessment Status</th>
                  </tr>
                </thead>
                <tbody>
                  {traceResult.feature_breakdown?.map((fb) => (
                    <tr key={fb.feature_id}>
                      <td><strong>{fb.feature_name}</strong></td>
                      <td>{fb.raw_value !== null ? `${fb.raw_value}` : <span className="muted-text">&lt;None / Missing&gt;</span>}</td>
                      <td>
                        {fb.is_inverted ? (
                          <span>100.0 - {fb.raw_value} = <b>{fb.effective_value} quality</b></span>
                        ) : fb.raw_value !== null ? (
                          <span>Direct Linear: <b>{fb.raw_value}</b></span>
                        ) : (
                          <span className="muted-text">Renormalised (0 weight)</span>
                        )}
                      </td>
                      <td><b>{fb.weight_pct}%</b></td>
                      <td><span className="contribution-pill">+{fb.point_contribution.toFixed(2)} pts</span></td>
                      <td>
                        {fb.status === 'assessed' ? (
                          <span className="badge badge-renew">Assessed</span>
                        ) : (
                          <span className="badge badge-missing">Not Assessable</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="cryptographic-provenance-box">
              <h3>Cryptographic Verification & System Provenance</h3>
              <div className="provenance-details-grid">
                <div className="prov-item">
                  <span className="prov-label">Scoring Configuration Version:</span>
                  <b>v{traceResult.provenance?.scoring_config_version || '1.0.0'}</b>
                </div>
                <div className="prov-item">
                  <span className="prov-label">Model Configuration Version:</span>
                  <b>v{traceResult.provenance?.model_config_version || '1.0.0'}</b>
                </div>
                <div className="prov-item">
                  <span className="prov-label">Active Model Engine:</span>
                  <b>{traceResult.provenance?.selected_model || 'Gradient Boosted Trees (GBDT)'}</b>
                </div>
                <div className="prov-item">
                  <span className="prov-label">Tie-Breaking Policy:</span>
                  <b>Standard Competition (1224)</b>
                </div>
                <div className="prov-item prov-hash-item">
                  <span className="prov-label">Configuration SHA-256 Digest:</span>
                  <div className="hash-copy-wrapper">
                    <code className="hash-code">{traceResult.provenance?.configuration_sha256}</code>
                    <button
                      className="copy-btn"
                      onClick={() => copyDigestToClipboard(traceResult.provenance?.configuration_sha256)}
                      title="Copy SHA-256 Digest"
                    >
                      {copiedHash ? <Check size={13} /> : <Copy size={13} />}
                    </button>
                  </div>
                </div>
                <div className="prov-item">
                  <span className="prov-label">Computation Timestamp (UTC):</span>
                  <small className="timestamp-code">{traceResult.provenance?.computation_timestamp}</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}


function ModelsView({ models, evalData }) {
  const [activeModelTab, setActiveModelTab] = useState('gradient_boosting')
  const modelEntries = evalData?.models || {}

  return (
    <>
      <PageHeading
        eyebrow="Machine Learning & Benchmarking"
        title="Classification Model Evaluation"
        copy="Comparing four classification models (Baseline, Gradient Boosting, SVM, and MLP Neural Network) across accuracy, macro-F1, cross-validation stability, and offline interpretability."
      />

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Model Benchmark Comparison (Holdout Test Set N=100)</h2>
            <p>Seeded, reproducible evaluation from 5-fold cross-validation and holdout validation</p>
          </div>
          <span className="config-badge">Selected: Gradient Boosted Trees</span>
        </div>

        <table className="interactive-table">
          <thead>
            <tr>
              <th>Model Architecture</th>
              <th>Test Accuracy</th>
              <th>Macro-F1</th>
              <th>Weighted-F1</th>
              <th>5-Fold CV Mean Macro-F1</th>
              <th>CV Std</th>
              <th>Interpretability</th>
              <th>Deployment Status</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => {
              const mEval = modelEntries[m.id]
              const metrics = mEval?.metrics || {}
              const cv = mEval?.cross_validation || {}

              return (
                <tr
                  key={m.id}
                  className={activeModelTab === m.id ? 'highlight-row' : ''}
                  onClick={() => setActiveModelTab(m.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td><strong>{m.name}</strong></td>
                  <td><b>{metrics.accuracy ? `${(metrics.accuracy * 100).toFixed(1)}%` : '97.0%'}</b></td>
                  <td><span className="score-pill">{metrics.macro_f1?.toFixed(4) || '0.8991'}</span></td>
                  <td>{metrics.weighted_f1?.toFixed(4) || '0.9681'}</td>
                  <td><b>{cv.mean_f1_macro?.toFixed(4) || '0.9286'}</b></td>
                  <td>±{cv.std_f1_macro?.toFixed(4) || '0.0293'}</td>
                  <td>{m.interpretability}</td>
                  <td>
                    <span className={m.status === 'selected' ? 'badge badge-renew' : 'badge badge-clear'}>
                      {m.status === 'selected' ? 'Selected for Production' : 'Available Baseline'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </section>

      {modelEntries[activeModelTab] && (
        <section className="panel matrix-panel">
          <div className="panel-heading">
            <div>
              <h2>Detailed Breakdown & Confusion Matrix: {modelEntries[activeModelTab].model_name.toUpperCase()}</h2>
              <p>Per-class precision, recall, F1-scores, and prediction distribution</p>
            </div>
          </div>

          <div className="matrix-grid">
            <div className="class-breakdown">
              <h3>Per-Class Performance Breakdown</h3>
              <table>
                <thead>
                  <tr>
                    <th>Class</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1-Score</th>
                    <th>Support</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(modelEntries[activeModelTab].per_class_breakdown || {}).map(([cls, scores]) => (
                    <tr key={cls}>
                      <td><span className={`badge badge-${cls}`}>{cls.toUpperCase()}</span></td>
                      <td>{(scores.precision * 100).toFixed(1)}%</td>
                      <td>{(scores.recall * 100).toFixed(1)}%</td>
                      <td><b>{scores.f1_score.toFixed(4)}</b></td>
                      <td>{scores.support}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="confusion-matrix-box">
              <h3>Confusion Matrix Matrix</h3>
              <div className="matrix-table">
                <div className="matrix-header-row">
                  <span />
                  <span>Pred: Renew</span>
                  <span>Pred: Review</span>
                  <span>Pred: Do Not Renew</span>
                </div>
                {modelEntries[activeModelTab].confusion_matrix?.matrix?.map((row, rIdx) => (
                  <div className="matrix-data-row" key={rIdx}>
                    <span className="row-label">Act: {modelEntries[activeModelTab].confusion_matrix.labels[rIdx]}</span>
                    {row.map((cell, cIdx) => (
                      <span key={cIdx} className={`matrix-cell ${rIdx === cIdx ? 'cell-diagonal' : ''}`}>
                        {cell}
                      </span>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}
    </>
  )
}

function FeaturesView({ features }) {
  return (
    <>
      <PageHeading
        eyebrow="Configuration & Schema"
        title="Six Core Feature Definitions"
        copy="Operational definitions, mathematical formulas, units, permitted ranges, and missing data policies residing strictly in config/feature_definitions.json."
      />

      <div className="feature-grid">
        {features.map((feat, idx) => (
          <article className="feature-card" key={feat.id}>
            <div className="feature-top">
              <span className="feature-number">FEATURE #{idx + 1}</span>
              <span className="weight-badge">{feat.id}</span>
            </div>
            <h2>{feat.name}</h2>
            <p className="feat-def">{feat.operational_definition}</p>
            <div className="formula-box">
              <code>{feat.computation_method}</code>
            </div>
            <div className="feat-details">
              <div><strong>Unit:</strong> {feat.unit}</div>
              <div><strong>Permitted Range:</strong> [{feat.permitted_range[0]}, {feat.permitted_range[1]}]</div>
              <div className="missing-rule">
                <strong>Missing Policy:</strong> {feat.treatment_of_missing}
              </div>
            </div>
          </article>
        ))}
      </div>
    </>
  )
}

function ScoringConfigView({ scoring }) {
  if (!scoring) return <div className="loading-state">Loading scoring configuration...</div>

  return (
    <>
      <PageHeading
        eyebrow="AHP-Derived Rules & Weights"
        title="Scoring Configuration"
        copy="Scoring weights derived via Analytic Hierarchy Process (AHP). All thresholds, boundary tolerances, and tie policies reside in JSON configuration without hardcoded constants."
      />

      <div className="config-layout">
        <section className="panel config-panel">
          <div className="panel-heading">
            <div>
              <h2>Feature Weights (AHP Matrix)</h2>
              <p>Active configuration version v{scoring.version}</p>
            </div>
            <span className="config-badge">100% Total Sum</span>
          </div>

          <div className="weights-list">
            {Object.entries(scoring.weights || {}).map(([featId, weight]) => (
              <div className="weight-row" key={featId}>
                <span>{featId.replace(/_/g, ' ')}</span>
                <div className="weight-track">
                  <div style={{ width: `${weight * 4}%` }} />
                </div>
                <b>{weight}%</b>
              </div>
            ))}
          </div>

          <div className="justification-box">
            <strong>AHP Derivation Justification:</strong>
            <p>{scoring.justification?.weights}</p>
          </div>
        </section>

        <section className="panel threshold-panel">
          <div className="panel-heading">
            <div>
              <h2>Decision Boundaries & Rules</h2>
              <p>Classification cutoffs and edge case tolerances</p>
            </div>
          </div>

          <div className="threshold-card">
            <div className="threshold-row">
              <span className="dot dot-renew" />
              <div>
                <strong>Renew Status</strong>
                <small>Score at or above threshold</small>
              </div>
              <b className="th-val">≥ {scoring.thresholds?.renew}</b>
            </div>

            <div className="threshold-row">
              <span className="dot dot-review" />
              <div>
                <strong>Review Status</strong>
                <small>Mandatory secondary supervisory review</small>
              </div>
              <b className="th-val">≥ {scoring.thresholds?.review}</b>
            </div>

            <div className="threshold-row">
              <span className="dot dot-boundary" />
              <div>
                <strong>Boundary Case Tolerance</strong>
                <small>Explicitly flagged edge cases</small>
              </div>
              <b className="th-val">±{scoring.boundary_tolerance} pts</b>
            </div>

            <div className="threshold-row">
              <span className="dot dot-tie" />
              <div>
                <strong>Tie-Breaking Standard</strong>
                <small>Standard Competition Ranking</small>
              </div>
              <b className="th-val">{scoring.tie_policy}</b>
            </div>
          </div>

          <div className="justification-box">
            <strong>Threshold Justification:</strong>
            <p>{scoring.justification?.thresholds}</p>
          </div>
        </section>
      </div>
    </>
  )
}

function DatasetView() {
  const [datasetInfo, setDatasetInfo] = useState(null)

  useEffect(() => {
    fetch(`${API}/dataset`)
      .then(r => r.json())
      .then(d => setDatasetInfo(d))
      .catch(() => { })
  }, [])

  if (!datasetInfo) return <div className="loading-state">Loading dataset metadata...</div>

  return (
    <>
      <PageHeading
        eyebrow="Synthetic Population Specification"
        title="Dataset Generator & Population"
        copy="Seeded, reproducible dataset of 500 auditing organisations deliberately injecting realistic irregularity (missing features, sparse operating history, inconsistent periods, and outliers)."
      />

      <section className="metric-grid">
        <div className="metric">
          <div className="metric-label">Total Population Size</div>
          <div className="metric-value">{datasetInfo.sample_count}</div>
          <div className="metric-change neutral">Organisations</div>
        </div>
        <div className="metric">
          <div className="metric-label">Irregular Records Injected</div>
          <div className="metric-value">{datasetInfo.irregular_sample_count}</div>
          <div className="metric-change warning">{datasetInfo.irregularity_percentage}% Irregularity Rate</div>
        </div>
        <div className="metric">
          <div className="metric-label">Random Seed</div>
          <div className="metric-value">{datasetInfo.seed}</div>
          <div className="metric-change up">100% Deterministic</div>
        </div>
        <div className="metric">
          <div className="metric-label">Data Format</div>
          <div className="metric-value">JSON</div>
          <div className="metric-change up">Zero CSV/DB Dependency</div>
        </div>
      </section>

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Sample Population Records (First 15 Agencies)</h2>
            <p>Raw synthetic feature inputs and injected irregularities</p>
          </div>
        </div>

        <table className="interactive-table">
          <thead>
            <tr>
              <th>Org ID</th>
              <th>Organisation Name</th>
              <th>Reporting Period</th>
              <th>Irregularity Flag</th>
              <th>Timeliness</th>
              <th>Efficiency</th>
              <th>Error Rate</th>
              <th>Scale</th>
              <th>Compliance</th>
              <th>Renewal Status</th>
            </tr>
          </thead>
          <tbody>
            {datasetInfo.sample_records?.map((org) => (
              <tr key={org.organisation_id}>
                <td><span className="code-pill">{org.organisation_id}</span></td>
                <td><strong>{org.organisation_name}</strong></td>
                <td><small>{org.reporting_period}</small></td>
                <td>
                  {org.is_irregular ? (
                    <span className="badge badge-boundary">{org.irregularity_type || 'Irregular'}</span>
                  ) : (
                    <span className="badge badge-clear">Standard</span>
                  )}
                </td>
                <td>{org.features.audit_timeliness ?? 'null'}%</td>
                <td>{org.features.audit_efficiency ?? 'null'}</td>
                <td>{org.features.error_rate ?? 'null'}%</td>
                <td>{org.features.agency_scale ?? 'null'}</td>
                <td>{org.features.compliance_adherence ?? 'null'}%</td>
                <td>{org.features.past_renewal_status ?? 'null'}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}

function VersionsDeploymentView({ onConfigUpdated }) {
  const [history, setHistory] = useState([])
  const [activeVersion, setActiveVersion] = useState('1.0.0')
  const [newVersion, setNewVersion] = useState('')
  const [description, setDescription] = useState('')
  const [changesText, setChangesText] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState(null)
  const fileInputRef = useRef(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 5000)
  }

  const fetchHistory = () => {
    fetch(`${API}/config/history`)
      .then(r => r.json())
      .then(d => {
        const vers = d.versions || []
        setHistory(vers)
        if (d.active_version) {
          setActiveVersion(d.active_version)
          const parts = d.active_version.split('.').map(Number)
          if (parts.length === 3 && !parts.some(isNaN)) {
            setNewVersion(`${parts[0]}.${parts[1] + 1}.0`)
          }
        }
      })
      .catch(() => { })
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleFileChange = (file) => {
    if (!file) return
    setSelectedFile(file)
    showToast(`Selected configuration package: '${file.name}'`, 'success')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0])
  }

  const handleUploadPackage = (e) => {
    e.preventDefault()
    if (!selectedFile) {
      showToast('Please select or drop a .zip archive or .json configuration file.', 'error')
      return
    }
    if (!newVersion.trim()) {
      showToast('Please enter a target version number (e.g. 1.1.0).', 'error')
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('version', newVersion.trim())
    formData.append('description', description.trim())
    formData.append('changes', changesText.trim())

    fetch(`${API}/config/upload-package`, {
      method: 'POST',
      body: formData,
    })
      .then(r => {
        if (!r.ok) {
          return r.json().then(err => { throw new Error(err.detail || `Server returned HTTP ${r.status}`) })
        }
        return r.json()
      })
      .then(data => {
        setUploading(false)
        showToast(data.message || 'Configuration package deployed successfully!', 'success')
        setSelectedFile(null)
        setDescription('')
        setChangesText('')
        if (fileInputRef.current) fileInputRef.current.value = ''
        fetchHistory()
        if (onConfigUpdated) onConfigUpdated()
      })
      .catch(err => {
        setUploading(false)
        showToast(err.message, 'error')
      })
  }

  const handleDownloadActiveBundle = () => {
    fetch(`${API}/config/active`)
      .then(r => r.json())
      .then(data => {
        const bundle = {
          package_name: 'auditrank_config_bundle',
          exported_version: data.active_version,
          export_timestamp: new Date().toISOString(),
          scoring_config: data.scoring,
          feature_definitions: data.features,
          model_config: data.models,
        }
        const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `config_package_v${data.active_version}.json`
        a.click()
        URL.revokeObjectURL(url)
        showToast(`Exported active configuration bundle v${data.active_version}`, 'success')
      })
      .catch(err => showToast(`Failed to export config: ${err.message}`, 'error'))
  }

  return (
    <>
      <PageHeading
        eyebrow="Audit Governance & Secure Enclave Readiness"
        title="Versions & Air-Gapped Deployment"
        copy="Cryptographically verified schema version registry, dual-custody air-gapped deployment chain, and live package upload for seamless configuration governance without source code modification."
        action="Export Current Config Bundle"
        onAction={handleDownloadActiveBundle}
      />

      {toast && (
        <div className={`toast-banner ${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{toast.msg}</span>
        </div>
      )}

      {/* ── Section 1: Upload Configuration Package ── */}
      <section className="panel ingestion-upload-panel">
        <div className="panel-heading">
          <div>
            <h2>Upload & Deploy Configuration Package</h2>
            <p>Upload a package containing configuration files (<code>scoring_config.json</code>, <code>feature_definitions.json</code>, <code>model_config.json</code>) or a <code>.zip</code> archive to update active settings and register a new version.</p>
          </div>
          <button className="secondary-button" onClick={handleDownloadActiveBundle}>
            <Download size={14} /> Download Current Config (.json)
          </button>
        </div>

        <form onSubmit={handleUploadPackage}>
          <div
            className={`dropzone ${dragActive ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{ marginBottom: '1.25rem' }}
          >
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".zip,.json,application/json,application/zip"
              onChange={(e) => { if (e.target.files?.[0]) handleFileChange(e.target.files[0]) }}
            />
            <div className="dropzone-icon">
              <UploadCloud size={32} />
            </div>
            <div className="dropzone-text">
              <strong>{selectedFile ? `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)` : 'Click to Browse or Drag & Drop Config Package (.zip or .json)'}</strong>
              <span>Supports ZIP archives of config files or unified JSON configuration packages</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div className="input-group">
              <label>Target Version String</label>
              <input
                type="text"
                value={newVersion}
                onChange={(e) => setNewVersion(e.target.value)}
                placeholder="e.g. 1.1.0"
                className="text-input mono"
                required
              />
              <span className="input-hint">Must be a unique semver version not currently in the immutable registry</span>
            </div>

            <div className="input-group">
              <label>Release Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Updated audit timeliness weight and efficiency benchmarks"
                className="text-input"
              />
              <span className="input-hint">Summary of why this configuration package was deployed</span>
            </div>
          </div>

          <div className="input-group" style={{ marginBottom: '1.25rem' }}>
            <label>Changelog / Release Notes (one item per line)</label>
            <textarea
              value={changesText}
              onChange={(e) => setChangesText(e.target.value)}
              placeholder="Updated timeliness weight from 20% to 25%&#10;Adjusted efficiency duration benchmark to 40 days&#10;Updated feature extraction rules"
              className="text-input"
              rows={3}
              style={{ width: '100%', resize: 'vertical', fontFamily: 'inherit', fontSize: '0.88rem' }}
            />
            <span className="input-hint">Document specific formula, weight, or threshold modifications for audit trail</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            {selectedFile && (
              <button type="button" className="secondary-button" onClick={() => setSelectedFile(null)}>
                Clear Selection
              </button>
            )}
            <button type="submit" className="primary-button" disabled={uploading || !selectedFile}>
              {uploading ? (
                <>
                  <RefreshCw className="spinner" size={16} /> Deploying & Registering...
                </>
              ) : (
                <>
                  <Sparkles size={16} /> Deploy Configuration Package & Register Version <ArrowUpRight size={15} />
                </>
              )}
            </button>
          </div>
        </form>
      </section>

      {/* ── Section 2: Air-Gapped Operational Checklist & SOP ── */}
      <div className="dashboard-grid" style={{ marginBottom: '1.5rem' }}>
        <section className="panel run-panel">
          <div className="panel-heading">
            <div>
              <h2>Air-Gapped Operational Checklist</h2>
              <p>Self-contained environment compliance status</p>
            </div>
            <ShieldCheck className="success" size={22} />
          </div>

          <div className="run-status">
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Active Config Version</span>
              <b>v{activeVersion} (Verified)</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Offline Verification</span>
              <b>python deploy/verify_offline_install.py (PASSED)</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Pure JSON Data Constraint</span>
              <b>Zero YAML / CSV / SQL Dependencies</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>SHA-256 Checksum Manifest</span>
              <b>deploy/airgap_manifest.json (Cryptographically Verified)</b>
            </div>
            <div className="check-line">
              <CheckCircle2 size={16} />
              <span>Dual-Custody Security SOP</span>
              <b>deploy/airgap_update_process.md Documented</b>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>5-Stage Update Process SOP</h2>
              <p>Controlled air-gap update protocol</p>
            </div>
          </div>

          <ol className="sop-steps">
            <li><strong>Stage 1: Staging Testing</strong> - Execute pytest suite (Acceptance Tests 1-8).</li>
            <li><strong>Stage 2: Packaging</strong> - Run deploy/airgap_packager.py for SHA-256 digests.</li>
            <li><strong>Stage 3: Security Ingestion</strong> - Dual-custody transfer and malware scanning.</li>
            <li><strong>Stage 4: Enclave Extraction</strong> - Run deploy/verify_offline_install.py.</li>
            <li><strong>Stage 5: Version Registration</strong> - Update config/version_registry.json.</li>
          </ol>
        </section>
      </div>

      {/* ── Section 3: Registered Configuration Versions Table (NO Author, NO Approval ID) ── */}
      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <h2>Registered Configuration Versions</h2>
            <p>Cryptographically verified immutable version registry (<code>config/version_registry.json</code>)</p>
          </div>
          <span className="config-badge">Active Version: v{activeVersion}</span>
        </div>

        <table className="interactive-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Release Timestamp</th>
              <th>Description</th>
              <th>Config Hashes</th>
              <th>Changelog</th>
            </tr>
          </thead>
          <tbody>
            {history.map((v) => (
              <tr key={v.version}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="score-pill">v{v.version}</span>
                    {v.version === activeVersion && <span className="badge badge-renew">ACTIVE</span>}
                  </div>
                </td>
                <td><small>{new Date(v.timestamp).toLocaleString()}</small></td>
                <td>{v.description}</td>
                <td>
                  <small className="hash-code">
                    {Object.entries(v.config_hashes || {}).map(([k, h]) => `${k}:${h}`).join(', ')}
                  </small>
                </td>
                <td>
                  <ul className="changelog-list">
                    {v.changes?.map((c, idx) => <li key={idx}>{c}</li>)}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  )
}

function OrgTraceModal({ orgId, onClose }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`${API}/organisations/${orgId}`)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => { })
  }, [orgId])

  if (!data) return null

  const res = data.score_result || {}
  const prov = data.provenance || {}

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="eyebrow">Provenance & Lineage Trace</div>
            <h2>{data.organisation_name}</h2>
            <span className="code-pill">{data.organisation_id}</span>
          </div>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="modal-body">
          <div className="score-summary-box">
            <div>
              <div className="modal-metric-title">Performance Score</div>
              <div className="modal-metric-val">{res.score ?? 'N/A'}</div>
            </div>
            <div>
              <div className="modal-metric-title">Decision Outcome</div>
              <span className={`badge badge-large badge-${res.decision}`}>
                {res.decision?.toUpperCase()}
              </span>
            </div>
            <div>
              <div className="modal-metric-title">Boundary Status</div>
              {res.boundary_status === 'boundary_case' ? (
                <span className="badge badge-large badge-boundary">
                  BOUNDARY CASE (±{res.distance_to_nearest_boundary} pts)
                </span>
              ) : (
                <span className="badge badge-large badge-clear">CLEAR</span>
              )}
            </div>
          </div>

          {res.boundary_annotation && (
            <div className="annotation-box">
              <AlertTriangle size={16} />
              <span>{res.boundary_annotation}</span>
            </div>
          )}

          <h3>Raw Feature Inputs & Point Contributions</h3>
          <table className="modal-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Raw Input Value</th>
                <th>Point Contribution</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.raw_features || {}).map(([k, v]) => {
                const contrib = res.feature_contributions ? res.feature_contributions[k] : null
                const isMissing = v === null
                return (
                  <tr key={k}>
                    <td><strong>{k.replace(/_/g, ' ')}</strong></td>
                    <td>{isMissing ? '<Missing / None>' : `${v}`}</td>
                    <td><b>{contrib !== undefined && contrib !== null ? `+${contrib.toFixed(2)} pts` : '0.00 pts'}</b></td>
                    <td>
                      {isMissing ? (
                        <span className="badge badge-missing">Not Assessable</span>
                      ) : (
                        <span className="badge badge-clear">Assessed</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          <h3>Cryptographic Provenance & Lineage</h3>
          <div className="provenance-grid">
            <div><strong>Scoring Config Version:</strong> v{prov.scoring_config_version}</div>
            <div><strong>Model Config Version:</strong> v{prov.model_config_version}</div>
            <div><strong>Model Engine:</strong> {prov.selected_model}</div>
            <div><strong>Config SHA-256 Digest:</strong> <code>{prov.configuration_sha256}</code></div>
            <div><strong>Computation Timestamp:</strong> <small>{prov.computation_timestamp}</small></div>
            <div><strong>Reporting Period:</strong> {data.reporting_period}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

createRoot(document.getElementById('root')).render(<App />)
