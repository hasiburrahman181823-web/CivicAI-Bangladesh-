import {
  ComplaintListItem,
  ComplaintDetail,
  AIPreviewResult,
  AdminStats,
  User
} from './types';

// Use the deployed Render API by default; VITE_API_URL can override it per environment.
const API_BASE = (import.meta.env.VITE_API_URL || 'https://civicai-bangladesh.onrender.com').replace(/\/+$/, '');

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('civicai_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchDivisions(): Promise<Record<string, { districts: Record<string, string[]> }>> {
  const res = await fetch(`${API_BASE}/api/complaints/divisions`);
  if (!res.ok) throw new Error('Failed to load administrative divisions');
  return res.json();
}

export async function previewAI(title: string, description: string): Promise<AIPreviewResult> {
  const res = await fetch(`${API_BASE}/api/complaints/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  });
  if (!res.ok) throw new Error('Failed to generate AI preview');
  return res.json();
}

export async function submitGuestComplaint(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/complaints/guest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to submit guest complaint' }));
    throw new Error(err.detail || 'Submission failed');
  }
  return res.json();
}

export async function submitAuthenticatedComplaint(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/complaints`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Submission failed' }));
    throw new Error(err.detail || 'Submission failed');
  }
  return res.json();
}

export async function trackComplaint(trackingId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/complaints/track/${encodeURIComponent(trackingId.trim())}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Complaint not found' }));
    throw new Error(err.detail || 'Complaint not found');
  }
  return res.json();
}

export async function fetchFeed(params: Record<string, any> = {}): Promise<ComplaintListItem[]> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== 'All' && v !== '') {
      query.append(k, String(v));
    }
  });
  const res = await fetch(`${API_BASE}/api/complaints/feed?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load complaints feed');
  return res.json();
}

export async function fetchMapMarkers(params: Record<string, any> = {}): Promise<any[]> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v && v !== 'All') query.append(k, String(v));
  });
  const res = await fetch(`${API_BASE}/api/complaints/map?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load map markers');
  return res.json();
}

export async function fetchComplaintDetails(id: number): Promise<ComplaintDetail> {
  const res = await fetch(`${API_BASE}/api/complaints/${id}`);
  if (!res.ok) throw new Error('Complaint not found');
  return res.json();
}

export async function upvoteComplaint(id: number): Promise<{ upvotes_count: number; has_upvoted: boolean }> {
  const res = await fetch(`${API_BASE}/api/complaints/${id}/upvote`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to toggle upvote');
  return res.json();
}

export async function addComment(id: number, commentText: string, authorName?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/complaints/${id}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ comment_text: commentText, author_name: authorName }),
  });
  if (!res.ok) throw new Error('Failed to post comment');
  return res.json();
}

export async function uploadFile(file: File): Promise<{ url: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

// ----------------- Auth API -----------------
export async function loginUser(email: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Invalid login' }));
    throw new Error(err.detail || 'Invalid login credentials');
  }
  const data = await res.json();
  localStorage.setItem('civicai_token', data.access_token);
  localStorage.setItem('civicai_user', JSON.stringify(data.user));
  return data;
}

export async function registerUser(email: string, fullName: string, password: string, phone?: string): Promise<{ access_token: string; user: User }> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, full_name: fullName, password, phone }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(err.detail || 'Registration failed');
  }
  const data = await res.json();
  localStorage.setItem('civicai_token', data.access_token);
  localStorage.setItem('civicai_user', JSON.stringify(data.user));
  return data;
}

export function logoutUser(): void {
  localStorage.removeItem('civicai_token');
  localStorage.removeItem('civicai_user');
}

export function getStoredUser(): User | null {
  const str = localStorage.getItem('civicai_user');
  if (!str) return null;
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

// ----------------- Admin API -----------------
export async function fetchAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${API_BASE}/api/admin/stats`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error('Failed to load admin statistics');
  return res.json();
}

export async function fetchAdminComplaints(params: Record<string, any> = {}): Promise<any[]> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v && v !== 'All') query.append(k, String(v));
  });
  const res = await fetch(`${API_BASE}/api/admin/complaints?${query.toString()}`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error('Failed to load admin complaints');
  return res.json();
}

export async function verifyComplaint(id: number, payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/admin/complaints/${id}/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to verify complaint');
  return res.json();
}

export async function assignComplaint(id: number, payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/admin/complaints/${id}/assign`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to assign complaint');
  return res.json();
}

export async function updateComplaintStatus(id: number, payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/api/admin/complaints/${id}/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update status');
  return res.json();
}

export async function mergeDuplicateComplaints(primaryId: number, duplicateId: number, reason?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/admin/complaints/merge-duplicates`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({
      primary_complaint_id: primaryId,
      duplicate_complaint_id: duplicateId,
      merge_reason: reason,
    }),
  });
  if (!res.ok) throw new Error('Failed to merge duplicates');
  return res.json();
}

export async function fetchAIMetrics(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/admin/ai-models/metrics`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error('Failed to fetch AI metrics');
  return res.json();
}

export async function fetchAuditLogs(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/admin/audit-logs`, {
    headers: { ...getAuthHeader() },
  });
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}
