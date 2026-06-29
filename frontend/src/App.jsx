import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

/* ─────────────── constants ─────────────── */

const CUSTOMERS = [
  { id: 'C001', name: 'ABC Manufacturing' },
  { id: 'C002', name: 'Pinnacle Healthcare' },
  { id: 'C003', name: 'NovaTech Solutions' },
  { id: 'C004', name: 'GreenLeaf Retail' },
  { id: 'C005', name: 'Meridian Logistics' },
  { id: 'C006', name: 'Atlas Finserv' },
  { id: 'C007', name: 'Orion Enterprises' },
  { id: 'C008', name: 'Vanguard Media' },
  { id: 'C009', name: 'FreshHire Staffing' },
  { id: 'C010', name: 'BrightPath Education' },
];

const LOADING_STEPS = [
  'Uploading Transcript…',
  'Planner Agent Running…',
  'Analyzing Customer…',
  'Detecting Risks…',
  'Finding Opportunities…',
  'Searching Knowledge Base…',
  'Generating Recommendations…',
  'Preparing Explanations…',
  'Loading Dashboard…',
];

/* Maps agent name → { color, icon } for React Flow nodes */
const AGENT_META = {
  'Planner Agent':        { bg: '#6366f1', icon: '🧠' },
  'Customer Agent':       { bg: '#0ea5e9', icon: '👤' },
  'Knowledge Agent':      { bg: '#8b5cf6', icon: '📚' },
  'Sentiment Agent':      { bg: '#f59e0b', icon: '💬' },
  'Risk Agent':           { bg: '#ef4444', icon: '⚠' },
  'Opportunity Agent':    { bg: '#10b981', icon: '💡' },
  'Recommendation Agent': { bg: '#3b82f6', icon: '🎯' },
  'Action Executor':      { bg: '#f97316', icon: '⚡' },
};

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();

