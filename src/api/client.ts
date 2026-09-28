import { ComplaintCreate, ComplaintResponse, ComplaintListResponse, StatsResponse, ProviderInfo, Status } from '../types';

/**
 * Custom application error encapsulating HTTP status codes and API error messages.
 * Preserves backend response codes (e.g. 409 status transitions, 429 rate limits).
 */
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}


async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = 'API Error';
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      message = await response.text() || message;
    }
    throw new ApiError(response.status, message);
  }

  return response.json();
}

export const createComplaint = (data: ComplaintCreate): Promise<ComplaintResponse> => 
  fetchApi<ComplaintResponse>('/api/complaints', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getComplaint = (id: string): Promise<ComplaintResponse> => 
  fetchApi<ComplaintResponse>(`/api/complaints/${id}`);

export const listComplaints = (
  page = 1,
  pageSize = 10,
  category?: string,
  priority?: string,
  status?: string
): Promise<ComplaintListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (category) params.append('category', category);
  if (priority) params.append('priority', priority);
  if (status) params.append('status', status);
  
  return fetchApi<ComplaintListResponse>(`/api/complaints?${params.toString()}`);
};

export const updateStatus = (id: string, status: Status): Promise<ComplaintResponse> => 
  fetchApi<ComplaintResponse>(`/api/complaints/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

export const getStats = async (): Promise<{ data: StatsResponse; cacheStatus: string | null }> => {
  const response = await fetch('/api/stats');
  if (!response.ok) {
    throw new ApiError(response.status, 'Failed to fetch stats');
  }
  const cacheStatus = response.headers.get('X-Cache');
  const data = await response.json();
  return { data, cacheStatus };
};

export const getProviders = (): Promise<ProviderInfo> => 
  fetchApi<ProviderInfo>('/api/providers');
