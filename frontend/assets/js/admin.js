/* =========================================================
   Lost & Found AI — logic trang quản trị
   ========================================================= */

const API = '/api';
const token = () => localStorage.getItem('token');
const $  = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function escapeHtml(s = '') {
  return String(s).replace(/[&<>'"]/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[c]));
}

function msg(text, type = 'info') {
  $('#message').innerHTML = `<div class="alert alert-${type} alert-dismissible">
    ${escapeHtml(text)}<button class="btn-close" data-bs-dismiss="alert"></button></div>`;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  setTimeout(() => { $('#message').innerHTML = ''; }, 5000);
}

function fmtDate(v) {
  if (!v) return '';
  const d = new Date(String(v).replace(' ', 'T'));
  return isNaN(d) ? String(v) : d.toLocaleDateString('vi-VN');
}

async function api(path, opt = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token()) headers['Authorization'] = 'Bearer ' + token();

  const res  = await fetch(API + path, { ...opt, headers: { ...headers, ...(opt.headers || {}) } });
  const json = await res.json().catch(() => ({}));

  if (res.status === 401) {
    localStorage.removeItem('token');
    location.href = '/frontend/index.html';
    throw new Error('Phiên đăng nhập đã hết hạn');
  }
  if (!res.ok) throw new Error(json.message || 'Có lỗi xảy ra');
  return json.data;
}

/* ---------------- Thống kê ---------------- */

const STAT_CARDS = [
  ['total_users',       'Người dùng',        'primary'],
  ['total_posts',       'Bài đăng',          'dark'],
  ['open_posts',        'Đang mở',           'success'],
  ['total_matches',     'Cặp so khớp',       'info'],
  ['pending_matches',   'Chờ xác nhận',      'warning'],
  ['confirmed_matches', 'Đã xác nhận',       'success'],
  ['total_categories',  'Danh mục',          'secondary'],
  ['total_images',      'Ảnh đã tải',        'secondary'],
];

async function loadStats() {
  try {
    const s = await api('/admin/stats');
    $('#stats').innerHTML = STAT_CARDS.map(([key, label, color]) =>
      `<div class="col-6 col-md-3">
        <div class="card shadow-sm border-${color}">
          <div class="card-body py-3">
            <div class="text-muted small">${label}</div>
            <div class="fs-3 fw-semibold text-${color}">${Number(s[key] ?? 0).toLocaleString('vi-VN')}</div>
          </div>
        </div>
      </div>`).join('');
  } catch (e) { msg(e.message, 'danger'); }
}

/* ---------------- Người dùng ---------------- */

async function loadUsers() {
  $('#userRows').innerHTML = '<tr><td colspan="10" class="text-muted">Đang tải...</td></tr>';
  try {
    const rows = await api('/admin/users');
    $('#userRows').innerHTML = rows.map(u => {
      const active  = Number(u.status) === 1;
      const isAdmin = u.role === 'ADMIN';
      return `<tr>
        <td>${u.id}</td>
        <td>${escapeHtml(u.full_name)}</td>
        <td>${escapeHtml(u.username)}</td>
        <td>${escapeHtml(u.email)}</td>
        <td>${escapeHtml(u.phone || '—')}</td>
        <td><span class="badge text-bg-${isAdmin ? 'warning' : 'light'} ${isAdmin ? '' : 'text-dark'}">${u.role}</span></td>
        <td class="text-center">${u.post_count}</td>
        <td>${fmtDate(u.created_at)}</td>
        <td><span class="badge text-bg-${active ? 'success' : 'danger'}">${active ? 'Hoạt động' : 'Đã khóa'}</span></td>
        <td class="text-end">${isAdmin ? '' :
          `<button class="btn btn-sm btn-outline-${active ? 'danger' : 'success'}"
                   data-user="${u.id}" data-status="${active ? 0 : 1}">
             ${active ? 'Khóa' : 'Mở khóa'}
           </button>`}</td>
      </tr>`;
    }).join('');
  } catch (e) {
    $('#userRows').innerHTML = `<tr><td colspan="10" class="text-danger">${escapeHtml(e.message)}</td></tr>`;
  }
}

/* ---------------- Danh mục ---------------- */

async function loadCategories() {
  $('#catRows').innerHTML = '<tr><td colspan="6" class="text-muted">Đang tải...</td></tr>';
  try {
    const rows = await api('/admin/categories');
    $('#catRows').innerHTML = rows.map(c => {
      const active = Number(c.status) === 1;
      return `<tr>
        <td>${c.id}</td>
        <td><input class="form-control form-control-sm" value="${escapeHtml(c.name)}" data-cat-name="${c.id}"></td>
        <td><input class="form-control form-control-sm" value="${escapeHtml(c.description || '')}" data-cat-desc="${c.id}"></td>
        <td class="text-center">${c.post_count}</td>
        <td><span class="badge text-bg-${active ? 'success' : 'secondary'}">${active ? 'Hiện' : 'Ẩn'}</span></td>
        <td class="text-end text-nowrap">
          <button class="btn btn-sm btn-outline-primary" data-cat-save="${c.id}">Lưu</button>
          <button class="btn btn-sm btn-outline-${active ? 'secondary' : 'success'}"
                  data-cat-toggle="${c.id}" data-status="${active ? 0 : 1}">${active ? 'Ẩn' : 'Hiện'}</button>
        </td>
      </tr>`;
    }).join('');
  } catch (e) {
    $('#catRows').innerHTML = `<tr><td colspan="6" class="text-danger">${escapeHtml(e.message)}</td></tr>`;
  }
}

/* ---------------- Bài đăng ---------------- */

async function loadPosts() {
  $('#postRows').innerHTML = '<tr><td colspan="10" class="text-muted">Đang tải...</td></tr>';
  const params = new URLSearchParams({
    q:         $('#pq').value,
    post_type: $('#pType').value,
    status:    $('#pStatus').value
  });
  try {
    const rows = await api('/admin/posts?' + params.toString());
    if (!rows.length) {
      $('#postRows').innerHTML = '<tr><td colspan="10" class="text-muted">Không có bài đăng phù hợp.</td></tr>';
      return;
    }
    $('#postRows').innerHTML = rows.map(p => `<tr>
      <td>${p.id}</td>
      <td><span class="badge ${p.post_type === 'LOST' ? 'badge-lost' : 'badge-found'}">${p.post_type}</span></td>
      <td>${escapeHtml(p.title)}</td>
      <td>${escapeHtml(p.category_name)}</td>
      <td>${escapeHtml(p.owner_name)}</td>
      <td>${escapeHtml(p.location)}</td>
      <td class="text-center">${p.image_count}</td>
      <td><span class="badge text-bg-${p.status === 'OPEN' ? 'primary' : 'secondary'}">${p.status}</span></td>
      <td>${fmtDate(p.created_at)}</td>
      <td class="text-end"><button class="btn btn-sm btn-outline-danger" data-del-post="${p.id}">Xóa</button></td>
    </tr>`).join('');
  } catch (e) {
    $('#postRows').innerHTML = `<tr><td colspan="10" class="text-danger">${escapeHtml(e.message)}</td></tr>`;
  }
}

/* ---------------- Chuyển tab ---------------- */

$$('[data-tab]').forEach(btn => {
  btn.onclick = () => {
    $$('[data-tab]').forEach(b => b.classList.toggle('active', b === btn));
    ['users', 'categories', 'posts'].forEach(t =>
      $('#tab-' + t).classList.toggle('d-none', t !== btn.dataset.tab));
    if (btn.dataset.tab === 'users')      loadUsers();
    if (btn.dataset.tab === 'categories') loadCategories();
    if (btn.dataset.tab === 'posts')      loadPosts();
  };
});

/* ---------------- Sự kiện ---------------- */

$('#btnLogout').onclick = () => {
  localStorage.removeItem('token');
  location.href = '/frontend/index.html';
};

$('#pSearch').onclick = loadPosts;

$('#catForm').onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  try {
    await api('/admin/categories', { method: 'POST', body: JSON.stringify(data) });
    e.target.reset();
    msg('Đã thêm danh mục mới', 'success');
    loadCategories();
    loadStats();
  } catch (x) { msg(x.message, 'danger'); }
};

