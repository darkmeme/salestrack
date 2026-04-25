// ── CSRF helper ─────────────────────────────────────────────────────────────
function getCsrfToken() {
    return document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))
        ?.split('=')[1] || '';
}

// ── JSON POST helper ─────────────────────────────────────────────────────────
function postJSON(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(data),
    }).then(r => r.json());
}

// ── Form POST helper ──────────────────────────────────────────────────────────
function postForm(url, data) {
    const body = new FormData();
    body.append('csrfmiddlewaretoken', getCsrfToken());
    for (const [k, v] of Object.entries(data)) {
        if (v !== null && v !== undefined) body.append(k, v);
    }
    return fetch(url, { method: 'POST', body }).then(r => r.json());
}

// ── Toast notification ───────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.querySelector('.toast-container') || (() => {
        const c = document.createElement('div');
        c.className = 'toast-container position-fixed top-0 end-0 p-3';
        c.style.zIndex = 9999;
        document.body.appendChild(c);
        return c;
    })();

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const wrapper = document.getElementById('wrapper');
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');

    // Create overlay element for mobile
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);

    const isDesktop = () => window.innerWidth >= 992;

    // Restore desktop collapsed state from localStorage
    if (isDesktop() && localStorage.getItem('sidebarCollapsed') === 'true') {
        wrapper.classList.add('sidebar-collapsed');
    }

    function closeMobileSidebar() {
        sidebar.classList.remove('show');
        overlay.classList.remove('active');
    }

    toggleBtn && toggleBtn.addEventListener('click', () => {
        if (isDesktop()) {
            // Desktop: toggle collapsed class on wrapper
            const collapsed = wrapper.classList.toggle('sidebar-collapsed');
            localStorage.setItem('sidebarCollapsed', collapsed);
        } else {
            // Mobile: slide in/out
            const open = sidebar.classList.toggle('show');
            overlay.classList.toggle('active', open);
        }
    });

    // Close mobile sidebar when clicking overlay
    overlay.addEventListener('click', closeMobileSidebar);

    // Close mobile sidebar on nav link click (UX improvement)
    sidebar.querySelectorAll('.nav-item a').forEach(link => {
        link.addEventListener('click', () => {
            if (!isDesktop()) closeMobileSidebar();
        });
    });

    // Auto-dismiss existing toasts (server-rendered)
    document.querySelectorAll('.toast').forEach(el => {
        new bootstrap.Toast(el, { delay: 4000 }).show();
    });

    // Global branch selector
    const branchSel = document.getElementById('globalBranchSelector');
    if (branchSel) {
        branchSel.addEventListener('change', function () {
            postForm('/set-branch/', { branch_id: this.value }).then(() => location.reload());
        });
    }

    loadNotifications();
});

// ── Low stock notifications ──────────────────────────────────────────────────
function loadNotifications() {
    const badge = document.getElementById('notifBadge');
    const list = document.getElementById('notifList');
    if (!badge || !list) return;

    fetch('/inventory/low-stock/')
        .then(r => r.json())
        .then(res => {
            if (!res.success || !res.data.length) {
                badge.style.display = 'none';
                list.innerHTML = '<div class="dropdown-item text-muted small">Sin alertas de stock</div>';
                return;
            }
            badge.style.display = 'block';
            list.innerHTML = res.data.slice(0, 8).map(item => `
                <div class="dropdown-item small">
                    <div class="fw-semibold">${item.product}</div>
                    <div class="text-muted">${item.branch} — Stock: <span class="text-danger fw-bold">${item.quantity}</span> (mín: ${item.min_stock})</div>
                </div>`).join('');
        })
        .catch(() => { if (badge) badge.style.display = 'none'; });
}
