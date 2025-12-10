/* Main Billing Logic */
let cart = [];
let allProducts = [];

document.addEventListener('DOMContentLoaded', () => {
    loadProducts();

    // Auto-focus search on load
    const searchInput = document.getElementById('productSearch');
    if (searchInput) searchInput.focus();

    // Restore View Preference
    const savedView = localStorage.getItem('billingView');
    if (savedView === 'list') {
        document.getElementById('productList').classList.add('list-view');
    }

    // Event Listeners for Filter/Sort
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyCombinedFilters, 300);
        });
    }
    document.getElementById('sortBy')?.addEventListener('change', applyCombinedFilters);
    document.getElementById('filterCategory')?.addEventListener('change', applyCombinedFilters);


    // Customer Auto-Suggestion Logic
    const customerInput = document.getElementById('customerName');
    const mobileInput = document.getElementById('customerMobile');
    const customerList = document.getElementById('customerList');

    let customersData = []; // Store for lookup

    if (customerInput) {
        // Load customers
        fetch('/api/customers')
            .then(res => res.json())
            .then(customers => {
                customersData = customers;
                customerList.innerHTML = '';
                customers.forEach(c => {
                    const option = document.createElement('option');
                    option.value = c.name;
                    customerList.appendChild(option);
                });
            })
            .catch(err => console.log('Error loading customers:', err));

        // Name -> Mobile Lookup
        customerInput.addEventListener('input', (e) => {
            const val = e.target.value;
            const match = customersData.find(c => c.name.toLowerCase() === val.toLowerCase());
            if (match && match.mobile) {
                mobileInput.value = match.mobile;
            }
        });

        // Mobile -> Name Lookup
        mobileInput.addEventListener('input', (e) => {
            const val = e.target.value;
            const match = customersData.find(c => c.mobile === val);
            if (match) {
                customerInput.value = match.name;
            }
        });
    }
});

async function loadProducts() {
    try {
        const res = await fetch('/api/products');
        allProducts = await res.json();

        // Populate Categories
        const categories = [...new Set(allProducts.map(p => p.category).filter(Boolean))].sort();
        const catSelect = document.getElementById('filterCategory');
        if (catSelect) {
            catSelect.innerHTML = '<option value="">All Categories</option>'; // Reset
            categories.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                catSelect.appendChild(opt);
            });
        }

        applyCombinedFilters(); // Initial render
    } catch (err) {
        console.error("Failed to load products", err);
    }
}

let searchTimeout;

function applyCombinedFilters() {
    const query = document.getElementById('productSearch').value.toLowerCase();
    const sortVal = document.getElementById('sortBy')?.value || 'name';
    const catVal = document.getElementById('filterCategory')?.value || '';

    let results = allProducts.filter(p => {
        const matchesName = p.name.toLowerCase().includes(query);
        const matchesCat = catVal ? p.category === catVal : true;
        return matchesName && matchesCat;
    });

    // Sorting
    results.sort((a, b) => {
        if (sortVal === 'name_asc' || sortVal === 'name') return a.name.localeCompare(b.name);
        if (sortVal === 'name_desc') return b.name.localeCompare(a.name);
        if (sortVal === 'price_asc') return parseFloat(a.price) - parseFloat(b.price);
        if (sortVal === 'price_desc') return parseFloat(b.price) - parseFloat(a.price);
        if (sortVal === 'stock_asc') return parseFloat(a.stock) - parseFloat(b.stock);
        if (sortVal === 'stock_desc') return parseFloat(b.stock) - parseFloat(a.stock);
        return 0;
    });

    renderProductList(results, false);
}

// Infinite Scroll State
let currentProductSet = [];
let renderedCount = 0;
const BATCH_SIZE = 50;

