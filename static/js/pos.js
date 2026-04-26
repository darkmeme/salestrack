// POS — Point of Sale JavaScript
// window.CURRENCY_SYMBOL and window.TAX_RATE are injected by pos.html
const TAX_RATE = typeof window.TAX_RATE !== 'undefined' ? window.TAX_RATE : 0.15;
const CURRENCY = typeof window.CURRENCY_SYMBOL !== 'undefined' ? window.CURRENCY_SYMBOL : 'L';

let cart = [];
let searchTimer = null;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const productInput = document.getElementById('productSearch');
    const searchResults = document.getElementById('searchResults');
    const customerInput = document.getElementById('customerSearch');
    const customerResults = document.getElementById('customerResults');

    if (productInput) {
        productInput.addEventListener('input', function () {
            clearTimeout(searchTimer);
            const q = this.value.trim();
            if (!q) { hideDropdown(searchResults); return; }
            searchTimer = setTimeout(() => searchProducts(q), 250);
        });

        productInput.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            e.preventDefault();
            const q = this.value.trim();
            if (!q) return;
            clearTimeout(searchTimer);
            addFirstResult(q);
        });

        document.addEventListener('click', (e) => {
            if (!productInput.contains(e.target)) hideDropdown(searchResults);
            if (customerInput && !customerInput.contains(e.target) &&
                !customerResults.contains(e.target)) hideDropdown(customerResults);
        });
    }

    if (customerInput) {
        let custTimer;
        customerInput.addEventListener('input', function () {
            clearTimeout(custTimer);
            const q = this.value.trim();
            if (!q) { hideDropdown(customerResults); return; }
            custTimer = setTimeout(() => searchCustomers(q), 300);
        });
    }
});

function getBranchId() {
    const el = document.getElementById('posBranch');
    return el ? el.value : null;
}

// ── Product search ────────────────────────────────────────────────────────────
function searchProducts(q) {
    const branchId = getBranchId();
    if (!branchId) { showToast('Selecciona una sucursal primero.', 'warning'); return; }
    const results = document.getElementById('searchResults');

    fetch(`/sales/new/search-products/?branch=${branchId}&q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(res => {
            results.innerHTML = '';
            if (!res.data || !res.data.length) {
                results.innerHTML = '<div class="search-result-item text-muted">Sin resultados</div>';
            } else {
                res.data.forEach(p => {
                    const div = document.createElement('div');
                    div.className = 'search-result-item';
                    div.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <strong>${p.name}</strong>
                            <span class="text-primary">${CURRENCY} ${p.price.toFixed(2)}</span>
                        </div>
                        <small class="text-muted">${p.sku} — Stock: <span class="${p.stock < 5 ? 'text-danger' : 'text-success'}">${p.stock}</span></small>`;
                    div.addEventListener('click', () => {
                        addToCart(p);
                        document.getElementById('productSearch').value = '';
                        hideDropdown(document.getElementById('searchResults'));
                    });
                    results.appendChild(div);
                });
            }
            results.style.display = 'block';
        })
        .catch(() => showToast('Error al buscar productos.', 'danger'));
}