document.addEventListener('click', async (e) => {
  /* Khóa / mở khóa người dùng */
  const userBtn = e.target.closest('[data-user]');
  if (userBtn) {
    const status = Number(userBtn.dataset.status);
    if (!confirm(status ? 'Mở khóa tài khoản này?' : 'Khóa tài khoản này? Người dùng sẽ không đăng nhập được.')) return;
    try {
      await api(`/admin/users/${userBtn.dataset.user}/status`, {
        method: 'PATCH', body: JSON.stringify({ status })
      });
      msg(status ? 'Đã mở khóa tài khoản' : 'Đã khóa tài khoản', 'success');
      loadUsers();
      loadStats();
    } catch (x) { msg(x.message, 'danger'); }
    return;
  }

  /* Lưu chỉnh sửa danh mục */
  const saveBtn = e.target.closest('[data-cat-save]');
  if (saveBtn) {
    const id = saveBtn.dataset.catSave;
    const body = {
      name:        $(`[data-cat-name="${id}"]`).value,
      description: $(`[data-cat-desc="${id}"]`).value
    };
    try {
      await api(`/admin/categories/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
      msg('Đã cập nhật danh mục', 'success');
      loadCategories();
    } catch (x) { msg(x.message, 'danger'); }
    return;
  }

  /* Ẩn / hiện danh mục */
  const toggleBtn = e.target.closest('[data-cat-toggle]');
  if (toggleBtn) {
    try {
      await api(`/admin/categories/${toggleBtn.dataset.catToggle}`, {
        method: 'PATCH', body: JSON.stringify({ status: Number(toggleBtn.dataset.status) })
      });
      loadCategories();
    } catch (x) { msg(x.message, 'danger'); }
    return;
  }

  /* Xóa bài đăng */
  const delBtn = e.target.closest('[data-del-post]');
  if (delBtn) {
    if (!confirm('Xóa vĩnh viễn bài đăng này? Ảnh và các kết quả so khớp liên quan cũng sẽ bị xóa theo.')) return;
    try {
      await api(`/admin/posts/${delBtn.dataset.delPost}`, { method: 'DELETE' });
      msg('Đã xóa bài đăng', 'success');
      loadPosts();
      loadStats();
    } catch (x) { msg(x.message, 'danger'); }
  }
});

/* ---------------- Khởi động: kiểm tra quyền ---------------- */

(async () => {
  if (!token()) { location.href = '/frontend/index.html'; return; }
  try {
    const me = await api('/auth/me');
    if (!me || me.role !== 'ADMIN') {
      $('#denied').classList.remove('d-none');
      return;
    }
    $('#adminLabel').textContent = me.full_name;
    $('#panel').classList.remove('d-none');
    await loadStats();
    await loadUsers();
  } catch (e) {
    $('#denied').classList.remove('d-none');
  }
})();
