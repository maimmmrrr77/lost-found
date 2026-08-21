/* =========================================================
   Lost & Found AI — logic giao diện người dùng
   ========================================================= */

const API = '/api';
const PLACEHOLDER = 'https://placehold.co/600x400?text=No+Image';

const loginModal    = new bootstrap.Modal('#loginModal');
const adminLoginModal = new bootstrap.Modal('#adminLoginModal');
const registerModal = new bootstrap.Modal('#registerModal');
const postModal     = new bootstrap.Modal('#postModal');
const uploadModal   = new bootstrap.Modal('#uploadModal');

let currentUser = null;

/* ---------------- Tiện ích ---------------- */

const token = () => localStorage.getItem('token');
const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

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
  return isNaN(d) ? String(v) : d.toLocaleString('vi-VN');
}

function fmtMoney(v) {
  const n = Number(v || 0);
  return n > 0 ? n.toLocaleString('vi-VN') + ' đ' : '';
}

/* Gọi API. Với FormData thì KHÔNG đặt Content-Type để trình duyệt tự sinh boundary. */
async function api(path, opt = {}) {
  const headers = {};
  if (token()) headers['Authorization'] = 'Bearer ' + token();
  if (!(opt.body instanceof FormData)) headers['Content-Type'] = 'application/json';

  const res  = await fetch(API + path, { ...opt, headers: { ...headers, ...(opt.headers || {}) } });
  const json = await res.json().catch(() => ({}));

  if (res.status === 401 && token()) {
    localStorage.removeItem('token');
    currentUser = null;
    authUi();
    throw new Error('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại');
  }
  if (!res.ok) throw new Error(json.message || 'Có lỗi xảy ra');
  return json.data;
}

/* ---------------- Điều hướng giữa các màn hình ---------------- */

const VIEWS = ['home', 'detail', 'mine', 'matches', 'notifications'];

function showView(name) {
  VIEWS.forEach(v => $('#view-' + v).classList.toggle('d-none', v !== name));
  if (name === 'mine')          loadMyPosts();
  if (name === 'matches')       loadMatches();
  if (name === 'notifications') loadNotifications();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-view]');
  if (!el) return;
  e.preventDefault();
  const view = el.dataset.view;
  if (view !== 'home' && !token()) { loginModal.show(); return; }
  showView(view);
});

/* ---------------- Trạng thái đăng nhập ---------------- */

function authUi() {
  const logged  = !!token();
  const isAdmin = currentUser && currentUser.role === 'ADMIN';

  $('#btnLogin').classList.toggle('d-none', logged);
  $('#btnAdminLogin').classList.toggle('d-none', logged);
  $('#btnRegister').classList.toggle('d-none', logged);
  $('#btnLogout').classList.toggle('d-none', !logged);
  $$('.auth-only').forEach(el => el.classList.toggle('d-none', !logged));
  $$('.admin-only').forEach(el => el.classList.toggle('d-none', !isAdmin));

  const label = $('#userLabel');
  label.classList.toggle('d-none', !logged || !currentUser);
  if (currentUser) label.textContent = currentUser.full_name;

  if (!logged) {
    $('#matchBadge').classList.add('d-none');
    $('#notifBadge').classList.add('d-none');
  }
}

async function loadMe() {
  if (!token()) { currentUser = null; authUi(); return; }
  try {
    currentUser = await api('/auth/me');
  } catch {
    currentUser = null;
  }
  authUi();
  if (currentUser) refreshBadges();
}

async function refreshBadges() {
  try {
    const [matches, notifs] = await Promise.all([
      api('/matches/mine'),
      api('/notifications')
    ]);
    const pending = (matches || []).filter(m => m.status === 'PENDING').length;
    const unread  = (notifs  || []).filter(n => Number(n.is_read) === 0).length;

    $('#matchBadge').textContent = pending;
    $('#matchBadge').classList.toggle('d-none', pending === 0);
    $('#notifBadge').textContent = unread;
    $('#notifBadge').classList.toggle('d-none', unread === 0);
  } catch { /* im lặng, không làm phiền người dùng */ }
}

/* ---------------- Danh mục ---------------- */

async function loadCategories() {
  try {
    const rows = await api('/categories');
    const opts = rows.map(x => `<option value="${x.id}">${escapeHtml(x.name)}</option>`).join('');
    $('#category').innerHTML = opts;
    $('#filterCategory').innerHTML = '<option value="">Tất cả danh mục</option>' + opts;
  } catch (e) { msg(e.message, 'danger'); }
}

