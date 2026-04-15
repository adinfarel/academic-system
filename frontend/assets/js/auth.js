/**
 * auth.js — Authentication & Route Guards
 * PolsriEduAI
 */

// ── Get Current User ──────────────────────────────────────────
/**
 * Ambil profil user yang sedang login dari API
 * Cache di localStorage supaya tidak hit API tiap page load
 */
async function getCurrentUser() {
  const cached = getCachedUser();
  if (cached && cached.id) return cached;

  try {
    const user = await apiGet('/api/v1/auth/me');
    setCachedUser(user);
    return user;
  } catch (e) {
    return null;
  }
}

function isLoggedIn() {
  return !!getToken();
}

function getUserRole() {
  const user = getCachedUser();
  return user ? user.role : null;
}

// ── Route Guards ──────────────────────────────────────────────
/**
 * Proteksi halaman — redirect ke login kalau belum auth
 * @param {string[]} allowedRoles - Role yang boleh akses halaman ini
 */
async function requireAuth(allowedRoles = []) {
  if (!isLoggedIn()) {
    window.location.href = '/frontend/pages/login.html';
    return null;
  }

  const user = await getCurrentUser();
  if (!user) {
    removeToken();
    window.location.href = '/frontend/pages/login.html';
    return null;
  }

  // Cek role kalau di-specify
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    // Redirect ke dashboard yang benar
    redirectToDashboard(user.role);
    return null;
  }

  return user;
}

// ── Logout ────────────────────────────────────────────────────
function logout() {
  removeToken();
  window.location.href = '/frontend/pages/login.html';
}

// ── Dashboard Routing ─────────────────────────────────────────
/**
 * Redirect ke dashboard yang sesuai berdasarkan role
 */
function redirectToDashboard(role) {
  const routes = {
    'mahasiswa': '/frontend/pages/mahasiswa/dashboard.html',
    'dosen': '/frontend/pages/dosen/dashboard.html',
    'admin': '/frontend/pages/admin/dashboard.html',
  };

  const target = routes[role] || '/frontend/pages/login.html';
  window.location.href = target;
}

// ── Theme Management ──────────────────────────────────────────
function getTheme() {
  return localStorage.getItem('polsri_theme') || 'dark';
}

function setTheme(theme) {
  localStorage.setItem('polsri_theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
  // Update toggle icon
  const toggleBtn = document.querySelector('.theme-toggle');
  if (toggleBtn) {
    toggleBtn.textContent = theme === 'dark' ? '☀' : '☾';
  }
}

function toggleTheme() {
  const current = getTheme();
  setTheme(current === 'dark' ? 'light' : 'dark');
}

/**
 * Initialize theme on page load
 * Call this di setiap halaman
 */
function initTheme() {
  // Light mode only — no theme switching needed
}

// ── Sidebar State ─────────────────────────────────────────────
function initSidebar() {
  const toggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.mobile-overlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('active');
    });

    if (overlay) {
      overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
      });
    }
  }

  // Set active nav link
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') && currentPath.includes(link.getAttribute('href').replace(/^\//, ''))) {
      link.classList.add('active');
    }
  });
}

// ── Init Dashboard Page ───────────────────────────────────────
/**
 * Setup umum untuk semua halaman dashboard
 * Call di awal setiap dashboard page
 */
async function initDashboardPage(allowedRoles = []) {
  initTheme();
  initSidebar();

  const user = await requireAuth(allowedRoles);
  if (!user) return null;

  // Update sidebar user info
  const nameEl = document.querySelector('.sidebar-user-name');
  const roleEl = document.querySelector('.sidebar-user-role');
  const avatarEl = document.querySelector('.sidebar-user-avatar');

  if (nameEl) nameEl.textContent = user.username;
  if (roleEl) roleEl.textContent = user.role;
  if (avatarEl) avatarEl.textContent = user.username.charAt(0).toUpperCase();

  return user;
}
