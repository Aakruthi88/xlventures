import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip as ReTooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  LineChart, Line,
} from 'recharts';
import customersCsv from '../../data/customers.csv?raw';
import usageCsv from '../../data/usage.csv?raw';
import crmData from '../../data/crm.json';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Customers', path: '/customers' },
  { label: 'History', path: '/history' },
  { label: 'Analytics', path: '/analytics' },
];

const ANALYSIS_STEPS = ['Customer Profile', 'CRM', 'Product Documents', 'Sentiment Analysis', 'Risk Detection', 'Opportunity Detection'];

function parseCustomers(csvText, usageText, crmEntries) {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map((header) => header.trim());
  const usageRows = usageText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const usageHeaders = usageRows[0]?.split(',').map((header) => header.trim()) || [];
  const usageMap = Object.fromEntries(
    usageRows.slice(1).map((line) => {
      const values = line.split(',').map((value) => value.trim());
      const row = Object.fromEntries(usageHeaders.map((header, index) => [header, values[index] || '']));
      return [row.Company, row];
    })
  );
  const crmMap = Object.fromEntries((crmEntries || []).map((entry) => [entry.company, entry]));

  return lines.slice(1).map((line) => {
    const values = line.split(',').map((value) => value.trim());
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] || '']));

    const renewalDate = new Date(row.RenewalDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const daysToRenewal = Math.round((renewalDate - today) / 86400000);

    const usageRow = usageMap[row.Company] || {};
    const crmRow = crmMap[row.Company] || {};

    return {
      id: row.CustomerID,
      name: row.Company,
      plan: row.Plan,
      industry: row.Industry,
      renewalDate: row.RenewalDate,
      healthScore: Number(row.HealthScore) || 0,
      daysToRenewal,
      licensedUsers: Number(usageRow.LicensedUsers) || 0,
      activeUsers: Number(usageRow.ActiveUsers) || 0,
      openSupportTickets: Number(crmRow.support_tickets_open) || 0,
      recentMeetingDate: crmRow.last_meeting_date || '',
      owner: crmRow.customer_owner || '',
    };
  });
}

function formatRenewalCountdown(days) {
  if (days < 0) return 'Expired';
  if (days === 0) return 'Today';
  if (days === 1) return '1 day';
  return `${days} days`;
}

function getStatusTone(score) {
  if (score >= 60) {
    return { label: 'Healthy', classes: 'bg-emerald-100 text-emerald-700' };
  }

  if (score < 40) {
    return { label: 'At Risk', classes: 'bg-rose-100 text-rose-700' };
  }

  return { label: 'Watch', classes: 'bg-amber-100 text-amber-700' };
}

function buildApiUrl(path) {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
  const normalizedBase = baseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function StatCard({ label, value, accent, sub }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      {sub ? <p className="mt-1 text-xs text-slate-400">{sub}</p> : null}
    </div>
  );
}

function Spinner({ className = 'h-5 w-5' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Zm0 0a8 8 0 0 0 8 8v4c-6.627 0-12-5.373-12-12h4Z" />
    </svg>
  );
}

function CustomerTable({ customers, navigate }) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('healthScore');
  const [sortDir, setSortDir] = useState('asc');

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return customers
      .filter((c) => !q || c.name.toLowerCase().includes(q) || c.industry.toLowerCase().includes(q) || c.plan.toLowerCase().includes(q))
      .sort((a, b) => {
        let av = a[sortKey], bv = b[sortKey];
        if (typeof av === 'string') av = av.toLowerCase(), bv = bv.toLowerCase();
        if (av < bv) return sortDir === 'asc' ? -1 : 1;
        if (av > bv) return sortDir === 'asc' ? 1 : -1;
        return 0;
      });
  }, [customers, search, sortKey, sortDir]);

  function SortIcon({ col }) {
    if (sortKey !== col) return <span className="ml-1 text-slate-300"></span>;
    return <span className="ml-1 text-sky-500">{sortDir === 'asc' ? '' : ''}</span>;
  }

  const thCls = 'px-4 py-3 font-semibold cursor-pointer select-none hover:text-slate-800 whitespace-nowrap';

  return (
    <div className="space-y-4">
      <input
        type="search"
        placeholder="Search by name, industry or plan..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm rounded-2xl border border-slate-200 px-4 py-2 text-sm shadow-sm focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
      />
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm shadow-slate-200/70">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className={thCls} onClick={() => toggleSort('name')}>Company<SortIcon col="name" /></th>
                <th className={thCls} onClick={() => toggleSort('plan')}>Plan<SortIcon col="plan" /></th>
                <th className={thCls} onClick={() => toggleSort('industry')}>Industry<SortIcon col="industry" /></th>
                <th className={thCls} onClick={() => toggleSort('healthScore')}>Health<SortIcon col="healthScore" /></th>
                <th className={thCls} onClick={() => toggleSort('daysToRenewal')}>Renewal<SortIcon col="daysToRenewal" /></th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {filtered.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-400">No customers match your search.</td></tr>
              ) : filtered.map((customer) => {
                const tone = getStatusTone(customer.healthScore);
                return (
                  <tr key={customer.id} className="hover:bg-slate-50">
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-800">{customer.name}</div>
                      <div className="mt-0.5 text-xs text-slate-400">{customer.id}</div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{customer.plan}</td>
                    <td className="px-4 py-4 text-slate-600">{customer.industry}</td>
                    <td className="px-4 py-4">
                      <span className={`font-semibold ${customer.healthScore >= 70 ? 'text-emerald-600' : customer.healthScore >= 40 ? 'text-amber-500' : 'text-rose-600'}`}>{customer.healthScore}</span>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{formatRenewalCountdown(customer.daysToRenewal)}</td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${tone.classes}`}>{tone.label}</span>
                    </td>
                    <td className="px-4 py-4">
                      <button
                        type="button"
                        onClick={() => navigate(`/customer/${customer.id}`)}
                        className="inline-flex items-center rounded-full bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700"
                      >
                        Open 
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="border-t border-slate-100 bg-slate-50 px-4 py-2.5 text-xs text-slate-400">
          {filtered.length} of {customers.length} customers
        </div>
      </div>
    </div>
  );
}

//
// Phase 14 Analysis Results
//

function healthScoreColor(score) {
  if (score >= 70) return { bar: 'bg-emerald-500', badge: 'bg-emerald-100 text-emerald-700', border: 'border-emerald-300' };
  if (score >= 40) return { bar: 'bg-amber-400', badge: 'bg-amber-100 text-amber-700', border: 'border-amber-300' };
  return { bar: 'bg-rose-500', badge: 'bg-rose-100 text-rose-700', border: 'border-rose-300' };
}

function riskBorderColor(severity) {
  if (!severity) return 'border-slate-200';
  const s = severity.toLowerCase();
  if (s === 'high') return 'border-rose-400';
  if (s === 'medium') return 'border-amber-400';
  return 'border-emerald-400';
}

function riskBadgeColor(severity) {
  if (!severity) return 'bg-slate-100 text-slate-600';
  const s = severity.toLowerCase();
  if (s === 'high') return 'bg-rose-100 text-rose-700';
  if (s === 'medium') return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
}

function priorityBadgeColor(priority) {
  if (!priority) return 'bg-slate-100 text-slate-600';
  const p = priority.toLowerCase();
  if (p === 'high') return 'bg-rose-100 text-rose-700';
  if (p === 'medium') return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
}

// Priority sort order: High  Medium  Low  everything else
const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };
function prioritySortValue(priority) {
  return PRIORITY_ORDER[(priority || '').toLowerCase()] ?? 99;
}

// Normalise an evidence item to a plain string.
// The new agentic backend returns evidence as [{source, data}] objects;
// the old format was plain strings. Both are handled here.
function evidenceToString(item) {
  if (!item) return '';
  if (typeof item === 'string') return item;
  if (typeof item === 'object') {
    // {source, data} shape from the new ExplanationAgent
    const parts = [];
    if (item.source) parts.push(String(item.source));
    if (item.data)   parts.push(String(item.data));
    return parts.join(': ');
  }
  return String(item);
}

// Classify a single evidence string into a source bucket using keyword heuristics
function classifyEvidence(item) {
  const text = evidenceToString(item);
  if (!text) return null;
  const t = text.toLowerCase();
  if (t.includes('transcript') || t.includes('meeting') || t.includes('call') || t.includes('said') || t.includes('mentioned') || t.includes('customer stated')) return 'Meeting Transcript';
  if (t.includes('crm') || t.includes('owner') || t.includes('champion') || t.includes('last meeting') || t.includes('account')) return 'CRM';
  if (t.includes('ticket') || t.includes('support') || t.includes('issue') || t.includes('open')) return 'Support Tickets';
  if (t.includes('playbook') || t.includes('guide') || t.includes('sop') || t.includes('knowledge') || t.includes('training') || t.includes('integration') || t.includes('onboarding') || t.includes('faq') || t.includes('renewal playbook') || t.includes('per ') || t.includes('recommends')) return 'Knowledge Base';
  return null; // ungrouped
}

// Group evidence items into source buckets; uncategorised items go into a general list.
// Each item is normalised to a string before classification and storage.
function groupEvidence(evidenceList) {
  const buckets = {};
  const ungrouped = [];
  for (const item of (evidenceList || [])) {
    const str = evidenceToString(item);
    if (!str) continue;
    const bucket = classifyEvidence(str);
    if (bucket) {
      if (!buckets[bucket]) buckets[bucket] = [];
      buckets[bucket].push(str);
    } else {
      ungrouped.push(str);
    }
  }
  return { buckets, ungrouped };
}

// Source icon mapping
const SOURCE_ICONS = {
  'Meeting Transcript': 'Transcript',
  'CRM': 'CRM',
  'Knowledge Base': 'Knowledge Base',
  'Support Tickets': 'Support',
};

//
// Toast notification (auto-dismisses after 3 s)
//
function Toast({ toasts }) {
  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="pointer-events-none fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold shadow-lg transition-all
            ${t.type === 'success' ? 'bg-emerald-600 text-white' : t.type === 'error' ? 'bg-rose-600 text-white' : 'bg-slate-800 text-white'}`}
        >
          <span aria-hidden="true">{t.type === 'success' ? '' : t.type === 'error' ? '-' : ''}</span>
          {t.message}
        </div>
      ))}
    </div>
  );
}