function addFirstResult(q) {
    const branchId = getBranchId();
    if (!branchId) { showToast('Selecciona una sucursal primero.', 'warning'); return; }
    fetch(`/sales/new/search-products/?branch=${branchId}&q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(res => {
            if (!res.data || !res.data.length) {
                showToast('Producto no encontrado.', 'warning');
                return;
            }
            const exact = res.data.find(p => p.sku.toLowerCase() === q.toLowerCase()) || res.data[0];
            addToCart(exact);
            document.getElementById('productSearch').value = '';
            hideDropdown(document.getElementById('searchResults'));
        })
        .catch(() => showToast('Error al buscar productos.', 'danger'));
}

// ── Customer search ───────────────────────────────────────────────────────────
function searchCustomers(q) {
    const results = document.getElementById('customerResults');
    fetch(`/customers/search/?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(res => {
            results.innerHTML = '';
            if (!res.data || !res.data.length) {
                results.innerHTML = '<div class="search-result-item text-muted small">Sin resultados</div>';
                results.style.display = 'block';
                return;
            }
            res.data.forEach(c => {
                const div = document.createElement('div');
                div.className = 'search-result-item';
                div.innerHTML = `
                    <div class="fw-semibold">${c.name}</div>
                    <small class="text-muted">${c.phone || ''} ${c.email ? '· ' + c.email : ''}</small>`;
                div.addEventListener('click', () => {
                    document.getElementById('customerId').value = c.id;
                    document.getElementById('customerSearch').value = c.name;
                    hideDropdown(results);
                });
                results.appendChild(div);
            });
            results.style.display = 'block';
        })
        .catch(() => showToast('Error al buscar clientes.', 'danger'));
}

function hideDropdown(el) {
    if (el) { el.innerHTML = ''; el.style.display = 'none'; }
}

// ── Cart management ───────────────────────────────────────────────────────────
function addToCart(product) {
    const existing = cart.find(i => i.product_id === product.id);
    if (existing) {
        if (existing.quantity >= product.stock) {
            showToast(`Stock máximo alcanzado (${product.stock} unidades).`, 'warning');
            return;
        }
        existing.quantity++;
        existing.subtotal = (existing.unit_price * existing.quantity) - existing.discount;
    } else {
        cart.push({
            product_id: product.id,
            name: product.name,
            sku: product.sku,
            unit_price: product.price,
            quantity: 1,
            discount: 0,
            subtotal: product.price,
            max_stock: product.stock,
        });
    }
    renderCart();
}

function renderCart() {
    const tbody = document.getElementById('cartBody');
    if (!cart.length) {
        tbody.innerHTML = `<tr id="emptyCart">
            <td colspan="6" class="text-center text-muted py-4">
                <i class="bi bi-cart-x fs-3 d-block mb-2"></i>El carrito está vacío
            </td></tr>`;
        recalculate();
        return;
    }

    tbody.innerHTML = cart.map((item, idx) => {
        const remaining = item.max_stock - item.quantity;
        const stockClass = remaining <= 0 ? 'text-danger fw-bold' : remaining <= 3 ? 'text-warning fw-semibold' : 'text-success';
        return `
        <tr>
            <td>
                <div class="fw-semibold">${item.name}</div>
                <small class="text-muted">${item.sku}</small>
            </td>
            <td>
                <input type="number" class="form-control form-control-sm cart-qty-input"
                       value="${item.quantity}" min="1" max="${item.max_stock}"
                       onchange="updateQty(${idx}, this.value)">
            </td>
            <td class="text-center">
                <span class="${stockClass}" title="Stock restante">${remaining}</span>
            </td>
            <td>
                <div class="input-group input-group-sm">
                    <span class="input-group-text" style="font-size:0.75rem;">${CURRENCY}</span>
                    <input type="number" class="form-control form-control-sm"
                           value="${item.unit_price.toFixed(2)}" min="0" step="0.01"
                           onchange="updatePrice(${idx}, this.value)">
                </div>
            </td>
            <td>
                <div class="input-group input-group-sm">
                    <span class="input-group-text" style="font-size:0.75rem;">${CURRENCY}</span>
                    <input type="number" class="form-control form-control-sm"
                           value="${item.discount.toFixed(2)}" min="0" step="0.01"
                           onchange="updateItemDiscount(${idx}, this.value)">
                </div>
            </td>
            <td class="fw-semibold text-end">${CURRENCY} ${item.subtotal.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="removeFromCart(${idx})">
                    <i class="bi bi-x"></i>
                </button>
            </td>
        </tr>`; }).join('');

    recalculate();
}

function updateQty(idx, val) {
    const qty = Math.max(1, Math.min(parseInt(val), cart[idx].max_stock));
    cart[idx].quantity = qty;
    cart[idx].subtotal = (cart[idx].unit_price * qty) - cart[idx].discount;
    renderCart();
}

function updatePrice(idx, val) {
    cart[idx].unit_price = parseFloat(val) || 0;
    cart[idx].subtotal = (cart[idx].unit_price * cart[idx].quantity) - cart[idx].discount;
    renderCart();
}

function updateItemDiscount(idx, val) {
    cart[idx].discount = parseFloat(val) || 0;
    cart[idx].subtotal = (cart[idx].unit_price * cart[idx].quantity) - cart[idx].discount;
    renderCart();
}

function removeFromCart(idx) {
    cart.splice(idx, 1);
    renderCart();
}

function clearCart() {
    cart = [];
    renderCart();
    document.getElementById('globalDiscount').value = 0;
    document.getElementById('customerId').value = '';
    document.getElementById('customerSearch').value = '';
    recalculate();
}

// ── Totals ────────────────────────────────────────────────────────────────────
function recalculate() {
    const subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    const discount = parseFloat(document.getElementById('globalDiscount')?.value) || 0;
    const taxable = Math.max(0, subtotal - discount);
    const tax = taxable * TAX_RATE;
    const total = taxable + tax;

    setText('summarySubtotal', `${CURRENCY} ${subtotal.toFixed(2)}`);
    setText('summaryTax', `${CURRENCY} ${tax.toFixed(2)}`);
    setText('summaryTotal', `${CURRENCY} ${total.toFixed(2)}`);

    const payInput = document.getElementById('paymentAmount');
    if (payInput && parseFloat(payInput.value) === 0) {
        payInput.value = total.toFixed(2);
    }
    updateCambio();
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

function updateCambio() {
    const payInput = document.getElementById('paymentAmount');
    const cambioBox = document.getElementById('cambioBox');
    const summaryCambio = document.getElementById('summaryCambio');
    if (!payInput || !cambioBox || !summaryCambio) return;

    const subtotal = cart.reduce((sum, i) => sum + i.subtotal, 0);
    const discount = parseFloat(document.getElementById('globalDiscount')?.value) || 0;
    const taxable = Math.max(0, subtotal - discount);
    const total = taxable + taxable * TAX_RATE;
    const paid = parseFloat(payInput.value) || 0;
    const cambio = paid - total;

    if (paid > 0 && cambio >= 0) {
        summaryCambio.textContent = `${CURRENCY} ${cambio.toFixed(2)}`;
        cambioBox.style.display = 'block';
    } else {
        cambioBox.style.display = 'none';
    }
}

// ── Customer ──────────────────────────────────────────────────────────────────
function clearCustomer() {
    document.getElementById('customerId').value = '';
    document.getElementById('customerSearch').value = '';
    hideDropdown(document.getElementById('customerResults'));
}

// ── New customer modal ────────────────────────────────────────────────────────
function saveNewCustomer() {
    const name = document.getElementById('newCustName').value.trim();
    if (!name) { showToast('El nombre es obligatorio.', 'warning'); return; }
    const payload = {
        name,
        phone: document.getElementById('newCustPhone').value.trim(),
        email: document.getElementById('newCustEmail').value.trim(),
        address: document.getElementById('newCustAddress').value.trim(),
    };
    postJSON('/customers/create/', payload).then(res => {
        if (res.success) {
            document.getElementById('customerId').value = res.id;
            document.getElementById('customerSearch').value = res.name;
            bootstrap.Modal.getInstance(document.getElementById('newCustomerModal')).hide();
            document.getElementById('newCustomerForm').reset();
            showToast('Cliente creado correctamente.', 'success');
        } else {
            const errs = Object.values(res.errors || {}).flat().join(' ');
            showToast(errs || 'Error al crear cliente.', 'danger');
        }
    }).catch(() => showToast('Error de conexión.', 'danger'));
}

// ── Complete sale ─────────────────────────────────────────────────────────────
function completeSale() {
    const branchId = getBranchId();
    if (!branchId) { showToast('Selecciona una sucursal.', 'warning'); return; }
    if (!cart.length) { showToast('El carrito está vacío.', 'warning'); return; }

    const subtotal = cart.reduce((s, i) => s + i.subtotal, 0);
    const discount = parseFloat(document.getElementById('globalDiscount').value) || 0;
    const taxable = Math.max(0, subtotal - discount);
    const tax = taxable * TAX_RATE;
    const total = taxable + tax;

    const payload = {
        branch_id: parseInt(branchId),
        customer_id: document.getElementById('customerId').value || null,
        items: cart.map(i => ({
            product_id: i.product_id,
            quantity: i.quantity,
            unit_price: i.unit_price,
            discount: i.discount,
        })),
        discount: discount,
        notes: document.getElementById('saleNotes').value,
        payment_method: document.getElementById('paymentMethod').value,
        payment_amount: parseFloat(document.getElementById('paymentAmount').value) || total,
    };

    postJSON('/sales/new/create/', payload).then(res => {
        if (res.success) {
            document.getElementById('invoiceResult').textContent = `Factura: ${res.invoice_number}`;
            document.getElementById('printLink').href = `/sales/${res.sale_id}/`;
            new bootstrap.Modal(document.getElementById('saleSuccessModal')).show();
            clearCart();
        } else {
            showToast(res.message || 'Error al procesar la venta.', 'danger');
        }
    }).catch(() => showToast('Error de conexión.', 'danger'));
}

function newSale() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('saleSuccessModal'));
    if (modal) modal.hide();
}