/* ---------------- Trang chủ: danh sách bài đăng ---------------- */

function postCard(p, opts = {}) {
  const badge = p.post_type === 'LOST' ? 'badge-lost' : 'badge-found';
  const label = p.post_type === 'LOST' ? 'Bị mất' : 'Nhặt được';
  const img   = p.primary_image || PLACEHOLDER;

  const statusBadge = opts.showStatus
    ? `<span class="badge text-bg-${p.status === 'OPEN' ? 'primary' : 'secondary'} ms-1">${escapeHtml(p.status)}</span>`
    : '';

  const actions = opts.owner ? `
    <div class="d-flex gap-2 mt-2">
      <button class="btn btn-sm btn-outline-secondary flex-fill" data-upload="${p.id}">Thêm ảnh</button>
      ${p.status === 'OPEN' ? `<button class="btn btn-sm btn-outline-danger flex-fill" data-close="${p.id}">Đóng bài</button>` : ''}
    </div>` : '';

  return `<div class="col-md-4">
    <div class="card shadow-sm">
      <img class="card-img-top post-img" src="${escapeHtml(img)}" alt="">
      <div class="card-body d-flex flex-column">
        <div>
          <span class="badge ${badge}">${label}</span>
          <span class="badge text-bg-secondary ms-1">${escapeHtml(p.category_name || '')}</span>
          ${statusBadge}
        </div>
        <h5 class="mt-2">${escapeHtml(p.title)}</h5>
        <p class="truncate text-muted small">${escapeHtml(p.description || '')}</p>
        <small class="text-muted">${escapeHtml(p.location)} · ${fmtDate(p.event_date)}</small>
        <div class="mt-auto pt-2">
          <button class="btn btn-sm btn-primary w-100" data-detail="${p.id}">Xem chi tiết</button>
          ${actions}
        </div>
      </div>
    </div>
  </div>`;
}

async function loadPosts() {
  const params = new URLSearchParams({
    q:           $('#q').value,
    post_type:   $('#type').value,
    category_id: $('#filterCategory').value
  });
  try {
    const rows = await api('/posts?' + params.toString());
    $('#posts').innerHTML = rows.length
      ? rows.map(p => postCard(p)).join('')
      : '<div class="col-12"><div class="alert alert-light border">Chưa có bài đăng phù hợp.</div></div>';
  } catch (e) { msg(e.message, 'danger'); }
}

/* ---------------- Chi tiết bài đăng ---------------- */

async function loadDetail(id) {
  showView('detail');
  $('#detailBody').innerHTML = '<p class="text-muted">Đang tải...</p>';
  try {
    const p      = await api('/posts/' + id);
    const images = p.images || [];
    const isMine = currentUser && Number(p.user_id) === Number(currentUser.id);

    const gallery = images.length
      ? `<div class="row g-2 mb-3">${images.map(i =>
          `<div class="col-4"><img src="${escapeHtml(i.image_path)}" class="img-fluid rounded border" alt=""></div>`
        ).join('')}</div>`
      : `<div class="alert alert-light border">Bài đăng này chưa có ảnh.</div>`;

    const row = (label, value) => value
      ? `<tr><th class="text-muted fw-normal" style="width:170px">${label}</th><td>${escapeHtml(value)}</td></tr>`
      : '';

    $('#detailBody').innerHTML = `
      <div class="card shadow-sm">
        <div class="card-body">
          <div class="mb-2">
            <span class="badge ${p.post_type === 'LOST' ? 'badge-lost' : 'badge-found'}">
              ${p.post_type === 'LOST' ? 'Bị mất' : 'Nhặt được'}</span>
            <span class="badge text-bg-secondary ms-1">${escapeHtml(p.category_name)}</span>
            <span class="badge text-bg-${p.status === 'OPEN' ? 'primary' : 'secondary'} ms-1">${escapeHtml(p.status)}</span>
          </div>
          <h3>${escapeHtml(p.title)}</h3>
          <p>${escapeHtml(p.description)}</p>
          ${gallery}
          <table class="table table-sm">
            ${row('Màu sắc', p.color)}
            ${row('Thương hiệu', p.brand)}
            ${row('Địa điểm', p.location)}
            ${row('Thời gian', fmtDate(p.event_date))}
            ${row('Người đăng', p.owner_name)}
            ${row('Liên hệ', p.contact)}
            ${row('Mức thưởng', fmtMoney(p.reward))}
            ${row('Ngày đăng', fmtDate(p.created_at))}
          </table>
          ${isMine ? `<button class="btn btn-outline-secondary btn-sm" data-upload="${p.id}">Thêm ảnh</button>` : ''}
        </div>
      </div>`;
  } catch (e) {
    $('#detailBody').innerHTML = `<div class="alert alert-danger">${escapeHtml(e.message)}</div>`;
  }
}

