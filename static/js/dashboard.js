// Dashboard JS — loads all data via AJAX
// window.CURRENCY_SYMBOL and window.IS_SUPERADMIN are injected by the template

document.addEventListener('DOMContentLoaded', () => {
    const CURRENCY = typeof window.CURRENCY_SYMBOL !== 'undefined' ? window.CURRENCY_SYMBOL : 'L';
    const isSuperadmin = window.IS_SUPERADMIN === true;

    const branchParam = () => {
        const sel = document.getElementById('globalBranchSelector');
        return sel ? sel.value : '';
    };

    function buildQuery() {
        const b = branchParam();
        return b ? `?branch=${b}` : '';
    }

    function fmt(val) {
        return `${CURRENCY} ${parseFloat(val).toFixed(2)}`;
    }

    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    // ── KPI Stats ──────────────────────────────────────────────────────────
    function loadStats() {
        fetch(`/api/stats/${buildQuery()}`)
            .then(r => r.json())
            .then(res => {
                if (!res.success) return;
                const d = res.data;
                setText('kpiSalesToday', d.sales_today);
                setText('kpiRevenueToday', fmt(d.revenue_today));
                setText('kpiMonthlyRevenue', fmt(d.monthly_revenue));
                setText('kpiLowStock', d.low_stock_count);
            })
            .catch(() => {});
    }

    // ── 7-day sales chart ─────────────────────────────────────────────────
    let chart7days = null;
    function loadChart7Days() {
        fetch(`/api/chart/sales-7days/${buildQuery()}`)
            .then(r => r.json())
            .then(res => {
                if (!res.success) return;
                const ctx = document.getElementById('chartSales7Days');
                if (!ctx) return;
                if (chart7days) chart7days.destroy();
                chart7days = new Chart(ctx, {
                    type: 'bar',
                    data: res.data,
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'top' } },
                        scales: {
                            y: { beginAtZero: true, ticks: { callback: v => `${CURRENCY} ${v}` } }
                        }
                    }
                });
            })
            .catch(() => {});
    }

    // ── Monthly revenue chart ─────────────────────────────────────────────
    let chartMonthly = null;
    function loadChartMonthly() {
        fetch(`/api/chart/monthly-revenue/${buildQuery()}`)
            .then(r => r.json())
            .then(res => {
                if (!res.success) return;
                const ctx = document.getElementById('chartMonthly');
                if (!ctx) return;
                if (chartMonthly) chartMonthly.destroy();
                chartMonthly = new Chart(ctx, {
                    type: 'line',
                    data: res.data,
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } },
                        scales: {
                            y: { beginAtZero: true, ticks: { callback: v => `${CURRENCY} ${v}` } }
                        }
                    }
                });
            })
            .catch(() => {});
    }

    // ── Recent sales ───────────────────────────────────────────────────────
    function loadRecentSales() {
        fetch('/api/recent-sales/')
            .then(r => r.json())
            .then(res => {
                const tbody = document.getElementById('recentSalesBody');
                if (!tbody || !res.success) return;
                if (!res.data.length) {
                    tbody.innerHTML = `<tr><td colspan="${isSuperadmin ? 6 : 5}" class="text-center text-muted py-3">Sin ventas recientes</td></tr>`;
                    return;
                }
                tbody.innerHTML = res.data.map(s => `
                    <tr>
                        <td><code class="small">${s.invoice_number}</code></td>
                        ${isSuperadmin ? `<td class="small">${s.branch}</td>` : ''}
                        <td>${s.customer}</td>
                        <td class="text-end fw-semibold">${fmt(s.total)}</td>
                        <td><span class="badge ${s.status === 'Completada' ? 'bg-success' : 'bg-secondary'}">${s.status}</span></td>
                        <td class="small text-muted">${s.created_at}</td>
                    </tr>`).join('');
            })
            .catch(() => {});
    }

    // ── Branch summary (superadmin) ────────────────────────────────────────
    function loadBranchSummary() {
        const container = document.getElementById('branchSummaryContainer');
        if (!container) return;
        fetch('/api/branch-summary/')
            .then(r => r.json())
            .then(res => {
                if (!res.success) return;
                if (!res.data.length) {
                    container.innerHTML = '<div class="p-3 text-center text-muted small">Sin sucursales activas</div>';
                    return;
                }
                container.innerHTML = res.data.map(b => `
                    <div class="border-bottom px-3 py-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <strong class="small">${b.name}</strong>
                            <code class="small text-muted">${b.code}</code>
                        </div>
                        <div class="d-flex justify-content-between mt-1">
                            <span class="small text-muted">${b.sales_today} ventas hoy</span>
                            <span class="small fw-semibold">${fmt(b.revenue_today)}</span>
                        </div>
                        ${b.low_stock > 0
                            ? `<span class="badge bg-danger-soft text-danger small mt-1">⚠ ${b.low_stock} stock crítico</span>`
                            : ''}
                    </div>`).join('');
            })
            .catch(() => {});
    }

    // ── Low stock alerts (non-superadmin) ─────────────────────────────────
    function loadLowStockAlerts() {
        const container = document.getElementById('lowStockAlerts');
        if (!container) return;
        fetch('/inventory/low-stock/')
            .then(r => r.json())
            .then(res => {
                if (!res.success || !res.data.length) {
                    container.innerHTML = '<div class="p-3 text-center text-muted small">Sin alertas de stock</div>';
                    return;
                }
                container.innerHTML = res.data.map(item => `
                    <div class="border-bottom px-3 py-2">
                        <div class="fw-semibold small">${item.product}</div>
                        <div class="d-flex justify-content-between">
                            <span class="text-danger fw-bold small">Stock: ${item.quantity}</span>
                            <span class="text-muted small">Mín: ${item.min_stock}</span>
                        </div>
                    </div>`).join('');
            })
            .catch(() => {});
    }

    // ── Reload on branch selector change ──────────────────────────────────
    const branchSel = document.getElementById('globalBranchSelector');
    if (branchSel) {
        branchSel.addEventListener('change', () => {
            loadStats();
            loadChart7Days();
            loadChartMonthly();
        });
    }

    // ── Init ───────────────────────────────────────────────────────────────
    loadStats();
    loadChart7Days();
    loadChartMonthly();
    loadRecentSales();
    loadBranchSummary();
    loadLowStockAlerts();
});
