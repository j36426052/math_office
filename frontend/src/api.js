// API base resolution order:
// 1. Explicit VITE_API_BASE (e.g. https://api.example.com)
// 2. Same origin (relative) if front-end served by backend ('' prefix)
// 3. Fallback dev default http://localhost:8000
const API_BASE = (import.meta.env.VITE_API_BASE && import.meta.env.VITE_API_BASE.trim())
  ? import.meta.env.VITE_API_BASE.trim().replace(/\/$/, '')
  : (window.location.port === '5173' ? 'http://localhost:8000' : '');

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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}

export async function adminDeleteBooking(id) {
  const r = await fetch(`${API_BASE}/admin/bookings/${id}`, { method: 'DELETE' });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}

export async function fetchWeeklyRooms() {
  const r = await fetch(`${API_BASE}/rooms/weekly`);
  return r.json();
}

export async function createSemesterBookings(data) {
  const r = await fetch(`${API_BASE}/admin/semester_bookings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if(!r.ok) throw new Error((await r.json()).detail || 'Error');
  return r.json();
}