/* ---------------- Bài đăng của tôi ---------------- */

async function loadMyPosts() {
  $('#minePosts').innerHTML = '<div class="col-12 text-muted">Đang tải...</div>';
  try {
    const rows = await api('/posts/mine');
    $('#minePosts').innerHTML = rows.length
      ? rows.map(p => postCard(p, { owner: true, showStatus: true })).join('')
      : '<div class="col-12"><div class="alert alert-light border">Bạn chưa đăng bài nào.</div></div>';
  } catch (e) {
    $('#minePosts').innerHTML = `<div class="col-12"><div class="alert alert-danger">${escapeHtml(e.message)}</div></div>`;
  }
}

/* ---------------- Gợi ý so khớp AI ---------------- */

function scoreColor(s) {
  if (s >= 0.85) return 'success';
  if (s >= 0.75) return 'primary';
  return 'warning';
}

async function loadMatches() {
  $('#matchList').innerHTML = '<p class="text-muted">Đang tải...</p>';
  try {
    const rows = await api('/matches/mine');
    if (!rows.length) {
      $('#matchList').innerHTML = '<div class="alert alert-light border">Chưa có gợi ý nào. Hệ thống sẽ tự động thông báo khi tìm thấy bài đăng tương đồng.</div>';
      return;
    }

    $('#matchList').innerHTML = rows.map(m => {
      const pct    = (Number(m.similarity_score) * 100).toFixed(1);
      const color  = scoreColor(Number(m.similarity_score));
      const status = { PENDING: 'Chờ xác nhận', CONFIRMED: 'Đã xác nhận', REJECTED: 'Đã từ chối' }[m.status] || m.status;
      const statusColor = { PENDING: 'warning', CONFIRMED: 'success', REJECTED: 'secondary' }[m.status] || 'secondary';

      const isLostOwner = currentUser && Number(m.lost_user_id) === Number(currentUser.id);
      const buttons = m.status === 'PENDING' ? `
        <div class="d-flex gap-2 mt-3">
          ${isLostOwner ? `<button class="btn btn-success btn-sm" data-match="${m.id}" data-status="CONFIRMED">Đúng là đồ của tôi</button>` : ''}
          <button class="btn btn-outline-secondary btn-sm" data-match="${m.id}" data-status="REJECTED">Không phải</button>
        </div>` : '';

      return `<div class="card shadow-sm mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <span class="badge text-bg-${statusColor}">${status}</span>
              <span class="badge text-bg-light text-dark ms-1">Mô hình: ${escapeHtml(m.ai_model)}</span>
            </div>
            <span class="badge text-bg-${color} fs-6">Tương đồng ${pct}%</span>
          </div>
          <div class="progress mt-2" style="height:6px">
            <div class="progress-bar bg-${color}" style="width:${pct}%"></div>
          </div>
          <div class="row g-3 mt-1">
            <div class="col-md-6">
              <div class="border rounded p-2 h-100">
                <span class="badge badge-lost">Bị mất</span>
                <div class="mt-1">${escapeHtml(m.lost_title)}</div>
                <button class="btn btn-link btn-sm px-0" data-detail="${m.lost_post_id}">Xem chi tiết</button>
              </div>
            </div>
            <div class="col-md-6">
              <div class="border rounded p-2 h-100">
                <span class="badge badge-found">Nhặt được</span>
                <div class="mt-1">${escapeHtml(m.found_title)}</div>
                <button class="btn btn-link btn-sm px-0" data-detail="${m.found_post_id}">Xem chi tiết</button>
              </div>
            </div>
          </div>
          ${buttons}
        </div>
      </div>`;
    }).join('');
  } catch (e) {
    $('#matchList').innerHTML = `<div class="alert alert-danger">${escapeHtml(e.message)}</div>`;
  }
}

/* ---------------- Thông báo ---------------- */

