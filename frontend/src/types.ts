export interface User {
  id: number;
  email: string;
  phone?: string;
  full_name: string;
  role: 'citizen' | 'officer' | 'admin';
  department?: string;
  created_at?: string;
}

export interface TimelineItem {
  id: number;
  status: string;
  title: string;
  description?: string;
  performed_by: string;
  created_at: string;
}

export interface CommentItem {
  id: number;
  author_name: string;
  comment_text: string;
  is_official_response: boolean;
  created_at: string;
}

export interface ComplaintListItem {
  id: number;
  tracking_id: string;
  title: string;
  description: string;
  category: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'Submitted' | 'AI_Analyzed' | 'Verified' | 'Assigned' | 'In_Progress' | 'Resolved' | 'Rejected' | 'Duplicate_Merged';
  division: string;
  district: string;
  upazila: string;
  area_name?: string;
  latitude?: number;
  longitude?: number;
  ai_priority_score: number;
  ai_priority_level: 'Critical' | 'High' | 'Medium' | 'Low';
  upvotes_count: number;
  comments_count: number;
  image_urls: string[];
  created_at: string;
  assigned_department?: string;
}

export interface ComplaintDetail extends ComplaintListItem {
  is_guest: boolean;
  is_anonymous: boolean;
  assigned_officer?: string;
  sla_deadline?: string;
  ai_category?: string;
  ai_category_confidence?: number;
  ai_severity?: string;
  ai_severity_confidence?: number;
  ai_urgency_score: number;
  ai_urgency_keywords: string[];
  ai_explanation_en?: string;
  ai_explanation_bn?: string;
  admin_override: boolean;
  admin_override_reason?: string;
  resolution_notes?: string;
  resolution_image_urls: string[];
  resolved_at?: string;
  updated_at: string;
  timeline: TimelineItem[];
  comments: CommentItem[];
}

export interface AIPreviewResult {
  language: string;
  predicted_category: string;
  category_confidence: number;
  top_categories: Array<{ category: string; confidence: number }>;
  predicted_severity: string;
  severity_confidence: number;
  top_severities: Array<{ severity: string; confidence: number }>;
  urgency_score: number;
  urgency_keywords: string[];
  estimated_priority_score: number;
  priority_level: string;
  potential_duplicates: Array<{
    complaint_id: number;
    tracking_id: string;
    title: string;
    status: string;
    category: string;
    severity: string;
    semantic_similarity: number;
    distance_km?: number;
    match_score: number;
    is_likely_duplicate: boolean;
  }>;
  is_duplicate_flagged: boolean;
  recommended_department: string;
  recommended_department_bn: string;
}

export interface AdminStats {
  total_complaints: number;
  pending_complaints: number;
  verified_complaints: number;
  in_progress_complaints: number;
  resolved_complaints: number;
  critical_complaints: number;
  resolution_rate_percent: number;
  avg_priority_score: number;
  category_distribution: Record<string, number>;
  division_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
}
