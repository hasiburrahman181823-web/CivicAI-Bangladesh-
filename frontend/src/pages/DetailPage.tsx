import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  MapPin,
  ThumbsUp,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Building2,
  Calendar,
  Send,
  User as UserIcon
} from 'lucide-react';
import { fetchComplaintDetails, upvoteComplaint, addComment } from '../api';
import { ComplaintDetail, User } from '../types';

interface DetailPageProps {
  complaintId: number;
  onBack: () => void;
  currentUser: User | null;
  lang: 'en' | 'bn';
}

export const DetailPage: React.FC<DetailPageProps> = ({
  complaintId,
  onBack,
  currentUser,
  lang
}) => {
  const [complaint, setComplaint] = useState<ComplaintDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [authorName, setAuthorName] = useState(currentUser?.full_name || '');
  const [postingComment, setPostingComment] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchComplaintDetails(complaintId);
      setComplaint(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [complaintId]);

  const handleUpvote = async () => {
    if (!complaint) return;
    try {
      const res = await upvoteComplaint(complaint.id);
      setComplaint({ ...complaint, upvotes_count: res.upvotes_count });
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !complaint) return;
    setPostingComment(true);
    try {
      await addComment(complaint.id, commentText, authorName || 'Concerned Citizen');
      setCommentText('');
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setPostingComment(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-semibold">Loading complaint intelligence details...</p>
      </div>
    );
  }

  if (!complaint) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <p className="text-sm font-bold text-slate-800">Complaint not found.</p>
        <button onClick={onBack} className="text-xs font-bold text-primary-600 underline">Return to feed</button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Back button */}
      <button
        onClick={onBack}
        className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-600 hover:text-primary-600 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Complaints Feed</span>
      </button>

      {/* Main Detail Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold bg-slate-100 text-slate-600 px-3 py-1 rounded-md">
              #{complaint.tracking_id}
            </span>
            <span className="text-xs font-bold bg-primary-50 text-primary-700 px-3 py-1 rounded-full border border-primary-200">
              {complaint.category}
            </span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
              complaint.severity === 'Critical' ? 'bg-rose-100 text-rose-800' :
              complaint.severity === 'High' ? 'bg-amber-100 text-amber-800' :
              'bg-sky-100 text-sky-800'
            }`}>
              {complaint.severity} Severity
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleUpvote}
              className="flex items-center space-x-1.5 bg-primary-50 hover:bg-primary-100 text-primary-700 font-bold px-4 py-2 rounded-xl border border-primary-200 transition text-xs shadow-sm"
            >
              <ThumbsUp className="w-4 h-4" />
              <span>I am also affected ({complaint.upvotes_count})</span>
            </button>
          </div>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-tight">
          {complaint.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-1">
            <MapPin className="w-4 h-4 text-primary-600" />
            <span className="font-semibold text-slate-700">{complaint.upazila}, {complaint.district}</span>
            {complaint.area_name && <span>({complaint.area_name})</span>}
          </div>
          <div className="flex items-center space-x-1">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span>Reported on {new Date(complaint.created_at).toLocaleDateString()}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Building2 className="w-4 h-4 text-slate-400" />
            <span>Assigned: <strong>{complaint.assigned_department || 'Municipal Routing'}</strong></span>
          </div>
        </div>

        {/* Narrative Description */}
        <div className="text-sm text-slate-700 leading-relaxed font-normal whitespace-pre-line">
          {complaint.description}
        </div>

        {/* Photos Grid */}
        {complaint.image_urls && complaint.image_urls.length > 0 && (
          <div className="space-y-2 pt-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">Citizen Photographic Evidence:</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {complaint.image_urls.map((img, i) => (
                <div key={i} className="h-44 rounded-xl overflow-hidden border border-slate-200 bg-slate-100">
                  <img src={img} alt="evidence" className="w-full h-full object-cover hover:scale-105 transition duration-300" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Factor Attribution Card */}
        <div className="bg-primary-50/70 border border-primary-200 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-primary-800 font-bold text-xs uppercase">
              <Sparkles className="w-4 h-4 text-primary-600" />
              <span>CivicAI Decision Support & Explainability Factor Breakdown</span>
            </div>
            <span className="text-xs font-extrabold text-primary-800 bg-primary-100 px-2 py-0.5 rounded">
              Priority Score: {complaint.ai_priority_score}/100
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed">
            {lang === 'bn' && complaint.ai_explanation_bn ? complaint.ai_explanation_bn : complaint.ai_explanation_en}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-primary-200/60 text-[11px]">
            <div>
              <span className="text-slate-400 block">AI Category Confidence:</span>
              <strong className="text-slate-800">{Math.round((complaint.ai_category_confidence || 0.95) * 100)}%</strong>
            </div>
            <div>
              <span className="text-slate-400 block">Severity Confidence:</span>
              <strong className="text-slate-800">{Math.round((complaint.ai_severity_confidence || 0.92) * 100)}%</strong>
            </div>
            <div>
              <span className="text-slate-400 block">Target SLA Window:</span>
              <strong className="text-slate-800">{complaint.severity === 'Critical' ? '12-24 Hours' : '48 Hours'}</strong>
            </div>
            <div>
              <span className="text-slate-400 block">Human Officer Verification:</span>
              <strong className={complaint.admin_override ? 'text-amber-700' : 'text-emerald-700'}>
                {complaint.admin_override ? 'Adjusted by Officer' : 'AI Verified'}
              </strong>
            </div>
          </div>
        </div>

        {/* Resolution Evidence Box (Before/After) */}
        {complaint.status === 'Resolved' && (
          <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-4">
            <div className="flex items-center space-x-2 text-emerald-800 font-bold text-sm">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <span>Resolution Verified by Supervising Engineer</span>
            </div>
            <p className="text-xs text-emerald-900 leading-relaxed font-medium">
              {complaint.resolution_notes || 'All reported defects successfully repaired and validated on-site.'}
            </p>
            {complaint.resolution_image_urls && complaint.resolution_image_urls.length > 0 && (
              <div>
                <span className="text-[11px] font-bold text-emerald-800 block mb-2 uppercase">Official After-Resolution Evidence:</span>
                <div className="grid grid-cols-2 gap-3">
                  {complaint.resolution_image_urls.map((url, i) => (
                    <div key={i} className="h-40 rounded-xl overflow-hidden border border-emerald-300">
                      <img src={url} alt="after-repair" className="w-full h-full object-cover" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Timeline Stepper */}
        <div className="pt-4 border-t border-slate-100 space-y-3">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
            Official Case Timeline & Milestones
          </h3>
          <div className="space-y-2">
            {complaint.timeline.map((item, idx) => (
              <div key={idx} className="flex items-start space-x-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="w-2 h-2 rounded-full bg-primary-600 mt-1 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <strong className="text-slate-900 font-bold">{item.title}</strong>
                    <span className="text-[11px] text-slate-400">{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                  {item.description && <p className="text-slate-600 mt-0.5">{item.description}</p>}
                  <span className="text-[10px] text-slate-400 font-medium block mt-1">Responsible: {item.performed_by}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Public Discussion & Comments */}
        <div className="pt-6 border-t border-slate-100 space-y-6">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-bold text-slate-900">
              Community Discussion ({complaint.comments.length})
            </h3>
          </div>

          {/* Add Comment Form */}
          <form onSubmit={handleAddComment} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input
                type="text"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                placeholder="Your Name / Local Resident"
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-primary-600 bg-white"
              />
            </div>
            <textarea
              required
              rows={2}
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Join the discussion, add local context, or report current status..."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-primary-600 bg-white"
            />
            <button
              type="submit"
              disabled={postingComment}
              className="bg-primary-600 hover:bg-primary-700 text-white font-bold px-4 py-2 rounded-lg text-xs transition flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{postingComment ? 'Posting...' : 'Post Public Comment'}</span>
            </button>
          </form>

          {/* Comments List */}
          <div className="space-y-3">
            {complaint.comments.map((cm) => (
              <div key={cm.id} className="p-4 bg-white border border-slate-200 rounded-xl space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1.5">
                    <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                    <strong className="text-slate-800 font-bold">{cm.author_name}</strong>
                    {cm.is_official_response && (
                      <span className="bg-primary-100 text-primary-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        Official Authority Response
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {new Date(cm.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed pl-5">{cm.comment_text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
