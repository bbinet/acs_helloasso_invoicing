// API client - all calls go through apiFetch which adds credentials and base path

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, statusText: string, detail: string) {
    super(`${status} ${statusText}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<any> {
  const url = `/api${path}`;
  // Add X-Requested-With header for CSRF protection
  const headers = new Headers(options.headers as HeadersInit || {});
  headers.set('X-Requested-With', 'XMLHttpRequest');
  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, response.statusText, detail);
  }

  return response.json();
}

// Auth
export function login(password: string) {
  return apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
}

export function logout() {
  return apiFetch('/auth/logout', { method: 'POST' });
}

export function checkAuth() {
  return apiFetch('/auth/check');
}

// Members
export function getMembers(params?: Record<string, string>) {
  let path = '/members';
  if (params && Object.keys(params).length > 0) {
    const qs = new URLSearchParams(params).toString();
    path += `?${qs}`;
  }
  return apiFetch(path);
}

export function getMember(memberId: string) {
  return apiFetch(`/members/${memberId}`);
}

export function exportCSV(params?: Record<string, string>) {
  let path = '/members/export/csv';
  if (params && Object.keys(params).length > 0) {
    const qs = new URLSearchParams(params).toString();
    path += `?${qs}`;
  }
  return apiFetch(path);
}

// Campaigns

export function refreshCampaigns() {
  return apiFetch('/campaigns/refresh', { method: 'POST' });
}

// Summary
export function getSummary() {
  return apiFetch('/summary');
}

// Invoices
export function generateInvoice(memberId: string) {
  return apiFetch(`/invoices/${memberId}/generate`, { method: 'POST' });
}

export function batchGenerateInvoices(memberIds?: number[]) {
  const params = memberIds ? `?${memberIds.map(id => `member_ids=${id}`).join('&')}` : '';
  return apiFetch(`/invoices/batch${params}`, { method: 'POST' });
}

export function getBatchInvoiceStatus(jobId: string) {
  return apiFetch(`/invoices/batch/${jobId}/status`);
}

export function cancelBatchInvoices(jobId: string) {
  return apiFetch(`/invoices/batch/${jobId}/cancel`, { method: 'POST' });
}

export function deleteInvoice(memberId: string) {
  return apiFetch(`/invoices/${memberId}`, { method: 'DELETE' });
}

export function downloadInvoice(memberId: string) {
  return apiFetch(`/invoices/${memberId}/download`);
}

// Emails
export function sendEmail(memberId: string) {
  return apiFetch(`/emails/${memberId}/send`, { method: 'POST' });
}

export function batchSendEmails(memberIds?: number[]) {
  const params = memberIds ? `?${memberIds.map(id => `member_ids=${id}`).join('&')}` : '';
  return apiFetch(`/emails/batch${params}`, { method: 'POST' });
}

export function getBatchEmailStatus(jobId: string) {
  return apiFetch(`/emails/batch/${jobId}/status`);
}

export function cancelBatchEmails(jobId: string) {
  return apiFetch(`/emails/batch/${jobId}/cancel`, { method: 'POST' });
}
