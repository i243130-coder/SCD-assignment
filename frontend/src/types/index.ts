export type Category = 'water' | 'electricity' | 'sanitation' | 'roads' | 'streetlights' | 'other';
export type Priority = 'high' | 'normal' | 'low';
export type Status = 'open' | 'in_progress' | 'resolved' | 'rejected';

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string | null;
}

export interface ComplaintResponse {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: Category;
  priority: Priority;
  status: Status;
  ai_summary: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintListResponse {
  items: ComplaintResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface StatsResponse {
  categories: { category: string; count: number }[];
  priorities: { priority: string; count: number }[];
  total: number;
}

export interface ProviderInfo {
  active_provider: string;
  recent_triages: {
    provider: string;
    latency_ms: number;
    fallback: boolean;
    created_at: string;
  }[];
}