async function loadNotifications() {
  $('#notifList').innerHTML = '<p class="text-muted">Đang tải...</p>';
  try {
    const rows = await api('/notifications');
    if (!rows.length) {
      $('#notifList').innerHTML = '<div class="alert alert-light border">Bạn chưa có thông báo nào.</div>';
      return;
    }
    $('#notifList').innerHTML = rows.map(n => {
      const unread = Number(n.is_read) === 0;
      return `<div class="list-group-item ${unread ? 'list-group-item-warning' : ''}">
        <div class="d-flex justify-content-between align-items-start gap-2">
          <div>
            <div class="fw-semibold">${escapeHtml(n.title)} ${unread ? '<span class="badge text-bg-danger">Mới</span>' : ''}</div>
            <div class="small">${escapeHtml(n.content)}</div>
            <small class="text-muted">${fmtDate(n.created_at)}</small>
          </div>
          ${unread ? `<button class="btn btn-sm btn-outline-primary" data-read="${n.id}">Đã đọc</button>` : ''}
        </div>
      </div>`;
    }).join('');
  } catch (e) {
    $('#notifList').innerHTML = `<div class="alert alert-danger">${escapeHtml(e.message)}</div>`;
  }
}

/* ---------------- Tải ảnh ---------------- */

async function uploadImages(postId, fileList) {
  const files = Array.from(fileList || []);
  let ok = 0, fail = 0;

  for (const file of files) {
    if (file.size > 5 * 1024 * 1024) { fail++; continue; }
    const fd = new FormData();
    fd.append('image', file);
    try {
      await api(`/posts/${postId}/images`, { method: 'POST', body: fd });
      ok++;
    } catch { fail++; }
  }
  return { ok, fail, total: files.length };
}

/* ---------------- Sự kiện ---------------- */

$('#btnSearch').onclick  = loadPosts;
$('#q').addEventListener('keydown', e => { if (e.key === 'Enter') loadPosts(); });
$('#btnLogin').onclick    = () => loginModal.show();
$('#btnAdminLogin').onclick = () => adminLoginModal.show();
$('#btnRegister').onclick = () => registerModal.show();
$('#switchToRegister').onclick = () => { loginModal.hide(); registerModal.show(); };
$('#switchToLogin').onclick    = () => { registerModal.hide(); loginModal.show(); };

$('#btnLogout').onclick = () => {
  localStorage.removeItem('token');
  currentUser = null;
  authUi();
  showView('home');
  msg('Đã đăng xuất', 'success');
};

$('#btnCreate').onclick = () => token() ? postModal.show() : loginModal.show();

/* Đăng nhập */
$('#loginForm').onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  try {
    const d = await api('/auth/login', { method: 'POST', body: JSON.stringify(data) });
    localStorage.setItem('token', d.token);
    currentUser = d.user;
    authUi();
    refreshBadges();
    loginModal.hide();
    e.target.reset();
    msg('Đăng nhập thành công. Xin chào ' + d.user.full_name, 'success');
  } catch (x) { msg(x.message, 'danger'); }
};

/* Đăng nhập quản trị và chuyển thẳng đến bảng điều khiển */
$('#adminLoginForm').onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  try {
    const d = await api('/auth/login', { method: 'POST', body: JSON.stringify(data) });
    if (String(d.user?.role || '').toUpperCase() !== 'ADMIN') {
      throw new Error('Tài khoản này không có quyền quản trị');
    }
    localStorage.setItem('token', d.token);
    e.target.reset();
    adminLoginModal.hide();
    location.href = '/frontend/admin.html';
  } catch (x) { msg(x.message, 'danger'); }
};

/* Đăng ký */
$('#registerForm').onsubmit = async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));

  if (data.password !== data.password_confirm) {
    msg('Mật khẩu nhập lại không khớp', 'danger');
    return;
  }
  delete data.password_confirm;
  if (!data.phone) delete data.phone;

  try {
    await api('/auth/register', { method: 'POST', body: JSON.stringify(data) });
    registerModal.hide();

    // Đăng nhập luôn cho người dùng đỡ phải nhập lại
    const d = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ identity: data.email, password: data.password })
    });
    localStorage.setItem('token', d.token);
    currentUser = d.user;
    authUi();
    refreshBadges();
    e.target.reset();
    msg('Đăng ký thành công. Bạn đã được đăng nhập tự động.', 'success');
  } catch (x) { msg(x.message, 'danger'); }
};