function renderProductList(products, append = false) {
    const listDiv = document.getElementById('productList');

    if (!append) {
        listDiv.innerHTML = '';
        listDiv.scrollTop = 0;
        renderedCount = 0;
        currentProductSet = products;
    }

    const nextBatch = currentProductSet.slice(renderedCount, renderedCount + BATCH_SIZE);

    if (nextBatch.length === 0 && renderedCount === 0) {
        listDiv.innerHTML = '<div style="padding:1rem; text-align:center; color:#888;">No medicines found.</div>';
        return;
    }

    const fragment = document.createDocumentFragment();

    nextBatch.forEach(p => {
        const div = document.createElement('div');
        div.className = 'product-card';
        div.onclick = () => addToCart(p);

        // Expiry Check
        let expiryBadge = '';
        if (p.expiry) {
            const days = getDaysUntil(p.expiry);
            if (days < 0) expiryBadge = '<span class="badge badge-danger">EXPIRED</span>';
            else if (days < 90) expiryBadge = `<span class="badge badge-warning">Exp:${days}d</span>`;
        }

        div.innerHTML = `
            <div class="card-header">
                <span class="product-category">${p.category || 'Medicine'}</span>
                ${expiryBadge}
            </div>
            <div class="card-body">
                <div class="product-name">${p.name}</div>
                <div class="product-meta">
                    <span class="stock-badge ${p.stock < 10 ? 'low-stock' : ''}">${parseFloat(p.stock).toFixed(1)} ${p.unit}</span>
                    <span class="pack-info">${p.per_strip ? `(${p.per_strip}/${p.unit})` : ''}</span>
                </div>
                <div class="product-price">₹${parseFloat(p.price).toFixed(2)}</div>
            </div>
            <button class="btn-add-card">Add +</button>
        `;
        fragment.appendChild(div);
    });

    listDiv.appendChild(fragment);
    renderedCount += nextBatch.length;
}

// Scroll Listener for Infinite Loading
window.addEventListener('scroll', () => {
    // Load more when scrolled to bottom (w/ 100px buffer)
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
        if (renderedCount < currentProductSet.length) {
            renderProductList(currentProductSet, true);
        }
    }
});

