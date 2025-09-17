// API base resolution order:
// 1. Explicit VITE_API_BASE (e.g. https://api.example.com)
// 2. Same origin (relative) if front-end served by backend ('' prefix)
// 3. Fallback dev default http://localhost:8000
const API_BASE = (import.meta.env.VITE_API_BASE && import.meta.env.VITE_API_BASE.trim())
  ? import.meta.env.VITE_API_BASE.trim().replace(/\/$/, '')
  : (window.location.port === '5173' ? 'http://localhost:8000' : '');

let adminAuthHeader = null;
export function setAdminAuth(user, pass) {
  if(!user || !pass) { adminAuthHeader = null; return; }
  adminAuthHeader = 'Basic ' + btoa(`${user}:${pass}`);
}
function authHeaders(extra={}) {
  return adminAuthHeader ? { ...extra, 'Authorization': adminAuthHeader } : extra;
}

export async function pingAdmin() {
  const r = await fetch(`${API_BASE}/admin/ping`, { headers: authHeaders() });
  if(!r.ok) throw new Error('unauthorized');
  return r.json();
}

export async function verifyAdmin() {
  const data = await pingAdmin();
  return data && data.ok;
}

export async function fetchRooms() {
  const r = await fetch(`${API_BASE}/rooms`);
  return r.json();
}

export async function fetchRoom(id) {
  const r = await fetch(`${API_BASE}/rooms/${id}`);
  if(!r.ok) throw new Error('Room not found');
  return r.json();
}

export async function fetchBookings(params = {}) {
  const query = new URLSearchParams(params).toString();
  const r = await fetch(`${API_BASE}/bookings${query?`?${query}`:''}`);
  return r.json();
}

export async function createBooking(data) {
  const r = await fetch(`${API_BASE}/bookings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}

export async function adminUpdateBooking(id, status) {
  const r = await fetch(`${API_BASE}/admin/bookings/${id}`, {
    method: 'PATCH',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ status })
  });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}

export async function adminDeleteBooking(id) {
  const r = await fetch(`${API_BASE}/admin/bookings/${id}`, { method: 'DELETE', headers: authHeaders() });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}

export async function fetchWeeklyRooms() {
  const url = `${API_BASE}/rooms/weekly`;
  console.log('[weekly] fetch start', { url });
  let r;
  try {
    r = await fetch(url, { headers: { 'Cache-Control': 'no-cache' } });
  } catch (e) {
    console.error('[weekly] network error', e);
    throw e;
  }
  console.log('[weekly] status', r.status);
  let data = null;
  try {
    data = await r.json();
  } catch (e) {
    console.error('[weekly] json parse error', e);
    throw e;
  }
  if(!r.ok) {
    console.error('[weekly] non-ok response', data);
    throw new Error(data && data.detail ? data.detail : 'weekly fetch failed');
  }
  console.log('[weekly] data length', Array.isArray(data) ? data.length : 'not-array', data);
  return data;
}

export async function createSemesterBookings(data) {
  const r = await fetch(`${API_BASE}/admin/semester_bookings`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data)
  });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}