function buildApiUrl(path) {
  const base = apiBaseUrl.replace(/\/$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

/* ─────────────── helpers ─────────────── */

function getHealthTone(score) {
  const n = Number(score || 0);
  if (n > 70) return { label: 'Healthy',  cls: 'bg-emerald-100 text-emerald-700',  bar: 'bg-emerald-500' };
  if (n >= 40) return { label: 'Watch',   cls: 'bg-amber-100 text-amber-700',    bar: 'bg-amber-500' };
  return              { label: 'At Risk', cls: 'bg-rose-100 text-rose-700',      bar: 'bg-rose-500' };
}

function getRiskTone(sev) {
  const v = String(sev || '').toLowerCase();
  if (v.includes('high'))   return { label: 'High',   cls: 'bg-rose-100 text-rose-700',   ring: 'border-rose-200 bg-rose-50',    icon: '⚠' };
  if (v.includes('medium')) return { label: 'Medium', cls: 'bg-amber-100 text-amber-700', ring: 'border-amber-200 bg-amber-50',  icon: '📉' };
  return                           { label: 'Low',    cls: 'bg-emerald-100 text-emerald-700', ring: 'border-emerald-200 bg-emerald-50', icon: '🛠' };
}

function getPriorityTone(p) {
  const v = String(p || '').toLowerCase();
  if (v.includes('high'))   return 'bg-rose-100 text-rose-700';
  if (v.includes('medium')) return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
}

function formatTimestamp(v) {
  if (!v) return '—';
  const d = new Date(v);
  return isNaN(d) ? String(v) : d.toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function Spinner({ className = 'h-4 w-4' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
    </svg>
  );
}

/* ─────────────── React Flow custom node ─────────────── */

function AgentNode({ data }) {
  const statusStyles = {
    completed: 'border-emerald-400 bg-emerald-50 shadow-emerald-200',
    running:   'border-sky-400   bg-sky-50   shadow-sky-200   animate-pulse',
    skipped:   'border-slate-300 bg-slate-50 shadow-slate-100 opacity-60',
    pending:   'border-slate-300 bg-white    shadow-slate-100',
    hitl:      'border-amber-400 bg-amber-50 shadow-amber-200',
  };
  const badgeStyles = {
    completed: 'bg-emerald-100 text-emerald-700',
    running:   'bg-sky-100   text-sky-700',
    skipped:   'bg-slate-100 text-slate-500',
    pending:   'bg-slate-100 text-slate-500',
    hitl:      'bg-amber-100 text-amber-700',
  };
  const status = data.status || 'pending';

  return (
    <div className={`rounded-2xl border-2 shadow-md px-4 py-3 min-w-[160px] transition-all duration-300 ${statusStyles[status]}`}>
      <Handle type="target" position={Position.Left} style={{ background: '#94a3b8' }} />
      <div className="flex items-center gap-2">
        <span className="text-xl">{data.icon}</span>
        <div>
          <p className="text-xs font-bold text-slate-700">{data.label}</p>
          <span className={`inline-block mt-1 rounded-full px-2 py-0.5 text-xs font-semibold ${badgeStyles[status]}`}>
            {status === 'completed' ? '✓ Done' : status === 'running' ? '⟳ Running' : status === 'hitl' ? '⏸ HITL' : status === 'skipped' ? 'Skipped' : 'Pending'}
          </span>
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#94a3b8' }} />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

/* ─────────────── Graph layout ─────────────── */

function buildFlowNodes(trace, agentsDone) {
  const rows = [
    [{ id: 'planner_node', label: 'Planner Agent', icon: '🧠', x: 0 }],
    [
      { id: 'customer_agent',   label: 'Customer Agent',    icon: '👤', x: 0 },
      { id: 'knowledge_agent',  label: 'Knowledge Agent',   icon: '📚', x: 1 },
      { id: 'sentiment_agent',  label: 'Sentiment Agent',   icon: '💬', x: 2 },
    ],
    [
      { id: 'risk_agent',        label: 'Risk Agent',        icon: '⚠', x: 0 },
      { id: 'opportunity_agent', label: 'Opportunity Agent', icon: '💡', x: 1 },
    ],
    [{ id: 'recommendation_agent', label: 'Recommendation Agent', icon: '🎯', x: 0 }],
    [{ id: 'action_execution_node', label: 'Action Executor', icon: '⚡', x: 0 }],
  ];

  const doneIds = new Set((trace || []).filter(t => t.status === 'completed').map(t => t.agent_name));
  const runningIds = new Set((trace || []).filter(t => t.status === 'running').map(t => t.agent_name));

  const nodeList = [];
  rows.forEach((row, rowIdx) => {
    const colW = 220;
    const totalW = row.length * colW;
    row.forEach((n, colIdx) => {
      const status = doneIds.has(n.id) ? 'completed'
        : runningIds.has(n.id) ? 'running'
        : n.id === 'action_execution_node' && agentsDone ? 'hitl'
        : 'pending';
      nodeList.push({
        id: n.id,
        type: 'agentNode',
        data: { label: n.label, icon: n.icon, status },
        position: { x: colIdx * colW - totalW / 2 + colW / 2 + 400, y: rowIdx * 110 + 40 },
      });
    });
  });
  return nodeList;
}

function buildFlowEdges() {
  return [
    { id: 'e1', source: 'planner_node', target: 'customer_agent',      animated: true },
    { id: 'e2', source: 'planner_node', target: 'knowledge_agent',      animated: true },
    { id: 'e3', source: 'planner_node', target: 'sentiment_agent',      animated: true },
    { id: 'e4', source: 'customer_agent',   target: 'risk_agent',        animated: true },
    { id: 'e5', source: 'knowledge_agent',  target: 'risk_agent',        animated: true },
    { id: 'e6', source: 'sentiment_agent',  target: 'opportunity_agent', animated: true },
    { id: 'e7', source: 'risk_agent',        target: 'recommendation_agent', animated: true },
    { id: 'e8', source: 'opportunity_agent', target: 'recommendation_agent', animated: true },
    { id: 'e9', source: 'recommendation_agent', target: 'action_execution_node',
      animated: true, label: '⏸ HITL Interrupt',
      style: { stroke: '#f59e0b', strokeWidth: 2 },
      labelStyle: { fill: '#92400e', fontWeight: 600, fontSize: 11 } },
  ];
}

/* ─────────────── main app ─────────────── */

export default function App() {
  const navigate  = useNavigate();
  const location  = useLocation();

  /* form / session */
  const [customerId,   setCustomerId]   = useState('C001');
  const [transcript,   setTranscript]   = useState('ABC Manufacturing has low analytics adoption, renewal in 20 days, and SAP integration is slow. Team exports to Excel instead of dashboards. VP is considering BambooHR and Workday.');
  const [isLoading,    setIsLoading]    = useState(false);
  const [loadingIdx,   setLoadingIdx]   = useState(0);
  const [loadingPct,   setLoadingPct]   = useState(10);
  const [error,        setError]        = useState('');
  const [sessionId,    setSessionId]    = useState('');

  /* dashboard data */
  const [summary,         setSummary]         = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [risks,           setRisks]           = useState([]);
  const [explanations,    setExplanations]    = useState([]);
  const [historyItems,    setHistoryItems]    = useState([]);
  const [historyLoading,  setHistoryLoading]  = useState(false);
  const [historyError,    setHistoryError]    = useState('');

  /* actions */
  const [toast,           setToast]           = useState(null);
  const [approvingId,     setApprovingId]     = useState('');
  const [executingId,     setExecutingId]     = useState('');
  const [executionResult, setExecutionResult] = useState({});

  /* React Flow */
  const [trace,           setTrace]           = useState([]);
  const [rfNodes,         setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges,         setRfEdges, onEdgesChange] = useEdgesState(buildFlowEdges());

  const selectedCustomer = useMemo(() => CUSTOMERS.find(c => c.id === customerId), [customerId]);
  const isDashboard = location.pathname === '/dashboard';
  const healthScore = Number(summary?.healthScore || 0);
  const healthTone  = summary ? getHealthTone(healthScore) : null;
  const agentsDone  = recommendations.length > 0;

  /* Sync React Flow nodes whenever trace changes */
  useEffect(() => {
    setRfNodes(buildFlowNodes(trace, agentsDone));
  }, [trace, agentsDone]);

  /* Fetch trace for current session */
  const refreshTrace = useCallback(async (sid) => {
    if (!sid) return;
    try {
      const r = await fetch(buildApiUrl(`/agent_trace/${sid}`));
      if (r.ok) {
        const d = await r.json();
        setTrace(d.trace || []);
      }
    } catch { /* silent */ }
  }, []);

  /* History */
  async function loadHistory(cid) {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const r = await fetch(buildApiUrl(`/history/${cid}`));
      if (!r.ok) throw new Error('Unable to load approval history.');
      const d = await r.json();
      setHistoryItems(Array.isArray(d) ? d : []);
    } catch (e) {
      setHistoryError(e.message || 'Unable to load approval history.');
    } finally {
      setHistoryLoading(false);
    }
  }

  /* Approve (legacy /approve — stores to memory/DB) */
  async function handleApprove(recId) {
    if (!sessionId || !recId) return;
    setApprovingId(recId);
    setToast(null);
    try {
      const r = await fetch(buildApiUrl('/approve'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, recommendation_id: recId }),
      });
      if (!r.ok) throw new Error('Unable to approve recommendation.');
      await loadHistory(customerId);
      setToast({ type: 'success', message: 'Recommendation approved — ready to execute.' });
    } catch (e) {
      setToast({ type: 'error', message: e.message || 'Unable to approve.' });
    } finally {
      setApprovingId('');
    }
  }

  /* Execute (/approve_action — resumes LangGraph HITL) */
  async function handleExecute(recId) {
    if (!sessionId || !recId) return;
    setExecutingId(recId);
    setToast(null);
    try {
      const r = await fetch(buildApiUrl('/approve_action'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, recommendation_id: recId, approved: true }),
      });
      if (!r.ok) throw new Error('Unable to execute action.');
      const d = await r.json();
      const result = d.execution_result || {};
      setExecutionResult(prev => ({ ...prev, [recId]: result }));
      await refreshTrace(sessionId);
      setToast({ type: 'success', message: result.action || 'Action executed successfully!' });
      await loadHistory(customerId);
    } catch (e) {
      setToast({ type: 'error', message: e.message || 'Unable to execute action.' });
    } finally {
      setExecutingId('');
    }
  }

  /* Upload transcript */
  async function handleUpload(e) {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSummary(null);
    setRecommendations([]);
    setRisks([]);
    setExplanations([]);
    setTrace([]);
    setExecutionResult({});
    setLoadingIdx(0);
    setLoadingPct(10);

    try {
      setLoadingIdx(0); setLoadingPct(12);
      await delay(200);
      const uploadRes = await fetch(buildApiUrl('/upload_transcript'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, transcript_text: transcript }),
      });
      if (!uploadRes.ok) throw new Error('Upload failed.');

      setLoadingIdx(1); setLoadingPct(24);
      await delay(200);
      const { session_id } = await uploadRes.json();
      setSessionId(session_id);

      setLoadingIdx(2); setLoadingPct(38);
      await delay(200);
      const recRes = await fetch(buildApiUrl(`/recommendation/${session_id}`));
      if (!recRes.ok) throw new Error('Failed to fetch recommendations.');

      setLoadingIdx(5); setLoadingPct(70);
      await delay(200);
      const rec = await recRes.json();

      const cs = rec.customer_summary || {};
      setSummary({
        company:         cs.company || selectedCustomer?.name || customerId,
        healthScore:     cs.health_score || 0,
        renewalCountdown: cs.days_to_renewal || 0,
        supportTickets:  cs.open_support_tickets || 0,
        plan:            cs.plan || '—',
        activeUsers:     cs.active_users || 0,
        licensedUsers:   cs.licensed_users || 0,
        dashboardUsage:  cs.dashboard_usage_pct || 0,
        owner:           cs.owner || '—',
      });
      setRecommendations(rec.recommendations?.recommendations || []);
      setRisks(rec.risks?.risks || []);
      setExplanations(rec.explanations?.explanations || []);

      setLoadingIdx(7); setLoadingPct(88);
      await delay(200);
      await loadHistory(customerId);
      await refreshTrace(session_id);

      setLoadingIdx(8); setLoadingPct(100);
      await delay(200);
      setToast({ type: 'success', message: 'Analysis complete — review your recommendations.' });
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Unexpected error.');
      setToast({ type: 'error', message: err.message || 'Unexpected error.' });
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (isDashboard && customerId) loadHistory(customerId);
  }, [location.pathname, customerId]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(t);
  }, [toast]);

  /* sorted history */
  const sortedHistory = useMemo(() =>
    [...historyItems].sort((a, b) => Date.parse(b.approved_at || 0) - Date.parse(a.approved_at || 0)),
    [historyItems]);

  const highRiskCount   = risks.filter(r => String(r.severity || '').toLowerCase().includes('high')).length;
  const mediumRiskCount = risks.filter(r => String(r.severity || '').toLowerCase().includes('medium')).length;

  const statCards = [
    { label: 'Recommendations', value: recommendations.length, color: 'text-sky-600' },
    { label: 'High Risks',       value: highRiskCount,          color: 'text-rose-600' },
    { label: 'Medium Risks',     value: mediumRiskCount,        color: 'text-amber-600' },
    { label: 'Prior Approvals',  value: historyItems.length,    color: 'text-emerald-600' },
  ];

  /* ─── render ─── */
  return (
    <div style={{ fontFamily: "'Inter', sans-serif" }} className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100">
      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm px-4">
          <div className="w-full max-w-xl rounded-3xl border border-slate-700 bg-slate-900 p-8 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Agentic AI Pipeline</p>
                <h2 className="mt-1 text-2xl font-bold text-white">Analyzing customer insights…</h2>
              </div>
              <div className="rounded-full bg-indigo-900/60 p-3 text-indigo-400"><Spinner className="h-6 w-6" /></div>
            </div>
            <div className="mt-6 h-2 rounded-full bg-slate-700 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500 transition-all duration-500" style={{ width: `${loadingPct}%` }} />
            </div>
            <div className="mt-4 grid gap-2">
              {LOADING_STEPS.map((step, i) => {
                const done   = i < loadingIdx;
                const active = i === loadingIdx;
                return (
                  <div key={step} className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all ${done ? 'bg-emerald-900/40 text-emerald-400' : active ? 'bg-indigo-900/50 text-indigo-300' : 'text-slate-500'}`}>
                    <span className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${done ? 'bg-emerald-500 text-white' : active ? 'bg-indigo-500 text-white' : 'bg-slate-700 text-slate-400'}`}>
                      {done ? '✓' : i + 1}
                    </span>
                    {step}
                    {active && <Spinner className="ml-auto h-3 w-3 text-indigo-400" />}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/60 backdrop-blur-md px-6 py-4 sticky top-0 z-40">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-lg font-bold shadow-lg shadow-indigo-500/30">⚡</div>
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-indigo-400">XL Ventures</p>
              <h1 className="text-base font-bold text-white leading-tight">Customer Success Copilot</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {sessionId && (
              <span className="rounded-full bg-emerald-900/50 border border-emerald-700/50 px-3 py-1 text-xs text-emerald-400 font-mono">
                Session: {sessionId.slice(0, 8)}…
              </span>
            )}
            <button onClick={() => navigate(isDashboard ? '/' : '/dashboard')}
              className="rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2 text-sm font-medium text-slate-300 hover:border-indigo-500 hover:text-indigo-300 transition-all">
              {isDashboard ? '← New Analysis' : 'Dashboard →'}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 space-y-8">
        {/* Toast */}
        {toast && (
          <div className={`rounded-2xl border px-4 py-3 text-sm font-medium transition-all ${toast.type === 'success' ? 'border-emerald-700 bg-emerald-900/50 text-emerald-300' : 'border-rose-700 bg-rose-900/50 text-rose-300'}`}>
            {toast.message}
          </div>
        )}

        {/* Upload Form */}
        {!isDashboard && (
          <form onSubmit={handleUpload} className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6 space-y-5">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-4">New Analysis</p>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Customer Account</label>
                <select value={customerId} onChange={e => setCustomerId(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white focus:border-indigo-500 focus:outline-none transition-colors">
                  {CUSTOMERS.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">Meeting Transcript</label>
                <textarea value={transcript} onChange={e => setTranscript(e.target.value)} rows={10}
                  className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none resize-none transition-colors"
                  placeholder="Paste meeting transcript, CRM notes, or email thread here…" />
              </div>
              {error && <p className="rounded-xl border border-rose-700 bg-rose-900/40 px-4 py-3 text-sm text-rose-300">{error}</p>}
              <button type="submit" disabled={isLoading}
                className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                {isLoading ? <><Spinner className="h-4 w-4" /> Analyzing…</> : '🚀 Run AI Analysis'}
              </button>
            </div>

            <div className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6 flex flex-col gap-4">
              <p className="text-xs font-bold uppercase tracking-widest text-indigo-400">Agent Pipeline</p>
              <p className="text-sm text-slate-400">The multi-agent system will analyze your transcript through a dynamic pipeline:</p>
              {['🧠 Planner Agent', '👤 Customer Agent', '📚 Knowledge Agent', '💬 Sentiment Agent', '⚠ Risk Agent', '💡 Opportunity Agent', '🎯 Recommendation Agent', '⚡ Action Executor'].map(step => (
                <div key={step} className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-800/60 px-3 py-2 text-sm text-slate-300">
                  {step}
                </div>
              ))}
            </div>
          </form>
        )}

        {/* Dashboard */}
        {isDashboard && (
          <div className="space-y-8">
            {/* React Flow Agent Graph */}
            <section className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-indigo-400">Live Execution</p>
                  <h2 className="text-lg font-bold text-white">Agent Execution Graph</h2>
                </div>
                <div className="flex items-center gap-3 text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400 inline-block"/> Completed</span>
                  <span className="flex items-center gap-1.5 text-sky-400"><span className="h-2 w-2 rounded-full bg-sky-400 inline-block"/> Running</span>
                  <span className="flex items-center gap-1.5 text-amber-400"><span className="h-2 w-2 rounded-full bg-amber-400 inline-block"/> HITL Interrupt</span>
                  <span className="flex items-center gap-1.5 text-slate-500"><span className="h-2 w-2 rounded-full bg-slate-500 inline-block"/> Pending</span>
                </div>
              </div>
              <div style={{ height: 480, background: '#0f172a' }}>
                <ReactFlow
                  nodes={rfNodes}
                  edges={rfEdges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  nodeTypes={nodeTypes}
                  fitView
                  proOptions={{ hideAttribution: true }}
                >
                  <Background color="#1e293b" gap={24} />
                  <Controls style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                </ReactFlow>
              </div>
            </section>

            {/* Stat Cards */}
            <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
              {statCards.map(c => (
                <div key={c.label} className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-5 hover:-translate-y-1 hover:border-indigo-700 transition-all">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{c.label}</p>
                  <p className={`mt-2 text-4xl font-bold ${c.color}`}>{c.value}</p>
                </div>
              ))}
            </div>

            {/* Customer Health */}
            {summary && (
              <section className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-indigo-400">Customer Health</p>
                    <h2 className="text-2xl font-bold text-white">{summary.company}</h2>
                  </div>
                  {healthTone && (
                    <span className={`rounded-full px-4 py-1.5 text-sm font-bold ${healthTone.cls}`}>{healthTone.label}</span>
                  )}
                </div>
                <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
                  {[
                    { label: 'Health Score',    value: `${summary.healthScore}/100` },
                    { label: 'Renewal',          value: `${summary.renewalCountdown}d` },
                    { label: 'Support Tickets',  value: summary.supportTickets },
                    { label: 'Plan',             value: summary.plan },
                    { label: 'Active Users',     value: `${summary.activeUsers}/${summary.licensedUsers}` },
                    { label: 'Dashboard Usage',  value: `${summary.dashboardUsage}%` },
                  ].map(m => (
                    <div key={m.label} className="rounded-2xl border border-slate-700 bg-slate-800/50 p-4 text-center">
                      <p className="text-xs text-slate-500 font-medium mb-1">{m.label}</p>
                      <p className="text-xl font-bold text-white">{m.value}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-5">
                  <div className="flex justify-between text-xs text-slate-500 mb-2">
                    <span>Customer Health</span>
                    <span>{summary.healthScore}%</span>
                  </div>
                  <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${healthTone?.bar || 'bg-slate-600'}`}
                      style={{ width: `${Math.max(0, Math.min(100, summary.healthScore))}%` }} />
                  </div>
                </div>
              </section>
            )}

            {/* Risks + Recommendations */}
            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              {/* Risk Cards */}
              <section className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-bold text-white">Risk Signals</h3>
                  <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-0.5 text-xs text-slate-400">{risks.length}</span>
                </div>
                <div className="space-y-3">
                  {risks.length > 0 ? risks.map((risk, i) => {
                    const tone = getRiskTone(risk.severity);
                    return (
                      <div key={i} className={`rounded-2xl border p-4 ${tone.ring}`}>
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-2">
                            <span className="text-xl mt-0.5">{tone.icon}</span>
                            <div>
                              <p className="text-sm font-bold text-slate-800">{risk.type || 'Risk'}</p>
                              <p className="mt-1 text-xs text-slate-600">{risk.evidence || '—'}</p>
                            </div>
                          </div>
                          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${tone.cls}`}>{tone.label}</span>
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="rounded-2xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">
                      No risks detected yet.
                    </div>
                  )}
                </div>
              </section>

              {/* Recommendations */}
              <section className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6">
                <div className="flex items-center justify-between mb-5">
                  <h3 className="font-bold text-white">Next Best Actions</h3>
                  <span className="rounded-full border border-slate-700 bg-slate-800 px-2.5 py-0.5 text-xs text-slate-400">{recommendations.length}</span>
                </div>
                <div className="space-y-4">
                  {recommendations.length > 0 ? recommendations.map((item, i) => {
                    const expl = explanations[i] || {};
                    const execRes = executionResult[item.id];
                    const confidence = Math.round(Number(item.confidence || 0) * 100);
                    // evidence now has {source, data} objects
                    const evidenceItems = (expl.evidence || []);
                    return (
                      <div key={item.id || i} className="rounded-2xl border border-slate-700 bg-slate-800/50 p-4 hover:border-indigo-600 transition-all">
                        {/* Action + badges */}
                        <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
                          <p className="text-sm font-bold text-white flex-1">{item.action}</p>
                          <div className="flex gap-2 flex-wrap">
                            <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${getPriorityTone(item.priority)}`}>{item.priority}</span>
                            <span className="rounded-full bg-slate-700 px-2.5 py-0.5 text-xs text-slate-300">
                              {confidence}% confidence
                            </span>
                          </div>
                        </div>

                        {/* Confidence bar */}
                        <div className="mb-3">
                          <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
                            <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500 transition-all duration-700"
                              style={{ width: `${confidence}%` }} />
                          </div>
                        </div>

                        {/* Reasoning */}
                        {expl.reasoning && (
                          <p className="text-xs text-slate-400 mb-3 italic">"{expl.reasoning}"</p>
                        )}

                        {/* Evidence pills */}
                        {evidenceItems.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {evidenceItems.map((ev, ei) => {
                              const src = typeof ev === 'object' ? ev.source : 'CRM';
                              const dat = typeof ev === 'object' ? ev.data : ev;
                              const srcColors = {
                                'Meeting Transcript': 'border-sky-700 bg-sky-900/40 text-sky-300',
                                'Knowledge Base':     'border-purple-700 bg-purple-900/40 text-purple-300',
                                'Support Tickets':    'border-rose-700 bg-rose-900/40 text-rose-300',
                                'CRM':                'border-emerald-700 bg-emerald-900/40 text-emerald-300',
                              };
                              return (
                                <span key={ei} title={dat}
                                  className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${srcColors[src] || srcColors['CRM']}`}>
                                  {src}
                                </span>
                              );
                            })}
                          </div>
                        )}

                        {/* Execution result */}
                        {execRes && (
                          <div className={`mb-3 rounded-xl border px-3 py-2 text-xs font-medium ${execRes.status === 'success' ? 'border-emerald-700 bg-emerald-900/40 text-emerald-300' : 'border-rose-700 bg-rose-900/40 text-rose-300'}`}>
                            ⚡ {execRes.action || 'Action executed'}
                          </div>
                        )}

                        {/* Actions row */}
                        <div className="flex items-center gap-2 pt-1">
                          <button onClick={() => handleApprove(item.id)} disabled={!!approvingId}
                            className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-slate-600 bg-slate-700/60 px-3 py-2 text-xs font-bold text-slate-300 hover:border-indigo-500 hover:text-indigo-300 disabled:opacity-50 transition-all">
                            {approvingId === item.id ? <><Spinner className="h-3 w-3" /> Approving…</> : '✓ Approve'}
                          </button>
                          <button onClick={() => handleExecute(item.id)} disabled={!!executingId}
                            className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-indigo-600 bg-indigo-700/60 px-3 py-2 text-xs font-bold text-indigo-200 hover:bg-indigo-600 hover:border-indigo-400 disabled:opacity-50 transition-all">
                            {executingId === item.id ? <><Spinner className="h-3 w-3" /> Executing…</> : '⚡ Execute'}
                          </button>
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="rounded-2xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">
                      No recommendations yet. Upload a transcript to begin.
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* Approval History */}
            <section className="rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6">
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="font-bold text-white">Approval History</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Outcome learning — past approved actions for this customer</p>
                </div>
                <span className="text-xs text-slate-500">{historyItems.length} entries</span>
              </div>
              {historyLoading && <div className="flex items-center gap-2 text-sm text-slate-500 py-4"><Spinner className="h-4 w-4" /> Loading…</div>}
              {historyError && <div className="rounded-xl border border-rose-700 bg-rose-900/30 px-4 py-3 text-sm text-rose-300">{historyError}</div>}
              {!historyLoading && sortedHistory.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                        <th className="pb-3 pr-4">Action</th>
                        <th className="pb-3 pr-4">Priority</th>
                        <th className="pb-3 pr-4">Confidence</th>
                        <th className="pb-3">Approved At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {sortedHistory.map((item, i) => (
                        <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-3 pr-4">
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-900/50 border border-emerald-700/50 px-2 py-0.5 text-xs text-emerald-400 font-semibold mb-1">✓ Approved</span>
                            <p className="text-slate-300 text-xs mt-1">{item.action || 'Approved recommendation'}</p>
                          </td>
                          <td className="py-3 pr-4 text-slate-400 text-xs">{item.priority || '—'}</td>
                          <td className="py-3 pr-4 text-slate-400 text-xs">{item.confidence ?? '—'}</td>
                          <td className="py-3 text-slate-400 text-xs">{formatTimestamp(item.approved_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : !historyLoading && (
                <div className="rounded-2xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">
                  No approvals yet for this customer.
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
