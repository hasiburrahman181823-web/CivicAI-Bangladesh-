import React, { useState, useEffect } from 'react';
import {
  Search,
  CheckCircle,
  Clock,
  MapPin,
  ShieldCheck,
  Building2,
  Calendar,
  AlertCircle,
  Check,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { trackComplaint } from '../api';

interface TrackPageProps {
  initialTrackingId?: string;
  lang: 'en' | 'bn';
}

export const TrackPage: React.FC<TrackPageProps> = ({ initialTrackingId = '', lang }) => {
  const [trackingId, setTrackingId] = useState(initialTrackingId);
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (idToTrack?: string) => {
    const id = idToTrack || trackingId;
    if (!id.trim()) return;

    setError(null);
    setLoading(true);
    try {
      const res = await trackComplaint(id);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'No complaint found with this Tracking ID.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialTrackingId) {
      setTrackingId(initialTrackingId);
      handleSearch(initialTrackingId);
    }
  }, [initialTrackingId]);

  const stages = [
    { key: 'Submitted', label: '1. Registered' },
    { key: 'AI_Analyzed', label: '2. AI Analyzed' },
    { key: 'Verified', label: '3. Verified' },
    { key: 'In_Progress', label: '4. In Field Action' },
    { key: 'Resolved', label: '5. Resolved' }
  ];

  const getStageIndex = (status: string) => {
    switch (status) {
      case 'Submitted': return 0;
      case 'AI_Analyzed': return 1;
      case 'Verified': return 2;
      case 'Assigned': return 2;
      case 'In_Progress': return 3;
      case 'Resolved': return 4;
      default: return 1;
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Search Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          {lang === 'bn' ? 'অভিযোগের অগ্রগতি ট্র্যাক করুন' : 'Track Your Complaint Status'}
        </h1>
        <p className="text-xs text-slate-500">
          Enter your unique Tracking ID to inspect real-time progress, municipal department assignment, and before/after resolution evidence.
        </p>

        {/* Search Bar */}
        <form
          onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
          className="flex items-center bg-white p-2 rounded-2xl border border-slate-300 shadow-md focus-within:ring-2 focus-within:ring-primary-600 transition"
        >
          <Search className="w-5 h-5 text-primary-600 ml-3" />
          <input
            type="text"
            required
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
            placeholder="Enter Tracking ID (e.g. BD-2026-10001)..."
            className="flex-1 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-primary-600 hover:bg-primary-700 text-white font-bold text-xs uppercase px-6 py-2.5 rounded-xl transition shadow-sm disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Track'}
          </button>
        </form>

        {/* Quick Example Pins */}
        <div className="flex items-center justify-center space-x-2 text-xs text-slate-400">
          <span>Try sample IDs:</span>
          <button
            type="button"
            onClick={() => { setTrackingId('BD-2026-10001'); handleSearch('BD-2026-10001'); }}
            className="text-primary-600 hover:underline font-mono"
          >
            BD-2026-10001
          </button>
          <span>•</span>
          <button
            type="button"
            onClick={() => { setTrackingId('BD-2026-10004'); handleSearch('BD-2026-10004'); }}
            className="text-primary-600 hover:underline font-mono"
          >
            BD-2026-10004
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tracking Result View */}
      {data && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-6 p-6 sm:p-8 animate-in fade-in">
          {/* Top Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold bg-primary-50 text-primary-700 px-3 py-1 rounded-full border border-primary-200">
                  #{data.tracking_id}
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  {data.category}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 mt-2">{data.title}</h2>
              <div className="flex items-center space-x-2 text-xs text-slate-500 mt-1">
                <MapPin className="w-3.5 h-3.5 text-primary-600" />
                <span>{data.area_name ? `${data.area_name}, ` : ''}{data.upazila}, {data.district}</span>
              </div>
            </div>

            <div className="text-right sm:border-l sm:border-slate-100 sm:pl-6">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Current Status
              </span>
              <div className="text-lg font-extrabold text-primary-700 capitalize mt-0.5">
                {data.status.replace('_', ' ')}
              </div>
              <div className="text-xs text-slate-500 font-medium">
                Overall Progress: {data.progress_percent}%
              </div>
            </div>
          </div>

          {/* Stepper Progress Bar */}
          <div className="py-2">
            <div className="flex items-center justify-between relative mb-2">
              <div className="absolute top-1/2 left-0 right-0 h-1 bg-slate-200 -translate-y-1/2 z-0" />
              <div
                className="absolute top-1/2 left-0 h-1 bg-primary-600 -translate-y-1/2 z-0 transition-all duration-500"
                style={{ width: `${(getStageIndex(data.status) / (stages.length - 1)) * 100}%` }}
              />

              {stages.map((st, index) => {
                const currentIndex = getStageIndex(data.status);
                const isCompleted = index <= currentIndex;
                const isCurrent = index === currentIndex;

                return (
                  <div key={st.key} className="flex flex-col items-center relative z-10">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition ${
                        isCompleted
                          ? 'bg-primary-600 text-white shadow-md shadow-primary-600/30'
                          : 'bg-white text-slate-400 border-2 border-slate-300'
                      }`}
                    >
                      {isCompleted ? <Check className="w-4 h-4" /> : index + 1}
                    </div>
                    <span className={`text-[10px] mt-1.5 font-bold hidden sm:inline ${isCurrent ? 'text-primary-700' : isCompleted ? 'text-slate-800' : 'text-slate-400'}`}>
                      {st.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Departmental & SLA Info Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-400 font-semibold uppercase text-[10px] block">Assigned Authority</span>
              <strong className="text-slate-800 font-bold block truncate">{data.assigned_department || 'Central Municipal Desk'}</strong>
            </div>
            <div>
              <span className="text-slate-400 font-semibold uppercase text-[10px] block">Field Supervisor</span>
              <strong className="text-slate-800 font-bold block">{data.assigned_officer || 'Supervising Engineer'}</strong>
            </div>
            <div>
              <span className="text-slate-400 font-semibold uppercase text-[10px] block">AI Priority Score</span>
              <strong className="text-primary-700 font-bold block">{data.ai_priority_score}/100 ({data.ai_priority_level})</strong>
            </div>
          </div>

          {/* AI Explanation Card */}
          <div className="bg-primary-50/70 border border-primary-200 rounded-xl p-5 space-y-2">
            <div className="flex items-center space-x-2 text-primary-800 font-bold text-xs">
              <Sparkles className="w-4 h-4 text-primary-600" />
              <span>AI Multi-Model Intelligence Rationale</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {lang === 'bn' && data.ai_explanation_bn ? data.ai_explanation_bn : data.ai_explanation_en}
            </p>
          </div>

          {/* Resolution Evidence Box (If Resolved) */}
          {data.status === 'Resolved' && (
            <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3">
              <div className="flex items-center space-x-2 text-emerald-800 font-bold text-sm">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                <span>Civic Resolution Verified On-Site</span>
              </div>
              <p className="text-xs text-emerald-900 leading-relaxed">
                {data.resolution_notes || 'All civic repairs completed and officially cleared by municipal field teams.'}
              </p>
              {data.resolved_at && (
                <div className="text-[11px] text-emerald-700 font-semibold">
                  Official Completion Date: {new Date(data.resolved_at).toLocaleDateString()}
                </div>
              )}
            </div>
          )}

          {/* Timeline Milestones */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
              Official Progress Timeline & Milestones
            </h3>
            <div className="space-y-3">
              {data.timeline.map((item: any, idx: number) => (
                <div key={idx} className="flex items-start space-x-3 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full bg-primary-600 mt-1 shrink-0" />
                  <div className="flex-1 bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <div className="flex items-center justify-between">
                      <strong className="text-slate-800 font-bold">{item.title}</strong>
                      <span className="text-[11px] text-slate-400">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    {item.description && (
                      <p className="text-slate-600 mt-1 leading-relaxed">{item.description}</p>
                    )}
                    <span className="text-[10px] text-slate-400 font-medium block mt-1">
                      Action taken by: {item.performed_by}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
