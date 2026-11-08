import React from 'react';
import { MapPin, ThumbsUp, MessageSquare, Clock, ArrowRight, ShieldCheck, AlertTriangle } from 'lucide-react';
import { ComplaintListItem } from '../types';

interface ComplaintCardProps {
  complaint: ComplaintListItem;
  onSelect: (id: number) => void;
  onUpvote: (id: number) => void;
  lang: 'en' | 'bn';
}

export const ComplaintCard: React.FC<ComplaintCardProps> = ({
  complaint,
  onSelect,
  onUpvote,
  lang
}) => {
  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'Critical':
        return <span className="bg-rose-100 text-rose-800 border border-rose-200 text-[11px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Critical</span>;
      case 'High':
        return <span className="bg-amber-100 text-amber-800 border border-amber-200 text-[11px] font-bold px-2 py-0.5 rounded-full">High</span>;
      case 'Medium':
        return <span className="bg-sky-100 text-sky-800 border border-sky-200 text-[11px] font-bold px-2 py-0.5 rounded-full">Medium</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-bold px-2 py-0.5 rounded-full">Low</span>;
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'Resolved':
        return <span className="bg-emerald-100 text-emerald-800 font-semibold text-xs px-2.5 py-0.5 rounded-full flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> Resolved</span>;
      case 'In_Progress':
        return <span className="bg-primary-100 text-primary-800 font-semibold text-xs px-2.5 py-0.5 rounded-full">In Progress</span>;
      case 'Verified':
        return <span className="bg-blue-100 text-blue-800 font-semibold text-xs px-2.5 py-0.5 rounded-full">Verified</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 font-semibold text-xs px-2.5 py-0.5 rounded-full">Under Review</span>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 hover:border-primary-400 hover:shadow-lg transition-all duration-200 p-5 flex flex-col justify-between group">
      <div>
        {/* Header row: Tracking ID, Category, Severity */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              #{complaint.tracking_id}
            </span>
            <span className="text-xs font-semibold text-primary-700 bg-primary-50 px-2.5 py-0.5 rounded-full">
              {complaint.category}
            </span>
          </div>
          <div>{getSeverityBadge(complaint.severity)}</div>
        </div>

        {/* Title */}
        <h3
          onClick={() => onSelect(complaint.id)}
          className="text-base font-bold text-slate-900 group-hover:text-primary-700 transition cursor-pointer line-clamp-2 mt-1 mb-2"
        >
          {complaint.title}
        </h3>

        {/* Description snippet */}
        <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed mb-4">
          {complaint.description}
        </p>

        {/* Location & Priority */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 mb-4 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
          <div className="flex items-center space-x-1.5 font-medium text-slate-700">
            <MapPin className="w-3.5 h-3.5 text-primary-600 shrink-0" />
            <span className="truncate max-w-[200px]">
              {complaint.upazila}, {complaint.district}
            </span>
          </div>

          <div className="flex items-center space-x-1">
            <span className="text-[11px] text-slate-400 font-medium">AI Priority:</span>
            <span className="text-xs font-extrabold text-primary-700 bg-primary-100/70 px-1.5 py-0.5 rounded">
              {complaint.ai_priority_score}/100
            </span>
          </div>
        </div>
      </div>

      {/* Footer row: Status, Upvote, Comments, Details */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
        <div>{getStatusBadge(complaint.status)}</div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onUpvote(complaint.id)}
            className="flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-primary-600 bg-slate-50 hover:bg-primary-50 border border-slate-200 hover:border-primary-300 px-2.5 py-1.5 rounded-lg transition"
            title="I am also affected by this issue"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
            <span>{complaint.upvotes_count}</span>
          </button>

          <button
            onClick={() => onSelect(complaint.id)}
            className="flex items-center space-x-1 text-xs font-semibold text-primary-600 hover:text-primary-700 hover:underline px-2 py-1.5"
          >
            <span>{lang === 'bn' ? 'বিস্তারিত' : 'View'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
