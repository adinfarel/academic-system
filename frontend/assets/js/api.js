/**
 * api.js — API Client untuk PolsriEduAI
 * Fetch wrapper dengan token management otomatis
 */

const API_BASE = 'http://localhost:8000';

// ── Token Management ──────────────────────────────────────────
function getToken() {
  return localStorage.getItem('polsri_token');
}

function setToken(token) {
  localStorage.setItem('polsri_token', token);
}

function removeToken() {
  localStorage.removeItem('polsri_token');
  localStorage.removeItem('polsri_user');
}

function getCachedUser() {
  const data = localStorage.getItem('polsri_user');
  return data ? JSON.parse(data) : null;
}

function setCachedUser(user) {
  localStorage.setItem('polsri_user', JSON.stringify(user));
}

// ── Core Request Function ─────────────────────────────────────
/**
 * Fetch wrapper yang otomatis inject Authorization header
 * dan handle error responses
 * 
 * @param {string} endpoint - API endpoint (tanpa base URL)
 * @param {Object} options - fetch options
 * @returns {Promise<Object>} Response data
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const headers = options.headers || {};
  
  // Inject token kalau ada
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Default content-type JSON kalau bukan FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 — redirect ke login
    if (response.status === 401) {
      removeToken();
      window.location.href = '/frontend/pages/login.html';
      throw new Error('Sesi habis, silakan login kembali');
    }

    // Handle error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `Error ${response.status}`;
      throw new Error(message);
    }

    // Parse JSON response
    return await response.json();
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Tidak bisa terhubung ke server. Pastikan backend berjalan.');
    }
    throw error;
  }
}

// ── Convenience Methods ───────────────────────────────────────

async function apiGet(endpoint) {
  return apiRequest(endpoint, { method: 'GET' });
}

async function apiPost(endpoint, data) {
  return apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

async function apiPut(endpoint, data) {
  return apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

async function apiDelete(endpoint) {
  return apiRequest(endpoint, { method: 'DELETE' });
}

/**
 * Upload file via FormData (untuk absensi, register face)
 * @param {string} endpoint
 * @param {FormData} formData
 * @returns {Promise<Object>}
 */
async function apiFormData(endpoint, formData) {
  return apiRequest(endpoint, {
    method: 'POST',
    body: formData,
    // Jangan set Content-Type — browser otomatis set boundary untuk multipart
  });
}

/**
 * Login — kirim sebagai OAuth2 form-data (bukan JSON)
 * @param {string} username
 * @param {string} password
 * @returns {Promise<Object>} Token response
 */
async function apiLogin(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login gagal');
  }

  const data = await response.json();
  
  // Simpan token dan info user
  setToken(data.access_token);
  setCachedUser({
    username: data.username,
    role: data.role,
  });

  return data;
}