//
// Phase 14E+F  Expandable Recommendation Card with Human Review
//
function RecommendationCard({ rec, idx, explanation, sessionId, onToast }) {
  // Expand / collapse
  const [expanded, setExpanded] = useState(false);

  // Human-review state: null | 'approved' | 'rejected'
  const [reviewStatus, setReviewStatus] = useState(null);

  // Edit mode
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(rec.action);
  const [savedText, setSavedText] = useState(rec.action);

  // Async loading flags
  const [isApproving, setIsApproving] = useState(false);

  const isDone = reviewStatus !== null; // buttons disabled once a decision is made

  // Approve 
  async function handleApprove() {
    if (isDone || isApproving) return;
    setIsApproving(true);
    try {
      const res = await fetch(buildApiUrl('/approve_action'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, recommendation_id: rec.id, approved: true }),
      });
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      setReviewStatus('approved');
      onToast({ type: 'success', message: `Approved & Executed: ${savedText.slice(0, 60)}${savedText.length > 60 ? '...' : ''}` });
    } catch (err) {
      onToast({ type: 'error', message: `Approval/Execution failed: ${err.message}` });
    } finally {
      setIsApproving(false);
    }
  }

  // Reject 
  async function handleReject() {
    if (isDone) return;
    setReviewStatus('rejected');
    onToast({ type: 'error', message: `Rejected: ${savedText.slice(0, 60)}${savedText.length > 60 ? '...' : ''}` });
    try {
      await fetch(buildApiUrl('/approve_action'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, recommendation_id: rec.id, approved: false }),
      });
    } catch {
      // Non-critical
    }
  }

  // Edit 
  async function handleEditSave() {
    const trimmed = editedText.trim();
    if (!trimmed) return;
    setSavedText(trimmed);
    setIsEditing(false);
    onToast({ type: 'success', message: 'Recommendation updated.' });
    try {
      await fetch(buildApiUrl('/approve'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          recommendation_id: rec.id,
          action: 'edit',
          edited_text: trimmed,
        }),
      });
    } catch {
      // Non-critical: local edit already saved
    }
  }

  function handleEditCancel() {
    setEditedText(savedText);
    setIsEditing(false);
  }

  // Explainability data 
  const hasExplanation = !!explanation;
  const { buckets, ungrouped } = hasExplanation && explanation.evidence?.length
    ? groupEvidence(explanation.evidence)
    : { buckets: {}, ungrouped: [] };
  const bucketKeys = Object.keys(buckets);
  const hasGroupedEvidence = bucketKeys.length > 0 || ungrouped.length > 0;

  // Border colour driven by review status 
  const cardBorder =
    reviewStatus === 'approved' ? 'border-emerald-300' :
    reviewStatus === 'rejected' ? 'border-rose-300' :
    expanded ? 'border-sky-200' :
    'border-slate-200';

  return (
    <div className={`rounded-3xl border bg-white shadow-sm shadow-slate-200/70 transition-all ${cardBorder}`}>

      {/*  Collapsed / header row  */}
      <div className="px-6 py-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">

          {/* Left: index + action text (or edit field) */}
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold
              ${reviewStatus === 'approved' ? 'bg-emerald-600 text-white' : reviewStatus === 'rejected' ? 'bg-rose-500 text-white' : 'bg-slate-900 text-white'}`}>
              {reviewStatus === 'approved' ? '' : reviewStatus === 'rejected' ? '-' : idx + 1}
            </span>

            {isEditing ? (
              <div className="flex-1 space-y-2">
                <textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={3}
                  className="w-full rounded-2xl border border-sky-300 px-3 py-2 text-sm text-slate-800 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-400"
                  aria-label="Edit recommendation text"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleEditSave}
                    className="rounded-full bg-sky-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-sky-700"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={handleEditCancel}
                    className="rounded-full border border-slate-200 bg-slate-50 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p className={`font-semibold leading-snug ${isDone ? 'text-slate-500' : 'text-slate-800'}`}>
                {savedText}
              </p>
            )}
          </div>

          {/* Right: badges + chevron */}
          {!isEditing && (
            <div className="flex shrink-0 flex-wrap items-center gap-2 ml-11 sm:ml-0">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityBadgeColor(rec.priority)}`}>
                {rec.priority || 'Normal'}
              </span>
              {rec.confidence != null ? (
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                  {Math.round(rec.confidence * 100)}%
                </span>
              ) : null}

              {/* Dynamic status badge */}
              {reviewStatus === 'approved' ? (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">Approved</span>
              ) : reviewStatus === 'rejected' ? (
                <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">Rejected</span>
              ) : (
                <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-700">Pending Review</span>
              )}

              {/* Expand / collapse toggle */}
              <button
                type="button"
                onClick={() => setExpanded((p) => !p)}
                aria-expanded={expanded}
                aria-label={expanded ? 'Collapse details' : 'Expand details'}
                className="ml-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200"
              >
                <span
                  className={`inline-block transition-transform duration-200 text-xs ${expanded ? 'rotate-180' : ''}`}
                  aria-hidden="true"
                >-</span>
              </button>
            </div>
          )}
        </div>

        {/*  Human Review action buttons (shown while not editing and not done)  */}
        {!isEditing && (
          <div className="mt-4 flex flex-wrap items-center gap-2 ml-11">
            {/* Approve */}
            <button
              type="button"
              onClick={handleApprove}
              disabled={isDone || isApproving}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition
                ${reviewStatus === 'approved'
                  ? 'cursor-default bg-emerald-600 text-white opacity-80'
                  : isDone
                  ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700 active:scale-95'}`}
              aria-label="Approve recommendation"
            >
              {isApproving ? <Spinner className="h-3 w-3" /> : null}
              {reviewStatus === 'approved' ? 'Approved' : 'Approve'}
            </button>

            {/* Reject */}
            <button
              type="button"
              onClick={handleReject}
              disabled={isDone}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition
                ${reviewStatus === 'rejected'
                  ? 'cursor-default bg-rose-600 text-white opacity-80'
                  : isDone
                  ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                  : 'border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 active:scale-95'}`}
              aria-label="Reject recommendation"
            >
              <span aria-hidden="true">-</span>
              {reviewStatus === 'rejected' ? 'Rejected' : 'Reject'}
            </button>

            {/* Edit */}
            <button
              type="button"
              onClick={() => { if (!isDone) setIsEditing(true); }}
              disabled={isDone}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition
                ${isDone
                  ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                  : 'border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 active:scale-95'}`}
              aria-label="Edit recommendation"
            >
              
              Edit
            </button>
          </div>
        )}
      </div>

      {/*  Explainability panel (expanded)  */}
      {expanded && (
        <div className="border-t border-slate-100 px-6 pb-6 pt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-3">
            Explainability
          </p>

          {hasExplanation ? (
            <>
              {/* Reason + confidence */}
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                <p className="text-sm leading-relaxed text-slate-700 max-w-2xl">{explanation.reason || explanation.reasoning}</p>
                {explanation.confidence != null ? (
                  <span className="shrink-0 mt-1 sm:mt-0 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 self-start">
                    {Math.round(explanation.confidence * 100)}% confidence
                  </span>
                ) : null}
              </div>

              {/* Evidence */}
              {hasGroupedEvidence ? (
                <div className="mt-4 space-y-4">
                  {bucketKeys.map((bucket) => (
                    <div key={bucket}>
                      <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-1.5">
                        <span aria-hidden="true">{SOURCE_ICONS[bucket] || ''}</span>
                        {bucket}
                      </p>
                      <ul className="space-y-1.5 pl-5">
                        {buckets[bucket].map((fact, fi) => (
                          <li key={fi} className="flex items-start gap-2 text-sm text-slate-600">
                            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400" aria-hidden="true" />
                            {fact}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                  {ungrouped.length > 0 ? (
                    <div>
                      <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-1.5">
                        
                        Supporting Evidence
                      </p>
                      <ul className="space-y-1.5 pl-5">
                        {ungrouped.map((fact, fi) => (
                          <li key={fi} className="flex items-start gap-2 text-sm text-slate-600">
                            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400" aria-hidden="true" />
                            {fact}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-400 italic">No supporting evidence returned.</p>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-400 italic">No explainability data returned for this recommendation.</p>
          )}
        </div>
      )}
    </div>
  );
}

function sourceName(doc) {
  // Prefer an explicit 'source' field; fall back to 'id', 'title', or a truncated content preview.
  if (doc.source) return String(doc.source);
  if (doc.id) return String(doc.id);
  if (doc.title) return String(doc.title);
  if (doc.metadata?.source) return String(doc.metadata.source);
  if (doc.content) return String(doc.content).slice(0, 60) + '...';
  return 'Knowledge Document';
}

function AnalysisResults({ analysisResult, analysisCustomerId, activeSessionId, customers, navigate }) {
  const cs = analysisResult?.customer_summary || {};
  const risks = analysisResult?.risks?.risks || [];
  const retrievedDocs = analysisResult?.knowledge?.retrieved_docs || [];
  const recommendations = analysisResult?.recommendations?.recommendations || [];
  const explanations = analysisResult?.explanations?.explanations || analysisResult?.recommendations?.explanations || [];
  const customerName = customers.find((c) => c.id === analysisCustomerId)?.name || cs.company || 'Customer';

  const healthScore = cs.health_score ?? null;
  const healthColors = healthScore !== null ? healthScoreColor(healthScore) : null;
  const daysToRenewal = cs.days_to_renewal ?? null;
  const dashboardUsage = cs.dashboard_usage_pct ?? null;
  const openTickets = cs.open_support_tickets ?? null;

  // Determine whether any real analysis data is present
  const hasAnalysisData = analysisResult !== null && (
    healthScore !== null || risks.length > 0 || recommendations.length > 0
  );

  // Build a map from recommendation_id -> explanation for the explainability section.
  // Defensively filter out any null/undefined entries or entries without a recommendation_id
  // to prevent crashes when the backend returns unexpected shapes.
  const explainMap = Object.fromEntries(
    (explanations || [])
      .filter((e) => e && typeof e === 'object' && e.recommendation_id)
      .map((e) => [e.recommendation_id, e])
  );

  // Toast queue 
  const [toasts, setToasts] = useState([]);

  function pushToast({ type, message }) {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }

  const [trace, setTrace] = useState([]);
  useEffect(() => {
    if (!activeSessionId) return;
    async function fetchTrace() {
      try {
        const res = await fetch(buildApiUrl(`/agent_trace/${activeSessionId}`));
        if (res.ok) {
          const data = await res.json();
          setTrace(data.trace || []);
        }
      } catch (err) {
        console.error('Error fetching trace:', err);
      }
    }
    fetchTrace();
  }, [activeSessionId]);

  const timelineSteps = useMemo(() => {
    const agents = [
      { id: 'planner_agent', name: 'Planner Agent' },
      { id: 'customer_agent', name: 'Customer Agent' },
      { id: 'knowledge_agent', name: 'Knowledge Agent' },
      { id: 'sentiment_agent', name: 'Sentiment Agent' },
      { id: 'risk_agent', name: 'Risk Agent' },
      { id: 'opportunity_agent', name: 'Opportunity Agent' },
      { id: 'recommendation_agent', name: 'Decision Agent' },
    ];
    
    return agents.map(agent => {
      const entry = trace.find(t => t.agent_name === agent.id);
      let status = 'Pending';
      if (entry) {
        if (entry.status === 'completed') status = 'Completed';
        if (entry.status === 'running') status = 'Running';
        if (entry.status === 'failed') status = 'Failed';
      }
      return { name: agent.name, status };
    });
  }, [trace]);

  return (
    <div className="space-y-6">
      {/* Global toast stack */}
      <Toast toasts={toasts} />

      {/*  Header  */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">Analysis Results</p>
            <h3 className="mt-1 text-2xl font-semibold">{customerName}</h3>
            {activeSessionId ? <p className="mt-1 text-xs text-slate-400 break-all">Session: {activeSessionId}</p> : null}
          </div>
          <button
            type="button"
            onClick={() => navigate(`/customer/${analysisCustomerId || ''}`)}
            className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
          >
             Back to customer
          </button>
        </div>
      </div>

      {/* Agent Execution Timeline */}
      {activeSessionId && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Agent Execution Timeline</p>
          <div className="flex flex-col gap-2">
            {timelineSteps.map((step, i) => {
              const isCompleted = step.status === 'Completed';
              const isRunning = step.status === 'Running';
              const isFailed = step.status === 'Failed';
              return (
                <div
                  key={step.name}
                  className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition-all duration-500 ${
                    isCompleted ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                    : isRunning ? 'border-sky-200 bg-sky-50 text-sky-700'
                    : isFailed ? 'border-rose-200 bg-rose-50 text-rose-700'
                    : 'border-slate-200 bg-slate-50 text-slate-500'
                  }`}
                >
                  <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                    isCompleted ? 'bg-emerald-600 text-white'
                    : isRunning ? 'bg-sky-600 text-white'
                    : isFailed ? 'bg-rose-600 text-white'
                    : 'bg-slate-200 text-slate-500'
                  }`}>
                    {isCompleted ? '✓' : isFailed ? '✗' : i + 1}
                  </span>
                  <span className="flex-1 font-medium">{step.name}</span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    isCompleted ? 'bg-emerald-100 text-emerald-700'
                    : isRunning ? 'bg-sky-100 text-sky-700 animate-pulse'
                    : isFailed ? 'bg-rose-100 text-rose-700'
                    : 'bg-slate-100 text-slate-500'
                  }`}>
                    {step.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/*  No analysis guard  */}
      {!hasAnalysisData ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm shadow-slate-200/70">
          <p className="text-2xl mb-2"></p>
          <p className="font-semibold text-slate-700">No analysis available</p>
          <p className="mt-2 text-sm text-slate-500">Upload or paste a meeting transcript to generate AI recommendations.</p>
          <button
            type="button"
            onClick={() => navigate(`/customer/${analysisCustomerId || ''}`)}
            className="mt-5 inline-flex items-center rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Analyze Meeting 
          </button>
        </div>
      ) : (
        <>
      <section>
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Customer Summary</p>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {/* Health Score */}
          <div className={`rounded-3xl border bg-white p-5 shadow-sm shadow-slate-200/70 ${healthColors ? healthColors.border : 'border-slate-200'}`}>
            <p className="text-sm text-slate-500">Health Score</p>
            {healthScore !== null ? (
              <>
                <p className={`mt-2 text-3xl font-semibold tracking-tight ${healthScore >= 70 ? 'text-emerald-600' : healthScore >= 40 ? 'text-amber-500' : 'text-rose-600'}`}>
                  {healthScore}
                </p>
                <div className="mt-3 h-2 w-full rounded-full bg-slate-100">
                  <div
                    className={`h-2 rounded-full transition-all ${healthColors.bar}`}
                    style={{ width: `${Math.min(100, healthScore)}%` }}
                    role="progressbar"
                    aria-valuenow={healthScore}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  />
                </div>
                <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${healthColors.badge}`}>
                  {healthScore >= 70 ? 'Healthy' : healthScore >= 40 ? 'At Watch' : 'At Risk'}
                </span>
              </>
            ) : (
              <p className="mt-2 text-xl text-slate-400"></p>
            )}
          </div>

          {/* Renewal Countdown */}
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70">
            <p className="text-sm text-slate-500">Renewal Countdown</p>
            {daysToRenewal !== null ? (
              <>
                <p className={`mt-2 text-3xl font-semibold tracking-tight ${daysToRenewal <= 30 ? 'text-rose-600' : daysToRenewal <= 90 ? 'text-amber-500' : 'text-slate-800'}`}>
                  {daysToRenewal < 0 ? 'Expired' : daysToRenewal === 0 ? 'Today' : `${daysToRenewal}d`}
                </p>
                <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${daysToRenewal <= 30 ? 'bg-rose-100 text-rose-700' : daysToRenewal <= 90 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>
                  {daysToRenewal <= 30 ? 'Urgent' : daysToRenewal <= 90 ? 'Upcoming' : 'On track'}
                </span>
              </>
            ) : (
              <p className="mt-2 text-xl text-slate-400"></p>
            )}
          </div>

          {/* Product Adoption */}
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70">
            <p className="text-sm text-slate-500">Product Adoption</p>
            {dashboardUsage !== null ? (
              <>
                <p className={`mt-2 text-3xl font-semibold tracking-tight ${dashboardUsage >= 70 ? 'text-emerald-600' : dashboardUsage >= 40 ? 'text-amber-500' : 'text-rose-600'}`}>
                  {dashboardUsage}%
                </p>
                <div className="mt-3 h-2 w-full rounded-full bg-slate-100">
                  <div
                    className={`h-2 rounded-full transition-all ${dashboardUsage >= 70 ? 'bg-emerald-500' : dashboardUsage >= 40 ? 'bg-amber-400' : 'bg-rose-500'}`}
                    style={{ width: `${Math.min(100, dashboardUsage)}%` }}
                    role="progressbar"
                    aria-valuenow={dashboardUsage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  />
                </div>
                <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${dashboardUsage >= 70 ? 'bg-emerald-100 text-emerald-700' : dashboardUsage >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-rose-100 text-rose-700'}`}>
                  {dashboardUsage >= 70 ? 'Strong' : dashboardUsage >= 40 ? 'Moderate' : 'Low'}
                </span>
              </>
            ) : (
              <p className="mt-2 text-xl text-slate-400"></p>
            )}
          </div>

          {/* Open Support Tickets */}
          <div className={`rounded-3xl border bg-white p-5 shadow-sm shadow-slate-200/70 ${openTickets !== null && openTickets > 5 ? 'border-rose-300' : openTickets !== null && openTickets > 2 ? 'border-amber-300' : 'border-slate-200'}`}>
            <p className="text-sm text-slate-500">Open Support Tickets</p>
            {openTickets !== null ? (
              <>
                <p className={`mt-2 text-3xl font-semibold tracking-tight ${openTickets > 5 ? 'text-rose-600' : openTickets > 2 ? 'text-amber-500' : 'text-emerald-600'}`}>
                  {openTickets}
                </p>
                <span className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold ${openTickets > 5 ? 'bg-rose-100 text-rose-700' : openTickets > 2 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                  {openTickets > 5 ? 'High Volume' : openTickets > 2 ? 'Moderate' : 'Low'}
                </span>
              </>
            ) : (
              <p className="mt-2 text-xl text-slate-400"></p>
            )}
          </div>
        </div>
      </section>

      {/* 
          Section 2  Risk Analysis
       */}
      <section>
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Risk Analysis</p>
        {risks.length === 0 ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm shadow-slate-200/70">
            No risks detected for this customer.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {risks.map((risk, idx) => (
              <div
                key={idx}
                className={`rounded-3xl border-2 bg-white p-5 shadow-sm shadow-slate-200/70 ${riskBorderColor(risk.severity)}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    
                    <p className="font-semibold text-slate-800">{risk.type || 'Risk'}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${riskBadgeColor(risk.severity)}`}>
                    {risk.severity || 'Unknown'}
                  </span>
                </div>
                {risk.evidence ? (
                  <p className="mt-3 text-sm leading-relaxed text-slate-600">{risk.evidence}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 
          Section 3  Knowledge Retrieved (RAG)
       */}
      <section>
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Knowledge Retrieved</p>
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
          <div className="flex items-center gap-2 mb-4">
            
            <h4 className="font-semibold text-slate-800">Retrieved from Knowledge Base</h4>
            <span className="ml-auto rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-700">RAG</span>
          </div>
          <p className="mb-4 text-sm text-slate-500">
            The following documents were retrieved via Retrieval-Augmented Generation to ground the AI analysis.
          </p>
          {retrievedDocs.length === 0 ? (
            <p className="text-sm text-slate-400">No documents were retrieved for this session.</p>
          ) : (
            <ul className="space-y-3">
              {retrievedDocs.map((doc, idx) => (
                <li key={idx} className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
                  
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-800 text-sm">{sourceName(doc)}</p>
                    {(doc.content || doc.snippet) ? (
                      <p className="mt-1 text-xs leading-relaxed text-slate-500 line-clamp-2">{String(doc.content || doc.snippet).slice(0, 160)}{String(doc.content || doc.snippet).length > 160 ? '...' : ''}</p>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* 
          Section 4  AI Recommendations  |  Section 5  Explainability
          Cards are sorted by priority (High  Medium  Low).
          Each card is expandable to reveal the Explainability panel.
       */}
      {recommendations.length > 0 ? (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
              Recommendations
            </p>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
              {recommendations.length} action{recommendations.length !== 1 ? 's' : ''} | click to expand
            </span>
          </div>
          <div className="space-y-3">
            {[...recommendations]
              .sort((a, b) => prioritySortValue(a.priority) - prioritySortValue(b.priority))
              .map((rec, idx) => (
                <RecommendationCard
                  key={rec.id || idx}
                  rec={rec}
                  idx={idx}
                  explanation={explainMap[rec.id] || null}
                  sessionId={activeSessionId}
                  onToast={pushToast}
                />
              ))}
          </div>
        </section>
      ) : null}
      </>
      )}
    </div>
  );
}

//
// Phase 14 Recommendation History
//

// Seeded demo rows used to demonstrate business impact when the SQLite store is empty.
// Outcomes are illustrative; they are never submitted to the backend.
const DEMO_HISTORY = [
  {
    customer_id: 'C001',
    action: 'Schedule analytics training session for ABC Manufacturing team',
    priority: 'High',
    confidence: 0.91,
    approved_at: '2026-06-01T10:15:00Z',
    outcome: 'Adoption Increased',
  },
  {
    customer_id: 'C001',
    action: 'Escalate SAP integration issues to engineering team with priority fix',
    priority: 'High',
    confidence: 0.88,
    approved_at: '2026-06-01T10:16:00Z',
    outcome: 'Issue Resolved',
  },
  {
    customer_id: 'C002',
    action: 'Initiate executive sponsor outreach before renewal deadline',
    priority: 'High',
    confidence: 0.85,
    approved_at: '2026-06-03T14:22:00Z',
    outcome: 'Renewed',
  },
  {
    customer_id: 'C003',
    action: 'Prepare competitive comparison document addressing alternatives',
    priority: 'Medium',
    confidence: 0.79,
    approved_at: '2026-06-05T09:00:00Z',
    outcome: 'Expanded License',
  },
  {
    customer_id: 'C004',
    action: 'Send onboarding refresher resources to GreenLeaf Retail team',
    priority: 'Medium',
    confidence: 0.76,
    approved_at: '2026-06-07T11:30:00Z',
    outcome: 'Adoption Increased',
  },
  {
    customer_id: 'C005',
    action: 'Schedule quarterly business review with Meridian Logistics leadership',
    priority: 'Low',
    confidence: 0.72,
    approved_at: '2026-06-10T16:45:00Z',
    outcome: 'Renewed',
  },
  {
    customer_id: 'C009',
    action: 'Trigger automated health-score alert and assign CSM follow-up',
    priority: 'High',
    confidence: 0.83,
    approved_at: '2026-06-12T08:00:00Z',
    outcome: 'Adoption Increased',
  },
  {
    customer_id: 'C010',
    action: 'Offer complimentary professional services session for BrightPath Education',
    priority: 'Medium',
    confidence: 0.74,
    approved_at: '2026-06-15T13:10:00Z',
    outcome: 'Expanded License',
  },
];

const OUTCOME_STYLES = {
  'Renewed':            'bg-emerald-100 text-emerald-700',
  'Adoption Increased': 'bg-sky-100 text-sky-700',
  'Expanded License':   'bg-violet-100 text-violet-700',
  'Issue Resolved':     'bg-amber-100 text-amber-700',
};

function outcomeBadge(outcome) {
  return OUTCOME_STYLES[outcome] || 'bg-slate-100 text-slate-600';
}

function formatApprovedAt(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return iso;
  }
}

function RecommendationHistory({ customers }) {
  const [liveRows, setLiveRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterCustomer, setFilterCustomer] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all'); // 'all' | 'approve' | 'reject' | 'edit'

  useEffect(() => {
    let cancelled = false;
    async function fetchAll() {
      setLoading(true);
      const results = [];
      await Promise.all(
        customers.map(async (c) => {
          try {
            const res = await fetch(buildApiUrl(`/history/${c.id}`));
            if (!res.ok) return;
            const rows = await res.json();
            if (!Array.isArray(rows)) return;
            rows.forEach((r) => results.push({ ...r, customer_id: c.id }));
          } catch { /* skip */ }
        })
      );
      if (!cancelled) { setLiveRows(results); setLoading(false); }
    }
    fetchAll();
    return () => { cancelled = true; };
  }, [customers]);

  const backendHasData = liveRows.length > 0;

  // Use live data or fall back to demo seed
  const baseRows = backendHasData ? liveRows : DEMO_HISTORY;

  // Enrich with customer name
  const enriched = baseRows.map((row) => ({
    ...row,
    customerName: customers.find((c) => c.id === row.customer_id)?.name || row.customer_id,
    // Normalise status: backend returns 'approve'/'reject'/'edit'; demo rows may have no status
    status: row.status || 'approve',
  }));

  // Sort newest first
  const sorted = [...enriched].sort((a, b) => {
    const ta = a.approved_at ? new Date(a.approved_at).getTime() : 0;
    const tb = b.approved_at ? new Date(b.approved_at).getTime() : 0;
    return tb - ta;
  });

  // Build customer filter options from actual data
  const customerOptions = Array.from(new Set(sorted.map((r) => r.customer_id)));

  // Apply filters
  const filtered = sorted.filter((r) => {
    if (filterCustomer !== 'all' && r.customer_id !== filterCustomer) return false;
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    return true;
  });

  // Summary counts (over full sorted set, not filtered)
  const approvedCount  = sorted.filter((r) => r.status === 'approve').length;
  const rejectedCount  = sorted.filter((r) => r.status === 'reject').length;
  const editedCount    = sorted.filter((r) => r.status === 'edit').length;

  // Status display helper
  function StatusBadge({ status }) {
    if (status === 'reject') return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
        <span aria-hidden="true">-</span> Rejected
      </span>
    );
    if (status === 'edit') return (
      <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-700">
         Edited
      </span>
    );
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
         Approved
      </span>
    );
  }

  return (
    <div className="space-y-6">
      {/*  Header  */}
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
        <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-sky-600">Recommendation History</p>
            <h3 className="mt-0.5 text-2xl font-semibold tracking-tight">Actions &amp; outcomes</h3>
            <p className="mt-1 text-sm text-slate-500">
              {backendHasData
                ? 'Live data from the recommendation_actions store.'
                : 'No live actions yet  showing seeded demo data.'}
            </p>
          </div>
          {!backendHasData && (
            <span className="shrink-0 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700 self-start">
              Demo Data
            </span>
          )}
        </div>

        {/* Summary counts */}
        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Total Actions</p>
            <p className="mt-1 text-2xl font-semibold text-slate-800">{sorted.length}</p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
            <p className="text-xs text-emerald-600">Approved</p>
            <p className="mt-1 text-2xl font-semibold text-emerald-700">{approvedCount}</p>
          </div>
          <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4">
            <p className="text-xs text-rose-600">Rejected</p>
            <p className="mt-1 text-2xl font-semibold text-rose-700">{rejectedCount}</p>
          </div>
          <div className="rounded-2xl border border-sky-100 bg-sky-50 p-4">
            <p className="text-xs text-sky-600">Edited</p>
            <p className="mt-1 text-2xl font-semibold text-sky-700">{editedCount}</p>
          </div>
        </div>
      </div>

      {/*  Filters  */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label htmlFor="hist-filter-customer" className="text-xs font-semibold text-slate-500">Customer</label>
          <select
            id="hist-filter-customer"
            value={filterCustomer}
            onChange={(e) => setFilterCustomer(e.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="all">All customers</option>
            {customerOptions.map((cid) => (
              <option key={cid} value={cid}>
                {customers.find((c) => c.id === cid)?.name || cid}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="hist-filter-status" className="text-xs font-semibold text-slate-500">Status</label>
          <select
            id="hist-filter-status"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="all">All</option>
            <option value="approve">Approved</option>
            <option value="reject">Rejected</option>
            <option value="edit">Edited</option>
          </select>
        </div>

        {(filterCustomer !== 'all' || filterStatus !== 'all') && (
          <button
            type="button"
            onClick={() => { setFilterCustomer('all'); setFilterStatus('all'); }}
            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-100"
          >
            Clear filters
          </button>
        )}
      </div>

      {/*  Table  */}
      {loading ? (
        <div className="flex items-center gap-3 rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
          <Spinner className="h-4 w-4 text-sky-500" />
          Loading history...
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
          No records match the current filters.
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm shadow-slate-200/70">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                <tr>
                  <th className="px-5 py-3">Customer</th>
                  <th className="px-5 py-3">Recommendation</th>
                  <th className="px-5 py-3">Priority</th>
                  <th className="px-5 py-3">Confidence</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Edited Text</th>
                  <th className="px-5 py-3">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filtered.map((row, i) => (
                  <tr key={i} className="transition hover:bg-slate-50">
                    <td className="whitespace-nowrap px-5 py-4">
                      <p className="font-semibold text-slate-800">{row.customerName}</p>
                      <p className="text-xs text-slate-400">{row.customer_id}</p>
                    </td>
                    <td className="px-5 py-4 max-w-xs">
                      <p className="text-slate-700 leading-snug">{row.action || ''}</p>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityBadgeColor(row.priority)}`}>
                        {row.priority || ''}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-700">
                      {row.confidence != null ? `${Math.round(row.confidence * 100)}%` : ''}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="px-5 py-4 max-w-xs">
                      {row.edited_text
                        ? <p className="text-xs text-slate-500 italic leading-snug">{row.edited_text}</p>
                        : <span className="text-slate-300"></span>}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-500">
                      {formatApprovedAt(row.approved_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-100 bg-slate-50 px-5 py-2.5 text-xs text-slate-400">
            Showing {filtered.length} of {sorted.length} record{sorted.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
}

//
// Phase 14 Analytics Dashboard
//

// Palette shared across all charts
const CHART_COLORS = {
  approved:  '#10b981', // emerald-500
  pending:   '#f59e0b', // amber-400
  rejected:  '#f43f5e', // rose-500
  high:      '#f43f5e',
  medium:    '#f59e0b',
  low:       '#10b981',
  healthy:   '#10b981',
  watch:     '#f59e0b',
  atRisk:    '#f43f5e',
  line:      '#0ea5e9', // sky-500
  bar1:      '#6366f1', // indigo-500
  bar2:      '#0ea5e9',
};

// Demo KPI values used when the backend has no real approval data
const DEMO_KPI = {
  generated:    42,
  approvalRate: 87,   // %
  avgConfidence:83,   // %
  saved:         9,
  renewals:      7,
};

// Demo chart data
const DEMO_STATUS_PIE = [
  { name: 'Approved', value: 34 },
  { name: 'Pending',  value: 5  },
  { name: 'Rejected', value: 3  },
];

const DEMO_RISK_BAR = [
  { label: 'High',   count: 12 },
  { label: 'Medium', count: 18 },
  { label: 'Low',    count: 15 },
];

const DEMO_HEALTH_BAR = [
  { label: '039 At Risk', count: 3 },
  { label: '4069 Watch',  count: 4 },
  { label: '70100 Healthy', count: 3 },
];

const DEMO_TREND_LINE = [
  { month: 'Jan', approved: 2 },
  { month: 'Feb', approved: 4 },
  { month: 'Mar', approved: 5 },
  { month: 'Apr', approved: 7 },
  { month: 'May', approved: 9 },
  { month: 'Jun', approved: 7 },
];

// Custom tooltip shared by recharts charts
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-lg">
      {label ? <p className="mb-1 font-semibold text-slate-700">{label}</p> : null}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || p.fill }} className="font-medium">
          {p.name ? `${p.name}: ` : ''}{p.value}
        </p>
      ))}
    </div>
  );
}

// KPI card used in the summary strip
function KpiCard({ label, value, sub, accent }) {
  return (
    <div className={`rounded-3xl border bg-white p-5 shadow-sm shadow-slate-200/70 ${accent?.border || 'border-slate-200'}`}>
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold tracking-tight ${accent?.text || 'text-slate-800'}`}>{value}</p>
      {sub ? <p className="mt-1 text-xs text-slate-400">{sub}</p> : null}
    </div>
  );
}

// Section wrapper with title
function ChartSection({ title, badge, children }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
      <div className="mb-4 flex items-center gap-3">
        <p className="font-semibold text-slate-800">{title}</p>
        {badge ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">{badge}</span>
        ) : null}
      </div>
      {children}
    </div>
  );
}

function AnalyticsDashboard({ customers, compact = false }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const res = await fetch(buildApiUrl('/analytics'));
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) setAnalytics(data);
        }
      } catch { /* backend unreachable  show demo */ }
      if (!cancelled) setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const hasLive = analytics !== null && analytics.generated > 0;

  // KPIs 
  const kpi = useMemo(() => {
    if (!hasLive) return DEMO_KPI;
    return {
      generated:     analytics.generated,
      approvalRate:  analytics.approval_rate,   // null if no decisive votes yet
      avgConfidence: analytics.avg_confidence,  // null if no rows
      saved:    DEMO_KPI.saved,     // cannot derive from actions alone
      renewals: DEMO_KPI.renewals,
    };
  }, [hasLive, analytics]);

  // Recommendation Status pie 
  const statusPie = useMemo(() => {
    if (!hasLive) return DEMO_STATUS_PIE;
    const slices = [
      { name: 'Approved', value: analytics.approved },
      { name: 'Rejected', value: analytics.rejected },
      { name: 'Edited',   value: analytics.edited   },
    ].filter((s) => s.value > 0);
    return slices.length ? slices : DEMO_STATUS_PIE;
  }, [hasLive, analytics]);

  // Risk / Health bars  customer data, no action equivalent 
  const riskBar = useMemo(() => [
    { label: 'High',   count: customers.filter((c) => c.healthScore < 40).length  || DEMO_RISK_BAR[0].count },
    { label: 'Medium', count: customers.filter((c) => c.healthScore >= 40 && c.healthScore < 70).length || DEMO_RISK_BAR[1].count },
    { label: 'Low',    count: customers.filter((c) => c.healthScore >= 70).length || DEMO_RISK_BAR[2].count },
  ], [customers]);

  const healthBar = useMemo(() => [
    { label: '039 At Risk',   count: customers.filter((c) => c.healthScore < 40).length  || DEMO_HEALTH_BAR[0].count },
    { label: '4069 Watch',    count: customers.filter((c) => c.healthScore >= 40 && c.healthScore < 70).length || DEMO_HEALTH_BAR[1].count },
    { label: '70100 Healthy', count: customers.filter((c) => c.healthScore >= 70).length || DEMO_HEALTH_BAR[2].count },
  ], [customers]);

  // Approval Trend line 
  const trendLine = useMemo(() => {
    if (!hasLive || !analytics.by_month?.length) return DEMO_TREND_LINE;
    return analytics.by_month;
  }, [hasLive, analytics]);

  const PIE_PALETTE    = [CHART_COLORS.approved, CHART_COLORS.rejected, CHART_COLORS.pending];
  const RISK_PALETTE   = [CHART_COLORS.high, CHART_COLORS.medium, CHART_COLORS.low];
  const HEALTH_PALETTE = [CHART_COLORS.atRisk, CHART_COLORS.watch, CHART_COLORS.healthy];

  // Show '' for null values (approval_rate / avg_confidence before any decisions)
  function fmt(val, suffix = '') {
    if (loading) return '...';
    if (val === null || val === undefined) return '';
    return `${val}${suffix}`;
  }

  return (
    <div className="space-y-6">
      {/*  Page header (full page only)  */}
      {!compact && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-sky-600">Analytics</p>
              <h3 className="mt-0.5 text-2xl font-semibold tracking-tight">Business Impact Dashboard</h3>
              <p className="mt-1 text-sm text-slate-500">
                {hasLive
                  ? 'Computed from the recommendation_actions store.'
                  : 'No live actions yet  showing representative demo values.'}
              </p>
            </div>
            {!hasLive && (
              <span className="shrink-0 self-start rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                Demo Data
              </span>
            )}
          </div>
        </div>
      )}

      {/*  KPI cards (full Analytics page only)  */}
      {!compact && (
        <section aria-label="KPI summary">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Key Performance Indicators</p>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <KpiCard label="Recommendations Generated" value={fmt(kpi.generated)}
              accent={{ border: 'border-sky-200', text: 'text-sky-700' }} />
            <KpiCard label="Approval Rate" value={fmt(kpi.approvalRate, '%')}
              sub={hasLive ? 'approved | (approved + rejected)' : undefined}
              accent={{ border: 'border-emerald-200', text: 'text-emerald-600' }} />
            <KpiCard label="Avg. Confidence" value={fmt(kpi.avgConfidence, '%')}
              sub={hasLive ? 'mean across all actions' : undefined}
              accent={{ border: 'border-indigo-200', text: 'text-indigo-600' }} />
            <KpiCard label="Customers Saved" value={fmt(kpi.saved)} sub="Demo estimate"
              accent={{ border: 'border-violet-200', text: 'text-violet-600' }} />
            <KpiCard label="Renewals Improved" value={fmt(kpi.renewals)} sub="Demo estimate"
              accent={{ border: 'border-rose-200', text: 'text-rose-500' }} />
          </div>
        </section>
      )}

      {/*  Charts row 1  */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartSection title="Recommendation Status" badge="Pie Chart">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={statusPie} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                paddingAngle={3} dataKey="value"
                label={({ name, percent }) => `${name} ${Math.round(percent * 100)}%`} labelLine={false}>
                {statusPie.map((_, i) => <Cell key={i} fill={PIE_PALETTE[i % PIE_PALETTE.length]} />)}
              </Pie>
              <ReTooltip content={<ChartTooltip />} />
              <Legend iconType="circle" iconSize={10} />
            </PieChart>
          </ResponsiveContainer>
        </ChartSection>

        <ChartSection title="Risk Distribution" badge="Bar Chart">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={riskBar} barCategoryGap="35%" margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <ReTooltip content={<ChartTooltip />} cursor={{ fill: '#f1f5f9' }} />
              <Bar dataKey="count" name="Customers" radius={[6, 6, 0, 0]}>
                {riskBar.map((_, i) => <Cell key={i} fill={RISK_PALETTE[i % RISK_PALETTE.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>
      </div>

      {/*  Charts row 2  */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartSection title="Health Score Distribution" badge="Bar Chart">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={healthBar} barCategoryGap="35%" margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <ReTooltip content={<ChartTooltip />} cursor={{ fill: '#f1f5f9' }} />
              <Bar dataKey="count" name="Customers" radius={[6, 6, 0, 0]}>
                {healthBar.map((_, i) => <Cell key={i} fill={HEALTH_PALETTE[i % HEALTH_PALETTE.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        <ChartSection title="Approval Trend" badge="Line Chart">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendLine} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <ReTooltip content={<ChartTooltip />} />
              <Line type="monotone" dataKey="approved" name="Approved"
                stroke={CHART_COLORS.line} strokeWidth={2.5}
                dot={{ r: 4, fill: CHART_COLORS.line, strokeWidth: 0 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartSection>
      </div>
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const { customer_id } = useParams();
  const [customers, setCustomers] = useState(() => parseCustomers(customersCsv, usageCsv, crmData));

  // Fetch live customers from API (falls back to static CSV data if API unavailable)
  useEffect(() => {
    async function loadCustomers() {
      try {
        const res = await fetch(buildApiUrl('/customers'));
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setCustomers(data);
          }
        }
      } catch {
        // Keep static fallback silently
      }
    }
    loadCustomers();
  }, []);
  const [analysisMode, setAnalysisMode] = useState('paste');
  const [uploadedTranscriptText, setUploadedTranscriptText] = useState('');
  const [pastedTranscriptText, setPastedTranscriptText] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [completedSteps, setCompletedSteps] = useState(0);
  const [animationFinished, setAnimationFinished] = useState(false);
  const [recommendationReady, setRecommendationReady] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    const stored = window.sessionStorage.getItem('xlventures_analysis_result');
    return stored ? JSON.parse(stored) : null;
  });
  const [activeSessionId, setActiveSessionId] = useState(() => {
    if (typeof window === 'undefined') {
      return '';
    }
    return window.sessionStorage.getItem('xlventures_active_session') || '';
  });
  const [analysisCustomerId, setAnalysisCustomerId] = useState(() => {
    if (typeof window === 'undefined') {
      return '';
    }
    return window.sessionStorage.getItem('xlventures_analysis_customer') || '';
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('xlventures_active_session', activeSessionId);
      window.sessionStorage.setItem('xlventures_analysis_customer', analysisCustomerId);
    }
  }, [activeSessionId, analysisCustomerId]);

  const summaryStats = useMemo(() => {
    const healthyCustomers = customers.filter((customer) => customer.healthScore >= 60).length;
    const atRiskCustomers = customers.filter((customer) => customer.healthScore < 40).length;
    const renewalsThisMonth = customers.filter((customer) => customer.daysToRenewal <= 30).length;

    return [
      { label: 'Total Customers', value: customers.length, accent: 'bg-sky-100 text-sky-700' },
      { label: 'Healthy Customers', value: healthyCustomers, accent: 'bg-emerald-100 text-emerald-700' },
      { label: 'At Risk Customers', value: atRiskCustomers, accent: 'bg-rose-100 text-rose-700' },
      { label: 'Renewals This Month', value: renewalsThisMonth, accent: 'bg-amber-100 text-amber-700' },
    ];
  }, [customers]);

  const selectedCustomer = customers.find((customer) => customer.id === customer_id) || null;
  const isCustomerDetail = location.pathname.startsWith('/customer/');
  const isAnalysis = location.pathname === '/analysis';
  const isAnalysisResults = location.pathname === '/analysis-results';
  const currentPage = isAnalysisResults ? 'Analysis Results' : isAnalysis ? 'Analyzing Customer' : isCustomerDetail ? 'Customer Profile' : location.pathname === '/customers' ? 'Customers' : location.pathname === '/history' ? 'History' : location.pathname === '/analytics' ? 'Analytics' : 'Dashboard';

  function handleTranscriptFileSelection(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (loadedEvent) => {
      const text = String(loadedEvent.target?.result || '');
      setUploadedTranscriptText(text);
      setUploadError('');
    };
    reader.onerror = () => {
      setUploadError('Unable to read the selected transcript file.');
    };
    reader.readAsText(file);
  }

  async function handleAnalyze() {
    if (!selectedCustomer) {
      setUploadError('Select a customer before analyzing a transcript.');
      return;
    }

    const transcriptText = analysisMode === 'upload' ? uploadedTranscriptText : pastedTranscriptText;
    if (!transcriptText.trim()) {
      setUploadError('Please provide transcript text before analyzing.');
      return;
    }

    setIsUploading(true);
    setUploadError('');

    try {
      const response = await fetch(buildApiUrl('/upload_transcript'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: selectedCustomer.id, transcript_text: transcriptText }),
      });

      if (!response.ok) {
        throw new Error('Unable to start transcript analysis.');
      }

      const payload = await response.json();
      const sessionId = payload.session_id || '';
      if (!sessionId) {
        throw new Error('The backend did not return a session id.');
      }

      setActiveSessionId(sessionId);
      setAnalysisCustomerId(selectedCustomer.id);
      navigate('/analysis');
    } catch (error) {
      setUploadError(error.message || 'An unexpected error occurred.');
    } finally {
      setIsUploading(false);
    }
  }

  useEffect(() => {
    if (location.pathname !== '/analysis') {
      return undefined;
    }

    if (!activeSessionId) {
      setUploadError('Unable to start the analysis because no session was found.');
      return undefined;
    }

    setCompletedSteps(0);
    setAnimationFinished(false);
    setRecommendationReady(false);
    setUploadError('');

    const timers = ANALYSIS_STEPS.map((_, index) => {
      return window.setTimeout(() => {
        setCompletedSteps(index + 1);
      }, (index + 1) * 500);
    });

    const animationTimer = window.setTimeout(() => {
      setAnimationFinished(true);
    }, ANALYSIS_STEPS.length * 500);

    const fetchRecommendations = async () => {
      try {
        const response = await fetch(buildApiUrl(`/recommendation/${activeSessionId}`));
        if (!response.ok) {
          throw new Error('The recommendation request is still processing.');
        }
        const payload = await response.json();
        setAnalysisResult(payload);
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem('xlventures_analysis_result', JSON.stringify(payload));
        }
        setRecommendationReady(true);
      } catch (error) {
        setUploadError(error.message || 'Unable to load the recommendation response.');
      }
    };

    fetchRecommendations();

    return () => {
      timers.forEach((timerId) => window.clearTimeout(timerId));
      window.clearTimeout(animationTimer);
    };
  }, [activeSessionId, location.pathname]);

  useEffect(() => {
    if (location.pathname === '/analysis' && animationFinished && recommendationReady) {
      navigate('/analysis-results');
    }
  }, [animationFinished, recommendationReady, location.pathname, navigate]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-200 bg-slate-950 px-4 py-6 text-slate-200 lg:w-72 lg:border-b-0 lg:border-r lg:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-500 text-lg font-semibold text-white">X</div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-400">XL Ventures</p>
              <h1 className="text-lg font-semibold text-white">Customer Success</h1>
            </div>
          </div>

          <nav className="mt-10 space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/');
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive: navActive }) => `flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium transition ${navActive || isActive ? 'bg-sky-500/20 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}
                >
                  <span>{item.label}</span>
                  <span className="text-xs text-slate-400">-</span>
                </NavLink>
              );
            })}
          </nav>
        </aside>

        <main className="flex-1 bg-slate-50 p-4 md:p-6 lg:p-8">
          <header className="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">XL Ventures</p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight">{currentPage}</h2>
              </div>
            </div>
          </header>

          {isAnalysis ? (
            <div className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/70">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">AI Workflow</p>
                    <h3 className="mt-1 text-3xl font-semibold tracking-tight">Analyzing Customer...</h3>
                    <p className="mt-2 max-w-2xl text-sm text-slate-600">The agent workflow is running in the background so the demo can showcase each stage of the analysis experience.</p>
                  </div>
                  <div className="flex items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
                    <Spinner className="h-4 w-4" />
                    <span>Processing transcript</span>
                  </div>
                </div>

                <div className="mt-8 space-y-3">
                  {ANALYSIS_STEPS.map((step, index) => {
                    const isComplete = index + 1 <= completedSteps;
                    const isActive = index + 1 === completedSteps + 1 && completedSteps < ANALYSIS_STEPS.length;

                    return (
                      <div key={step} className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition-all duration-500 ${isComplete ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : isActive ? 'border-sky-200 bg-sky-50 text-sky-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                        <span className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold ${isComplete ? 'bg-emerald-600 text-white' : isActive ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                          {isComplete ? '' : index + 1}
                        </span>
                        <span className="font-medium">{step}</span>
                      </div>
                    );
                  })}

                  <div className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition-all duration-500 ${animationFinished ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                    <span className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold ${animationFinished ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                      {animationFinished ? '' : ''}
                    </span>
                    <span className="font-medium">Generating Recommendations...</span>
                  </div>
                </div>

                {uploadError ? <p className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{uploadError}</p> : null}
              </div>
            </div>
          ) : isAnalysisResults ? (
            <AnalysisResults
              analysisResult={analysisResult}
              analysisCustomerId={analysisCustomerId}
              activeSessionId={activeSessionId}
              customers={customers}
              navigate={navigate}
            />
          ) : isCustomerDetail ? (
            <div className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">Customer Summary</p>
                    <h3 className="mt-1 text-2xl font-semibold">{selectedCustomer?.name || 'Customer profile'}</h3>
                    <p className="mt-2 text-sm text-slate-600">{selectedCustomer ? `${selectedCustomer.industry}  ${selectedCustomer.plan} plan` : 'No customer found for this route.'}</p>
                  </div>
                  <button type="button" onClick={() => navigate('/customers')} className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100">
                     Back to customers
                  </button>
                </div>

                {selectedCustomer ? (
                  <div className="mt-6 grid gap-4 lg:grid-cols-2">
                    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                      <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                          <p className="text-sm text-slate-500">Subscription Plan</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{selectedCustomer.plan}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Health Score</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{selectedCustomer.healthScore}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Renewal Countdown</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{formatRenewalCountdown(selectedCustomer.daysToRenewal)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Open Support Tickets</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{selectedCustomer.openSupportTickets}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Active Users</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{selectedCustomer.activeUsers} / {selectedCustomer.licensedUsers}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Recent Meeting Date</p>
                          <p className="mt-2 text-lg font-semibold text-slate-800">{selectedCustomer.recentMeetingDate || ''}</p>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                      <p className="text-sm font-semibold uppercase tracking-[0.25em] text-sky-600">Analyze New Meeting</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        <button type="button" onClick={() => setAnalysisMode('upload')} className={`rounded-full px-4 py-2 text-sm font-semibold ${analysisMode === 'upload' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-700'}`}>
                          Upload Transcript
                        </button>
                        <button type="button" onClick={() => setAnalysisMode('paste')} className={`rounded-full px-4 py-2 text-sm font-semibold ${analysisMode === 'paste' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-700'}`}>
                          Paste Transcript
                        </button>
                      </div>

                      {analysisMode === 'upload' ? (
                        <label className="mt-4 block rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
                          <span className="mb-2 block font-semibold text-slate-700">Upload .txt file</span>
                          <input type="file" accept=".txt" onChange={handleTranscriptFileSelection} className="block w-full text-sm text-slate-500 file:mr-3 file:rounded-full file:border-0 file:bg-sky-600 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white" />
                          {uploadedTranscriptText ? <p className="mt-3 text-xs text-emerald-700">Transcript ready for analysis.</p> : null}
                        </label>
                      ) : (
                        <textarea
                          value={pastedTranscriptText}
                          onChange={(event) => setPastedTranscriptText(event.target.value)}
                          rows={8}
                          className="mt-4 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm shadow-sm focus:border-sky-500 focus:outline-none"
                          placeholder="Paste the meeting transcript here"
                        />
                      )}

                      {uploadError ? <p className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{uploadError}</p> : null}

                      <button type="button" onClick={handleAnalyze} disabled={isUploading} className="mt-4 inline-flex items-center justify-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400">
                        {isUploading ? 'Analyzing...' : 'Analyze'}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          ) : location.pathname === '/history' ? (
            <RecommendationHistory customers={customers} />
          ) : location.pathname === '/analytics' ? (
            <AnalyticsDashboard customers={customers} />
          ) : location.pathname === '/customers' ? (
            <div className="space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Customer Management</p>
                <h3 className="mt-0.5 text-2xl font-semibold tracking-tight">Active customer portfolio</h3>
                <p className="mt-1 text-sm text-slate-500">{customers.length} customers | sortable &amp; searchable</p>
              </div>
              <CustomerTable customers={customers} navigate={navigate} />
            </div>
          ) : (
            <div className="space-y-6">
              {/* KPI cards */}
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {summaryStats.map((card) => (
                  <StatCard key={card.label} label={card.label} value={card.value} />
                ))}
              </section>

              {/* Customers Needing Attention */}
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Customers</p>
                    <h3 className="mt-0.5 text-lg font-semibold text-slate-800">Needing Attention</h3>
                  </div>
                  <Link to="/customers" className="text-sm font-semibold text-sky-600 hover:text-sky-700">View all </Link>
                </div>
                <div className="space-y-2">
                  {[...customers]
                    .sort((a, b) => a.healthScore - b.healthScore)
                    .slice(0, 5)
                    .map((c) => {
                      const tone = getStatusTone(c.healthScore);
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => navigate(`/customer/${c.id}`)}
                          className="flex w-full items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-left transition hover:bg-slate-100"
                        >
                          <div className="min-w-0">
                            <p className="font-semibold text-slate-800 truncate">{c.name}</p>
                            <p className="mt-0.5 text-xs text-slate-400">{c.industry} | {formatRenewalCountdown(c.daysToRenewal)} to renewal</p>
                          </div>
                          <div className="ml-4 flex shrink-0 items-center gap-2">
                            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${tone.classes}`}>{tone.label}</span>
                            <span className={`font-semibold text-sm ${c.healthScore < 40 ? 'text-rose-600' : c.healthScore < 70 ? 'text-amber-500' : 'text-emerald-600'}`}>{c.healthScore}</span>
                          </div>
                        </button>
                      );
                    })}
                </div>
              </section>

              {/* Bottom row: Recent Recommendation Activity + Recent Approvals */}
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Recent Recommendation Activity */}
                <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">AI</p>
                      <h3 className="mt-0.5 text-lg font-semibold text-slate-800">Recent Recommendations</h3>
                    </div>
                    <Link to="/history" className="text-sm font-semibold text-sky-600 hover:text-sky-700">History </Link>
                  </div>
                  <ul className="space-y-2">
                    {DEMO_HISTORY.slice(0, 4).map((row, i) => {
                      const cust = customers.find((c) => c.id === row.customer_id);
                      return (
                        <li key={i} className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
                          <span className={`mt-0.5 rounded-full px-2 py-0.5 text-xs font-semibold ${priorityBadgeColor(row.priority)}`}>{row.priority}</span>
                          <div className="min-w-0">
                            <p className="text-sm text-slate-700 leading-snug line-clamp-2">{row.action}</p>
                            <p className="mt-0.5 text-xs text-slate-400">{cust?.name || row.customer_id}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </section>

                {/* Recent Approvals */}
                <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/70">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Outcomes</p>
                      <h3 className="mt-0.5 text-lg font-semibold text-slate-800">Recent Approvals</h3>
                    </div>
                    <Link to="/history" className="text-sm font-semibold text-sky-600 hover:text-sky-700">History </Link>
                  </div>
                  <ul className="space-y-2">
                    {DEMO_HISTORY.slice(0, 4).map((row, i) => {
                      const cust = customers.find((c) => c.id === row.customer_id);
                      return (
                        <li key={i} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-700 truncate">{cust?.name || row.customer_id}</p>
                            <p className="mt-0.5 text-xs text-slate-400 line-clamp-1">{row.action}</p>
                          </div>
                          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${outcomeBadge(row.outcome)}`}>{row.outcome}</span>
                        </li>
                      );
                    })}
                  </ul>
                </section>
              </div>

              {/* Mini KPI charts */}
              <AnalyticsDashboard customers={customers} compact />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
