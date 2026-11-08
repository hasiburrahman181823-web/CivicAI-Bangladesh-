import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle,
  Clock,
  Layers,
  Sparkles,
  GitMerge,
  FileSpreadsheet,
  RefreshCw,
  Search,
  Filter,
  AlertTriangle,
  UserCheck,
  Building2,
  Calendar,
  X
} from 'lucide-react';
import {
  fetchAdminStats,
  fetchAdminComplaints,
  verifyComplaint,
  assignComplaint,
  updateComplaintStatus,
  mergeDuplicateComplaints,
  fetchAIMetrics,
  fetchAuditLogs
} from '../api';
import { AdminStats, User } from '../types';

interface AdminPageProps {
  currentUser: User | null;
  onOpenAuth: () => void;
  lang: 'en' | 'bn';
}

export const AdminPage: React.FC<AdminPageProps> = ({ currentUser, onOpenAuth, lang }) => {
  const [activeTab, setActiveTab] = useState<'queue' | 'ai_models' | 'audit_logs'>('queue');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('All');
  const [search, setSearch] = useState('');

  // Modals state
  const [verifyModalItem, setVerifyModalItem] = useState<any | null>(null);
  const [overrideCategory, setOverrideCategory] = useState('');
  const [overrideSeverity, setOverrideSeverity] = useState('');
  const [overrideReason, setOverrideReason] = useState('');

  const [statusModalItem, setStatusModalItem] = useState<any | null>(null);
  const [newStatus, setNewStatus] = useState('In_Progress');
  const [resolutionNotes, setResolutionNotes] = useState('');

  const [mergeModalItem, setMergeModalItem] = useState<any | null>(null);
  const [duplicateIdToMerge, setDuplicateIdToMerge] = useState('');

  // AI & Audit state
  const [aiMetrics, setAiMetrics] = useState<any | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sData, cData] = await Promise.all([
        fetchAdminStats().catch(() => null),
        fetchAdminComplaints({ status: statusFilter, search }).catch(() => [])
      ]);
      if (sData) setStats(sData);
      setComplaints(cData || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadAIMetricsAndLogs = async () => {
    try {
      const [m, l] = await Promise.all([
        fetchAIMetrics().catch(() => null),
        fetchAuditLogs().catch(() => [])
      ]);
      setAiMetrics(m);
      setAuditLogs(l);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeTab === 'ai_models' || activeTab === 'audit_logs') {
      loadAIMetricsAndLogs();
    }
  }, [activeTab]);

  // Handle Verify Action
  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyModalItem) return;

    try {
      await verifyComplaint(verifyModalItem.id, {
        verified_category: overrideCategory || undefined,
        verified_severity: overrideSeverity || undefined,
        override_reason: overrideReason || undefined,
      });
      setVerifyModalItem(null);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    }
  };

  // Handle Status Update
  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusModalItem) return;

    try {
      await updateComplaintStatus(statusModalItem.id, {
        status: newStatus,
        notes: resolutionNotes,
      });
      setStatusModalItem(null);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Status update failed');
    }
  };

  // Handle Duplicate Merge
  const handleMergeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mergeModalItem || !duplicateIdToMerge) return;

    try {
      await mergeDuplicateComplaints(mergeModalItem.id, parseInt(duplicateIdToMerge));
      setMergeModalItem(null);
      setDuplicateIdToMerge('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Duplicate merge failed');
    }
  };

  if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'officer')) {
    return (
      <div className="max-w-md mx-auto my-20 p-8 bg-white border border-slate-200 rounded-2xl shadow-sm text-center space-y-4">
        <ShieldAlert className="w-12 h-12 text-primary-600 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Administrator Access Required</h2>
        <p className="text-xs text-slate-500">
          This portal is restricted to authorized municipal officers and central administrators.
        </p>
        <button
          onClick={onOpenAuth}
          className="bg-primary-600 hover:bg-primary-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl transition"
        >
          Sign in as Admin (Demo Available)
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Top Admin Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold bg-slate-900 text-white px-2.5 py-1 rounded">
              ADMINISTRATIVE CONTROL
            </span>
            <span className="text-xs font-semibold text-slate-500">
              Officer: {currentUser.full_name} ({currentUser.role})
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Executive Command & Verification Console
          </h1>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <a
            href="http://localhost:8000/api/admin/export"
            download
            className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold px-4 py-2 rounded-xl text-xs flex items-center space-x-1.5 transition shadow-sm"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Export CSV</span>
          </a>

          <button
            onClick={loadData}
            className="p-2 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 text-slate-600 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-white p-4 rounded-xl border border-slate-200">
            <span className="text-[10px] font-bold text-slate-400 uppercase">Total Queue</span>
            <div className="text-2xl font-black text-slate-900">{stats.total_complaints}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200">
            <span className="text-[10px] font-bold text-amber-500 uppercase">Pending Review</span>
            <div className="text-2xl font-black text-amber-600">{stats.pending_complaints}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200">
            <span className="text-[10px] font-bold text-blue-500 uppercase">Verified</span>
            <div className="text-2xl font-black text-blue-600">{stats.verified_complaints}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200">
            <span className="text-[10px] font-bold text-primary-500 uppercase">Active In Field</span>
            <div className="text-2xl font-black text-primary-600">{stats.in_progress_complaints}</div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200">
            <span className="text-[10px] font-bold text-emerald-500 uppercase">Resolved</span>
            <div className="text-2xl font-black text-emerald-600">{stats.resolved_complaints}</div>
          </div>
        </div>
      )}

      {/* Admin Tabs */}
      <div className="flex border-b border-slate-200 space-x-4 text-xs font-bold">
        <button
          onClick={() => setActiveTab('queue')}
          className={`pb-3 transition flex items-center space-x-1.5 ${
            activeTab === 'queue'
              ? 'border-b-2 border-primary-600 text-primary-700'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>AI-Prioritized Complaint Queue</span>
        </button>
        <button
          onClick={() => setActiveTab('ai_models')}
          className={`pb-3 transition flex items-center space-x-1.5 ${
            activeTab === 'ai_models'
              ? 'border-b-2 border-primary-600 text-primary-700'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>AI Models & Confusion Matrix</span>
        </button>
        <button
          onClick={() => setActiveTab('audit_logs')}
          className={`pb-3 transition flex items-center space-x-1.5 ${
            activeTab === 'audit_logs'
              ? 'border-b-2 border-primary-600 text-primary-700'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Administrative Audit Logs</span>
        </button>
      </div>

      {/* Tab 1: AI Queue Table */}
      {activeTab === 'queue' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-500">Filter Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-medium"
              >
                <option value="All">All Statuses</option>
                <option value="AI_Analyzed">AI Analyzed (Needs Verification)</option>
                <option value="Verified">Verified by Officer</option>
                <option value="In_Progress">Active In Field</option>
                <option value="Resolved">Resolved</option>
              </select>
            </div>

            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadData()}
                placeholder="Search tracking ID or keyword..."
                className="pl-3 pr-8 py-1.5 border border-slate-300 rounded-lg text-xs"
              />
            </div>
          </div>

          {/* Queue Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase text-[10px] font-bold">
                <tr>
                  <th className="py-3 px-3">Tracking ID</th>
                  <th className="py-3 px-3">Title & Area</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">AI Severity</th>
                  <th className="py-3 px-3">AI Priority</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Administrative Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3 font-mono font-bold text-slate-800">
                      #{c.tracking_id}
                    </td>
                    <td className="py-3 px-3 max-w-xs">
                      <div className="font-bold text-slate-900 truncate">{c.title}</div>
                      <div className="text-[11px] text-slate-400">
                        📍 {c.upazila}, {c.district}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-700">{c.category}</span>
                      {c.admin_override && (
                        <span className="block text-[10px] text-amber-600 font-bold">
                          ⚠️ Officer Adjusted
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`font-bold px-2 py-0.5 rounded ${
                        c.severity === 'Critical' ? 'bg-rose-100 text-rose-800' :
                        c.severity === 'High' ? 'bg-amber-100 text-amber-800' :
                        'bg-sky-100 text-sky-800'
                      }`}>
                        {c.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-extrabold text-primary-700 bg-primary-50 px-2 py-0.5 rounded border border-primary-200">
                        {c.ai_priority_score}/100
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-700">{c.status.replace('_', ' ')}</span>
                    </td>
                    <td className="py-3 px-3 text-right space-x-1.5 whitespace-nowrap">
                      {/* Verify Button */}
                      <button
                        onClick={() => {
                          setVerifyModalItem(c);
                          setOverrideCategory(c.category);
                          setOverrideSeverity(c.severity);
                          setOverrideReason('');
                        }}
                        className="bg-primary-50 hover:bg-primary-100 text-primary-700 border border-primary-200 font-semibold px-2.5 py-1 rounded-lg transition"
                      >
                        Verify / Override
                      </button>

                      {/* Status Button */}
                      <button
                        onClick={() => {
                          setStatusModalItem(c);
                          setNewStatus(c.status === 'Resolved' ? 'In_Progress' : 'Resolved');
                          setResolutionNotes(c.resolution_notes || '');
                        }}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold px-2.5 py-1 rounded-lg transition"
                      >
                        Update Status
                      </button>

                      {/* Merge Button */}
                      <button
                        onClick={() => {
                          setMergeModalItem(c);
                          setDuplicateIdToMerge('');
                        }}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-2 py-1 rounded-lg transition"
                        title="Merge Duplicates"
                      >
                        <GitMerge className="w-3.5 h-3.5 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: AI Models & Metrics */}
      {activeTab === 'ai_models' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">AI Model Performance & Confusion Matrices</h3>
              <p className="text-xs text-slate-500">Live evaluation telemetry from genuine BanglaPSG trained classifiers.</p>
            </div>
          </div>

          {aiMetrics ? (
            <div className="space-y-6 text-xs">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block font-semibold">Category Macro F1</span>
                  <strong className="text-xl font-black text-primary-600">
                    {(aiMetrics.metrics.category_metrics.macro_f1 * 100).toFixed(1)}%
                  </strong>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block font-semibold">Severity Macro F1</span>
                  <strong className="text-xl font-black text-primary-600">
                    {(aiMetrics.metrics.severity_metrics.macro_f1 * 100).toFixed(1)}%
                  </strong>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block font-semibold">Trained Features</span>
                  <strong className="text-xl font-black text-slate-900">
                    {aiMetrics.metrics.feature_count}
                  </strong>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block font-semibold">Model Artifacts</span>
                  <strong className="text-sm font-bold text-emerald-600 block mt-1">
                    Active & Calibrated
                  </strong>
                </div>
              </div>

              {/* Per Language Table */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 uppercase tracking-wide">
                  Per-Language Validation Performance:
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(aiMetrics.metrics.per_language_performance || {}).map(([langName, m]: [string, any]) => (
                    <div key={langName} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                      <strong className="text-slate-900 font-bold block">{langName}</strong>
                      <div className="text-slate-500">Samples: {m.samples}</div>
                      <div className="text-slate-700">Category F1: <strong>{(m.category_macro_f1 * 100).toFixed(1)}%</strong></div>
                      <div className="text-slate-700">Severity F1: <strong>{(m.severity_macro_f1 * 100).toFixed(1)}%</strong></div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Loading AI evaluation benchmarks...</p>
          )}
        </div>
      )}

      {/* Tab 3: Audit Logs */}
      {activeTab === 'audit_logs' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
            Administrative Audit Trail & Decisions Log
          </h3>
          <div className="space-y-2">
            {auditLogs.map((log) => (
              <div key={log.id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-primary-700">{log.action}</span>
                  <span className="text-slate-400">{new Date(log.created_at).toLocaleString()}</span>
                </div>
                <div className="text-slate-700 font-medium">{log.details}</div>
                <div className="text-[10px] text-slate-400">
                  Officer: {log.performed_by_email || 'System'} • Entity: {log.entity_type} #{log.entity_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verify & Override Modal */}
      {verifyModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 border border-slate-200 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">
                Verify Complaint #{verifyModalItem.tracking_id}
              </h3>
              <button onClick={() => setVerifyModalItem(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 font-medium">"{verifyModalItem.title}"</p>

            <form onSubmit={handleVerifySubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Verify or Override Category:</label>
                <select
                  value={overrideCategory}
                  onChange={(e) => setOverrideCategory(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 font-medium"
                >
                  <option value="Infrastructure">Infrastructure</option>
                  <option value="Water & Drainage">Water & Drainage</option>
                  <option value="Waste Management">Waste Management</option>
                  <option value="Electricity & Power">Electricity & Power</option>
                  <option value="Streetlight & Lighting">Streetlight & Lighting</option>
                  <option value="Public Safety & Law">Public Safety & Law</option>
                  <option value="Environment & Pollution">Environment & Pollution</option>
                  <option value="Healthcare & Sanitation">Healthcare & Sanitation</option>
                  <option value="Transport & Traffic">Transport & Traffic</option>
                  <option value="Corruption & Governance">Corruption & Governance</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Verify or Override Severity:</label>
                <select
                  value={overrideSeverity}
                  onChange={(e) => setOverrideSeverity(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 font-medium"
                >
                  <option value="Critical">Critical (Immediate Life Hazard)</option>
                  <option value="High">High Severity</option>
                  <option value="Medium">Medium Severity</option>
                  <option value="Low">Low Severity</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Officer Override Reason / Justification:
                </label>
                <textarea
                  rows={2}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Document why category or severity was adjusted..."
                  className="w-full border border-slate-300 rounded-lg p-2"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <button
                  type="submit"
                  className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2.5 rounded-xl transition"
                >
                  Confirm Verification & Recalculate Priority
                </button>
                <button
                  type="button"
                  onClick={() => setVerifyModalItem(null)}
                  className="px-4 py-2.5 border border-slate-300 rounded-xl"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Update Status Modal */}
      {statusModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 border border-slate-200 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">
                Update Status for #{statusModalItem.tracking_id}
              </h3>
              <button onClick={() => setStatusModalItem(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleStatusSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Select New Status:</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2 font-medium"
                >
                  <option value="Assigned">Assigned to Field Team</option>
                  <option value="In_Progress">In Progress (Active Work)</option>
                  <option value="Resolved">Resolved (Work Completed)</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Resolution Notes / Progress Update:
                </label>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Describe resolution actions taken, team dispatched, or repair details..."
                  className="w-full border border-slate-300 rounded-lg p-2"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <button
                  type="submit"
                  className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-2.5 rounded-xl transition"
                >
                  Save Status Milestone
                </button>
                <button
                  type="button"
                  onClick={() => setStatusModalItem(null)}
                  className="px-4 py-2.5 border border-slate-300 rounded-xl"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Merge Duplicate Modal */}
      {mergeModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 border border-slate-200 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900">
                Merge Duplicate into #{mergeModalItem.tracking_id}
              </h3>
              <button onClick={() => setMergeModalItem(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Enter the Complaint ID of the secondary duplicate report to merge into master complaint #{mergeModalItem.tracking_id}. Citizen endorsements will be pooled.
            </p>

            <form onSubmit={handleMergeSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Duplicate Complaint ID (Number):</label>
                <input
                  type="number"
                  required
                  value={duplicateIdToMerge}
                  onChange={(e) => setDuplicateIdToMerge(e.target.value)}
                  placeholder="e.g. 3"
                  className="w-full border border-slate-300 rounded-lg p-2"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <button
                  type="submit"
                  className="flex-1 bg-slate-900 hover:bg-black text-white font-bold py-2.5 rounded-xl transition"
                >
                  Execute Merge
                </button>
                <button
                  type="button"
                  onClick={() => setMergeModalItem(null)}
                  className="px-4 py-2.5 border border-slate-300 rounded-xl"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