function getDaysUntil(dateStr) {
    const today = new Date();
    const exp = new Date(dateStr);
    const diff = exp - today;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function addToCart(product) {
    // Check stock
    if (parseInt(product.stock) <= 0) {
        alert('Out of Stock!');
        return;
    }

    // Expiry Block
    if (product.expiry) {
        const days = getDaysUntil(product.expiry);
        if (days < 0) {
            if (!confirm(`WARNING: This item EXPIRED on ${product.expiry}. Sell anyway?`)) return;
        }
    }

    const existing = cart.find(item => item.id == product.id);
    if (existing) {
        if (existing.qty >= parseInt(product.stock)) {
            alert('Not enough stock!');
            return;
        }
        existing.qty++;
    } else {
        cart.push({
            ...product,
            qty: 1,
            sale_unit: 'main', // 'main' (Strip) or 'sub' (Tablet)
            per_strip: parseFloat(product.per_strip) || 0,
            original_price: product.price
        });
    }

    updateCartDisplay();
    // Clear search
    // document.getElementById('productSearch').value = ''; 
    // document.getElementById('searchResults').innerHTML = '';
}

function updateCartDisplay() {
    const listDiv = document.getElementById('cartItems');
    listDiv.innerHTML = '';

    let subTotal = 0;

    if (cart.length === 0) {
        listDiv.innerHTML = '<div class="empty-cart-msg">Cart is empty</div>';
    }

    cart.forEach((item, index) => {
        const lineTotal = item.qty * item.price;
        subTotal += lineTotal;

        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <div style="display:flex; align-items:center; gap:5px;">
                    <span>₹</span>
                    <input type="number" value="${item.price}" step="0.01" 
                        style="width:70px; padding:2px; border:1px solid #ddd; border-radius:4px;"
                        onchange="updatePrice(${index}, this.value)">
                    <span>x ${item.qty}</span>
                </div>
                <div style="font-size:0.8rem; color:#888;">${item.batch || ''}</div>
            </div>
            <div class="cart-actions">
                ${item.per_strip > 1 ? `
                    <select onchange="toggleUnit(${index}, this.value)" style="padding:2px; margin-right:5px; border-radius:4px; border:1px solid #ddd;">
                        <option value="main" ${item.sale_unit === 'main' ? 'selected' : ''}>${item.unit}</option>
                        <option value="sub" ${item.sale_unit === 'sub' ? 'selected' : ''}>Loose</option>
                    </select>
                ` : ''}
                
                <input type="number" 
                    value="${item.sale_unit === 'sub' ? Math.round(item.qty * item.per_strip) : item.qty}" 
                    min="${item.sale_unit === 'sub' ? 1 : 0.1}" 
                    step="${item.sale_unit === 'sub' ? 1 : 'any'}"
                    style="width:60px; padding:4px; border:1px solid #ddd; border-radius:4px;"
                    onchange="updateQty(${index}, this.value)">
                
                <span style="font-weight:600; min-width:60px; text-align:right;">₹${lineTotal.toFixed(2)}</span>
                
                <button class="btn-remove" onclick="removeFromCart(${index})">×</button>
            </div>
        `;
        listDiv.appendChild(div);
    });

    document.getElementById('totalAmount').textContent = '₹' + subTotal.toFixed(2);
}

function updateQty(index, newQty) {
    const item = cart[index];
    let val = parseFloat(newQty);

    if (isNaN(val) || val <= 0) {
        removeFromCart(index);
        return;
    }

    // Convert back to main unit if in sub mode
    let actualQty = val;
    if (item.sale_unit === 'sub' && item.per_strip > 0) {
        actualQty = val / item.per_strip;
    }

    if (actualQty > parseFloat(item.stock)) {
        alert(`Only ${item.stock} ${item.unit} in stock!`);
        updateCartDisplay(); // reset
        return;
    }

    item.qty = actualQty;
    updateCartDisplay();
}

function toggleView() {
    const list = document.getElementById('productList');
    list.classList.toggle('list-view');
    const isList = list.classList.contains('list-view');
    localStorage.setItem('billingView', isList ? 'list' : 'grid');
}

function toggleUnit(index, unit) {
    cart[index].sale_unit = unit;
    updateCartDisplay();
}

function updatePrice(index, newPrice) {
    const price = parseFloat(newPrice);
    if (isNaN(price) || price < 0) {
        updateCartDisplay(); // reset
        return;
    }
    cart[index].price = price;
    updateCartDisplay();
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartDisplay();
}

async function generateInvoice() {
    if (cart.length === 0) {
        alert('Cart is empty!');
        return;
    }

    const customerName = document.getElementById('customerName').value.trim() || 'Walk-in Customer';
    const customerMobile = document.getElementById('customerMobile').value.trim() || '';

    document.getElementById('btnGenerate').disabled = true;
    document.getElementById('btnGenerate').textContent = 'Processing...';

    try {
        const payload = {
            customer_name: customerName,
            customer_mobile: customerMobile,
            items: cart
        };

        const res = await fetch('/api/invoice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.success) {
            // Show Modal
            document.getElementById('modalOverlay').style.display = 'flex';
            // Setup Print Link
            const printBtn = document.getElementById('printBtn');
            if (printBtn) {
                printBtn.onclick = () => {
                    window.open(`/print_invoice/${data.invoice_file}`, '_blank');
                };
            }

            // Clear
            cart = [];
            updateCartDisplay();
            document.getElementById('customerName').value = '';
            document.getElementById('customerMobile').value = '';
            // Reload products to update stock
            loadProducts();

        } else {
            alert('Error: ' + data.message);
        }

    } catch (err) {
        console.error(err);
        alert('System Error');
    } finally {
        document.getElementById('btnGenerate').disabled = false;
        document.getElementById('btnGenerate').textContent = 'Generate Invoice';
    }
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
}

function newInvoice() {
    closeModal();
}