/* Đăng tin, kèm tải ảnh nếu có chọn */
$('#postForm').onsubmit = async (e) => {
  e.preventDefault();
  const btn = $('#btnSubmitPost');
  btn.disabled = true;
  btn.textContent = 'Đang xử lý...';

  try {
    const f = Object.fromEntries(new FormData(e.target));
    delete f.images;
    f.category_id = Number(f.category_id);
    f.reward      = Number(f.reward || 0);
    f.event_date  = f.event_date.replace('T', ' ') + ':00';

    const created = await api('/posts', { method: 'POST', body: JSON.stringify(f) });

    const files = $('#postImages').files;
    let note = '';
    if (files.length) {
      const r = await uploadImages(created.id, files);
      note = ` Đã tải lên ${r.ok}/${r.total} ảnh.`;
    }

    postModal.hide();
    e.target.reset();
    msg('Đăng tin thành công. Hệ thống đã chạy so khớp AI.' + note, 'success');
    showView('home');
    loadPosts();
    refreshBadges();
  } catch (x) {
    msg(x.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Đăng tin';
  }
};

/* Tải thêm ảnh cho bài đã đăng */
$('#uploadForm').onsubmit = async (e) => {
  e.preventDefault();
  const postId = $('#uploadPostId').value;
  const files  = $('#uploadImages').files;
  if (!files.length) return;

  try {
    const r = await uploadImages(postId, files);
    uploadModal.hide();
    e.target.reset();
    msg(`Đã tải lên ${r.ok}/${r.total} ảnh.` + (r.fail ? ` ${r.fail} ảnh thất bại (sai định dạng hoặc quá 5MB).` : ''),
        r.fail ? 'warning' : 'success');
    if (!$('#view-mine').classList.contains('d-none')) loadMyPosts();
    if (!$('#view-detail').classList.contains('d-none')) loadDetail(postId);
  } catch (x) { msg(x.message, 'danger'); }
};

/* Đánh dấu tất cả thông báo đã đọc */
$('#btnReadAll').onclick = async () => {
  try {
    const rows   = await api('/notifications');
    const unread = rows.filter(n => Number(n.is_read) === 0);
    for (const n of unread) await api(`/notifications/${n.id}/read`, { method: 'PATCH' });
    loadNotifications();
    refreshBadges();
    msg(`Đã đánh dấu ${unread.length} thông báo là đã đọc`, 'success');
  } catch (x) { msg(x.message, 'danger'); }
};

/* Ủy quyền sự kiện cho các nút sinh động */
document.addEventListener('click', async (e) => {
  const detailBtn = e.target.closest('[data-detail]');
  if (detailBtn) { loadDetail(detailBtn.dataset.detail); return; }

  const uploadBtn = e.target.closest('[data-upload]');
  if (uploadBtn) {
    $('#uploadPostId').value = uploadBtn.dataset.upload;
    uploadModal.show();
    return;
  }

  const closeBtn = e.target.closest('[data-close]');
  if (closeBtn) {
    if (!confirm('Đóng bài đăng này? Bài sẽ không còn hiển thị trong danh sách tìm kiếm.')) return;
    try {
      await api(`/posts/${closeBtn.dataset.close}/close`, { method: 'PATCH' });
      msg('Đã đóng bài đăng', 'success');
      loadMyPosts();
    } catch (x) { msg(x.message, 'danger'); }
    return;
  }

  const matchBtn = e.target.closest('[data-match]');
  if (matchBtn) {
    const status = matchBtn.dataset.status;
    try {
      await api(`/matches/${matchBtn.dataset.match}`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      });
      msg(status === 'CONFIRMED' ? 'Đã xác nhận. Hai bài đăng đã được tự động đóng.' : 'Đã từ chối kết quả so khớp', 'success');
      loadMatches();
      refreshBadges();
    } catch (x) { msg(x.message, 'danger'); }
    return;
  }

  const readBtn = e.target.closest('[data-read]');
  if (readBtn) {
    try {
      await api(`/notifications/${readBtn.dataset.read}/read`, { method: 'PATCH' });
      loadNotifications();
      refreshBadges();
    } catch (x) { msg(x.message, 'danger'); }
  }
});

/* ---------------- Khởi động ---------------- */

(async () => {
  await loadMe();
  await loadCategories();
  await loadPosts();
  showView('home');
})();
