import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

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

const AGENT_STEPS = [
  'Planner Agent',
  'Customer Agent',
  'Knowledge Agent',
  'Sentiment Agent',
  'Risk Agent',
  'Opportunity Agent',
  'Recommendation Agent',
  'Explainability Agent',
  'Memory Agent',
];

const LOADING_STEPS = [
  'Uploading Transcript...',
  'Planner Agent Running...',
  'Analyzing Customer...',
  'Detecting Risks...',
  'Finding Opportunities...',
  'Searching Knowledge Base...',
  'Generating Recommendations...',
  'Preparing Explanations...',
  'Loading Dashboard...',
];

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();

function buildApiUrl(path) {
  const normalizedBase = apiBaseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function getHealthTone(healthScore) {
  const numeric = Number(healthScore || 0);
  if (numeric > 70) return { label: 'Healthy', classes: 'bg-emerald-100 text-emerald-700' };
  if (numeric >= 40) return { label: 'Watch', classes: 'bg-amber-100 text-amber-700' };
  return { label: 'At Risk', classes: 'bg-rose-100 text-rose-700' };
}

function getRiskTone(severity) {
  const value = String(severity || '').toLowerCase();
  if (value.includes('high')) return { label: 'High', classes: 'bg-rose-100 text-rose-700', icon: '⚠', ring: 'border-rose-200 bg-rose-50' };
  if (value.includes('medium')) return { label: 'Medium', classes: 'bg-amber-100 text-amber-700', icon: '📉', ring: 'border-amber-200 bg-amber-50' };
  return { label: 'Low', classes: 'bg-emerald-100 text-emerald-700', icon: '🛠', ring: 'border-emerald-200 bg-emerald-50' };
}

function getPriorityTone(priority) {
  const value = String(priority || '').toLowerCase();
  if (value.includes('high')) return 'bg-rose-100 text-rose-700';
  if (value.includes('medium')) return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
}

function classifyEvidence(evidenceText) {
  const normalized = String(evidenceText || '').toLowerCase();
  if (/(transcript|meeting|conversation|team exports|dashboard)/.test(normalized)) return 'Meeting Transcript';
  if (/(guide|playbook|sop|faq|training|integration|onboarding)/.test(normalized)) return 'Knowledge Base';
  if (/(ticket|support)/.test(normalized)) return 'Support Tickets';
  return 'CRM';
}

function buildEvidenceGroups(evidenceItems) {
  const groups = [
    { label: 'Meeting Transcript', items: [] },
    { label: 'CRM', items: [] },
    { label: 'Knowledge Base', items: [] },
    { label: 'Support Tickets', items: [] },
  ];

  (evidenceItems || []).forEach((item) => {
    const label = classifyEvidence(item);
    const group = groups.find((entry) => entry.label === label);
    if (group) {
      group.items.push(item);
    }
  });

  return groups.filter((group) => group.items.length > 0);
}

function formatTimestamp(value) {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function Spinner({ className = 'h-4 w-4' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Zm0 0a8 8 0 0 0 8 8v4c-6.627 0-12-5.373-12-12h4Z" />
    </svg>
  );
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [customerId, setCustomerId] = useState('C001');
  const [transcript, setTranscript] = useState('ABC Manufacturing has low analytics adoption, renewal in 20 days, and SAP integration is slow.');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(10);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [summary, setSummary] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [risks, setRisks] = useState([]);
  const [explanations, setExplanations] = useState([]);
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [toast, setToast] = useState(null);
  const [approvingId, setApprovingId] = useState('');

  const selectedCustomer = useMemo(() => CUSTOMERS.find((customer) => customer.id === customerId), [customerId]);
  const sortedHistoryItems = useMemo(() => {
    return [...historyItems].sort((first, second) => {
      const firstTime = Date.parse(first.approved_at || 0);
      const secondTime = Date.parse(second.approved_at || 0);
      return (Number.isNaN(secondTime) ? 0 : secondTime) - (Number.isNaN(firstTime) ? 0 : firstTime);
    });
  }, [historyItems]);

  async function loadHistory(customer) {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const response = await fetch(buildApiUrl(`/history/${customer}`));
      if (!response.ok) {
        throw new Error('Unable to load approval history.');
      }
      const data = await response.json();
      setHistoryItems(Array.isArray(data) ? data : []);
    } catch (error) {
      setHistoryError(error.message || 'Unable to load approval history.');
      console.error('Unable to fetch history', error);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function handleApprove(recommendationId) {
    if (!sessionId || !recommendationId) {
      setToast({ type: 'error', message: 'Select a recommendation before approving.' });
      return;
    }

    setApprovingId(recommendationId);
    setToast(null);

    try {
      const response = await fetch(buildApiUrl('/approve'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, recommendation_id: recommendationId }),
      });

      if (!response.ok) {
        throw new Error('Unable to approve recommendation.');
      }

      await loadHistory(customerId);
      setToast({ type: 'success', message: 'Recommendation approved successfully.' });
    } catch (err) {
      setToast({ type: 'error', message: err.message || 'Unable to approve recommendation.' });
    } finally {
      setApprovingId('');
    }
  }

  async function handleUpload(event) {
    event.preventDefault();
    setIsLoading(true);
    setError('');
    setSummary(null);
    setRecommendations([]);
    setRisks([]);
    setExplanations([]);
    setLoadingStepIndex(0);
    setLoadingProgress(10);

    try {
      setLoadingStepIndex(0);
      setLoadingProgress(12);
      await new Promise((resolve) => window.setTimeout(resolve, 250));
      const response = await fetch(buildApiUrl('/upload_transcript'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, transcript_text: transcript }),
      });

      if (!response.ok) {
        throw new Error('Unable to upload transcript.');
      }

      setLoadingStepIndex(1);
      setLoadingProgress(24);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      const data = await response.json();
      setSessionId(data.session_id);

      setLoadingStepIndex(2);
      setLoadingProgress(36);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      const recResponse = await fetch(buildApiUrl(`/recommendation/${data.session_id}`));
      if (!recResponse.ok) {
        throw new Error('Unable to fetch recommendation summary.');
      }

      setLoadingStepIndex(4);
      setLoadingProgress(58);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      const recData = await recResponse.json();
      const customerSummary = recData.customer_summary || {};
      const summaryData = {
        company: customerSummary.company || selectedCustomer?.name || customerId,
        healthScore: customerSummary.health_score || 0,
        renewalCountdown: customerSummary.days_to_renewal || 0,
        supportTickets: customerSummary.open_support_tickets || 0,
      };
      setSummary(summaryData);
      setRecommendations(recData.recommendations?.recommendations || []);
      setRisks(recData.risks?.risks || []);
      setExplanations(recData.explanations?.explanations || []);
      setLoadingStepIndex(7);
      setLoadingProgress(88);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      setToast({ type: 'success', message: 'Transcript uploaded successfully.' });
      await loadHistory(customerId);
      setLoadingStepIndex(8);
      setLoadingProgress(100);
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      navigate('/dashboard');
    } catch (err) {
      const message = err.message || 'Unexpected error.';
      setError(message);
      setToast({ type: 'error', message });
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (location.pathname === '/dashboard' && customerId) {
      loadHistory(customerId);
    }
  }, [location.pathname, customerId]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const isDashboard = location.pathname === '/dashboard';
  const healthScore = Number(summary?.healthScore || 0);
  const healthPercent = Math.max(0, Math.min(100, healthScore));
  const healthTone = summary ? getHealthTone(healthScore) : null;
  const highRiskCount = risks.filter((item) => String(item.severity || item.level || item.priority || '').toLowerCase().includes('high')).length;
  const mediumRiskCount = risks.filter((item) => String(item.severity || item.level || item.priority || '').toLowerCase().includes('medium')).length;
  const statCards = [
    { label: 'Recommendations Generated', value: recommendations.length },
    { label: 'High Risks', value: highRiskCount },
    { label: 'Medium Risks', value: mediumRiskCount },
    { label: 'Previous Approvals', value: historyItems.length },
  ];

  return (
    <div className="min-h-screen bg-slate-50 px-3 py-6 text-slate-800 sm:px-4 lg:px-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">XL Ventures</p>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight">Customer Success Copilot</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-600">Upload a customer transcript and review the generated customer summary, risk cues, and recommendations.</p>
            </div>
            <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600 shadow-sm">
              {isDashboard ? 'Customer Summary Dashboard' : 'Upload Transcript'}
            </div>
          </div>
        </header>

        {isLoading ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm">
            <div className="w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-8 shadow-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-600">Working on your request</p>
                  <h2 className="mt-1 text-2xl font-semibold">Analyzing customer insights</h2>
                </div>
                <div className="rounded-full bg-sky-50 p-3 text-sky-600">
                  <Spinner className="h-6 w-6" />
                </div>
              </div>
              <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-gradient-to-r from-sky-500 to-emerald-500 transition-all duration-500" style={{ width: `${loadingProgress}%` }} />
              </div>
              <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
                <span>{LOADING_STEPS[loadingStepIndex] || 'Preparing insights...'}</span>
                <span>{loadingProgress}%</span>
              </div>
              <div className="mt-6 space-y-2">
                {LOADING_STEPS.map((step, index) => {
                  const isComplete = index < loadingStepIndex;
                  const isActive = index === loadingStepIndex;
                  return (
                    <div key={step} className={`flex items-center gap-3 rounded-2xl border px-3 py-2 text-sm ${isComplete ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : isActive ? 'border-sky-200 bg-sky-50 text-sky-700' : 'border-slate-200 bg-slate-50 text-slate-500'}`}>
                      <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${isComplete ? 'bg-emerald-600 text-white' : isActive ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                        {isComplete ? '✓' : index + 1}
                      </span>
                      {step}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : null}

        {!isDashboard ? (
          <form onSubmit={handleUpload} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
            <div className="grid gap-6 md:grid-cols-[1.1fr_0.9fr]">
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Customer</label>
                  <select value={customerId} onChange={(event) => setCustomerId(event.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm focus:border-sky-500 focus:outline-none">
                    {CUSTOMERS.map((customer) => (
                      <option key={customer.id} value={customer.id}>{customer.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Transcript</label>
                  <textarea value={transcript} onChange={(event) => setTranscript(event.target.value)} rows={10} className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm shadow-sm focus:border-sky-500 focus:outline-none" placeholder="Paste the meeting transcript here" />
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                <h2 className="text-lg font-semibold">Ready to analyze</h2>
                <p className="mt-2 text-sm text-slate-600">The workflow posts your transcript to the backend, then loads the generated recommendation summary for the selected customer.</p>
                <button type="submit" disabled={isLoading} className="mt-6 inline-flex items-center justify-center rounded-2xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white transition duration-200 hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-sky-300">
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <Spinner className="h-4 w-4" />
                      Uploading…
                    </span>
                  ) : 'Submit'}
                </button>
                {error ? <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
              </div>
            </div>
          </form>
        ) : (
          <div className="space-y-6">
            {toast ? (
              <div className={`rounded-2xl border px-4 py-3 text-sm shadow-sm transition duration-200 ${toast.type === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-rose-200 bg-rose-50 text-rose-700'}`}>
                {toast.message}
              </div>
            ) : null}

            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">AI Workflow</p>
                  <h2 className="text-xl font-semibold">Execution Timeline</h2>
                </div>
                <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-medium text-emerald-700">
                  {recommendations.length > 0 ? 'Completed successfully' : 'Pending execution'}
                </div>
              </div>
              <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {AGENT_STEPS.map((agent, index) => (
                  <div key={agent} className={`rounded-2xl border px-4 py-3 text-sm transition duration-200 ${recommendations.length > 0 ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                    <div className="flex items-center gap-2 font-semibold">
                      <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${recommendations.length > 0 ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                        {recommendations.length > 0 ? '✓' : index + 1}
                      </span>
                      {agent}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {statCards.map((card) => (
                <div key={card.label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70 transition duration-200 hover:-translate-y-0.5 hover:shadow-md">
                  <p className="text-sm text-slate-500">{card.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-800">{card.value}</p>
                </div>
              ))}
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">Customer Summary</p>
                  <h2 className="text-2xl font-semibold">{summary?.company || selectedCustomer?.name || 'Customer profile'}</h2>
                </div>
                {healthTone ? (
                  <span className={`rounded-full px-3 py-1 text-sm font-semibold ${healthTone.classes}`}>{healthTone.label}</span>
                ) : null}
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Health Score</p>
                      <p className="mt-1 text-3xl font-semibold">{summary?.healthScore ?? '—'} / 100</p>
                    </div>
                    <div className={`rounded-full px-3 py-1 text-sm font-semibold ${healthTone?.classes || 'bg-slate-100 text-slate-600'}`}>
                      {healthTone?.label || 'Pending'}
                    </div>
                  </div>
                  <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                    <div className={`h-full rounded-full transition-all duration-700 ${healthScore > 70 ? 'bg-emerald-500' : healthScore >= 40 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${healthPercent}%` }} />
                  </div>
                  <div className="mt-2 text-sm text-slate-500">Customer health is at {healthPercent}% of target readiness.</div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Renewal Countdown</p>
                    <p className="mt-2 text-2xl font-semibold">{summary?.renewalCountdown ?? '—'} days</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Support Tickets</p>
                    <p className="mt-2 text-2xl font-semibold">{summary?.supportTickets ?? '—'}</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                <p className="font-semibold text-slate-800">Session</p>
                <p className="mt-1 break-all">{sessionId || 'No active session'}</p>
              </div>
            </section>

            <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70 transition duration-200 hover:-translate-y-0.5 hover:shadow-md">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Risk Cards</h3>
                  <span className="text-sm text-slate-500">{risks.length} items</span>
                </div>
                <div className="mt-4 space-y-3">
                  {risks.length > 0 ? risks.map((risk, index) => {
                    const tone = getRiskTone(risk.severity || risk.level || risk.priority || 'Medium');
                    return (
                      <div key={`${risk.type || risk.name || index}`} className={`rounded-2xl border p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-sm ${tone.ring}`}>
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3">
                            <div className="rounded-2xl bg-white/80 p-2 text-lg">{tone.icon}</div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{risk.type || risk.name || 'Risk'}</p>
                              <p className="mt-2 text-sm text-slate-600">{risk.evidence || risk.details || 'No evidence provided.'}</p>
                            </div>
                          </div>
                          <span className={`rounded-full px-3 py-1 text-sm font-semibold ${tone.classes}`}>{tone.label}</span>
                        </div>
                      </div>
                    );
                  }) : (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-600">
                      No risk signals available yet. Upload a transcript to begin.
                    </div>
                  )}
                </div>
              </section>

              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70 transition duration-200 hover:-translate-y-0.5 hover:shadow-md">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Recommendations</h3>
                  <span className="text-sm text-slate-500">{recommendations.length} items</span>
                </div>
                <div className="mt-4 space-y-4">
                  {recommendations.length > 0 ? recommendations.map((item, index) => {
                    const explanation = explanations[index] || {};
                    const evidenceGroups = buildEvidenceGroups(explanation.evidence || []);
                    return (
                      <div key={`${item.id || index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 transition duration-200 hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-800">{item.action || 'Recommendation'}</p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              <span className={`rounded-full px-3 py-1 text-sm font-semibold ${getPriorityTone(item.priority)}`}>{item.priority || 'Unknown'}</span>
                              <span className="rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700">Confidence {Math.round(Number(item.confidence || 0) * 100)}%</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <label className="flex items-center gap-2 text-sm text-slate-600">
                              <input type="checkbox" className="h-4 w-4 rounded border-slate-300" />
                              Select
                            </label>
                            <button type="button" onClick={() => handleApprove(item.id)} disabled={approvingId === item.id} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:border-sky-400 hover:text-sky-700 disabled:cursor-not-allowed disabled:opacity-60">
                              {approvingId === item.id ? <><Spinner className="h-4 w-4" /> Approving…</> : 'Approve'}
                            </button>
                          </div>
                        </div>

                        <details className="group mt-4 rounded-2xl border border-slate-200 bg-white p-3">
                          <summary className="cursor-pointer list-none text-sm font-semibold text-slate-700">View rationale & evidence</summary>
                          <div className="mt-3 space-y-3 border-t border-slate-200 pt-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-800">Reason</p>
                              <p className="mt-1 text-sm text-slate-600">{explanation.reason || 'No rationale provided.'}</p>
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">Confidence</p>
                              <p className="mt-1 text-sm text-slate-600">{explanation.confidence ?? item.confidence ?? '—'}</p>
                            </div>
                            <div className="space-y-3">
                              {evidenceGroups.length > 0 ? evidenceGroups.map((group) => (
                                <div key={group.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                                  <p className="text-sm font-semibold text-slate-700">{group.label}</p>
                                  <ul className="mt-2 space-y-1 pl-4 text-sm text-slate-600">
                                    {group.items.map((entry, entryIndex) => (
                                      <li key={`${group.label}-${entryIndex}`} className="list-disc">{entry}</li>
                                    ))}
                                  </ul>
                                </div>
                              )) : (
                                <p className="text-sm text-slate-600">No evidence available.</p>
                              )}
                            </div>
                          </div>
                        </details>
                      </div>
                    );
                  }) : (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-600">
                      No recommendations available. Upload a transcript to begin.
                    </div>
                  )}
                </div>
              </section>
            </div>

            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:shadow-md">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold">Approval History</h3>
                  <p className="text-sm text-slate-500">Newest approvals appear first.</p>
                </div>
                <span className="text-sm text-slate-500">{historyItems.length} entries</span>
              </div>
              {historyLoading ? (
                <div className="mt-4 flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                  <Spinner className="h-4 w-4" />
                  Loading history…
                </div>
              ) : null}
              {historyError ? (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{historyError}</div>
              ) : null}
              <div className="mt-4 overflow-x-auto">
                {sortedHistoryItems.length > 0 ? (
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="sticky top-0 bg-white">
                      <tr className="text-left text-slate-600">
                        <th className="pb-3 font-semibold">Action</th>
                        <th className="pb-3 font-semibold">Priority</th>
                        <th className="pb-3 font-semibold">Confidence</th>
                        <th className="pb-3 font-semibold">Approved At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sortedHistoryItems.map((item, index) => (
                        <tr key={`${item.action || index}`} className="transition duration-200 hover:bg-slate-50">
                          <td className="py-3 pr-4 font-medium text-slate-800">
                            <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                              <span>✓</span> Approved
                            </span>
                            <div className="mt-2">{item.action || 'Approved recommendation'}</div>
                          </td>
                          <td className="py-3 pr-4 text-slate-600">{item.priority || 'Unknown'}</td>
                          <td className="py-3 pr-4 text-slate-600">{item.confidence ?? '—'}</td>
                          <td className="py-3 text-slate-600">{formatTimestamp(item.approved_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-600">
                    No approval history found yet.
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
