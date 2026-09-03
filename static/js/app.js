/
  * OWASP Juice Shop - Client Application JS(Indian Localization & Payment Portal)
    * Handles Indian INR Pricing(₹), UPI / QR(GPay, PhonePe, Paytm), RuPay Cards, NetBanking, and Auth
      */

const API_BASE = '/api';

const state = {
  products: [],
  categories: ['All'],
  activeCategory: 'All',
  searchQuery: '',
  sortBy: 'default',
  currentUser: null,
  basket: {
    items: [],
    item_count: 0,
    subtotal: 0.0,
    discount: 0.0,
    delivery_fee: 0.0,
    total: 0.0
  },
  activeCoupon: null,
  selectedProduct: null,
  checkoutData: {
    customer_name: 'Aarav Sharma',
    email: 'customer@juice-sh.op',
    address: 'Flat 402, Palm Heights, Bandra West',
    city: 'Mumbai',
    zip_code: '400050',
    country: 'India',
    delivery_method: 'Standard Fresh Delivery (Free)',
    delivery_fee: 0.0,
    payment_method: 'UPI / QR',
    card_number: '6080 3214 5678 9012',
    card_holder: 'AARAV SHARMA',
    expiry: '12/28',
    cvv: '888',
    bank_name: 'State Bank of India (SBI)',
    upi_id: 'aarav@oksbi',
    selected_upi_app: 'Google Pay'
  }
};

// ==========================================
// Initialization & Lifecycle
// ==========================================

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await checkAuthStatus();
  await fetchCategories();
  await fetchProducts();
  await fetchBasket();
});

// ==========================================
// Toast Notifications
// ==========================================

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  let icon = '🍹';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(60px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// Authentication APIs & State
// ==========================================

async function checkAuthStatus() {
  try {
    const token = localStorage.getItem('access_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/auth/me`, { headers });
    if (res.ok) {
      state.currentUser = await res.json();
      updateAuthUI();
    } else {
      state.currentUser = null;
      updateAuthUI();
    }
  } catch (err) {
    state.currentUser = null;
    updateAuthUI();
  }
}

function updateAuthUI() {
  const accountBtnText = document.getElementById('account-btn-label');
  const dropdownMenu = document.getElementById('account-dropdown-menu');

  if (!dropdownMenu) return;

  if (state.currentUser) {
    if (accountBtnText) accountBtnText.textContent = state.currentUser.full_name || state.currentUser.email.split('@')[0];
    dropdownMenu.innerHTML = `
      <div style="padding: 0.6rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
        <div style="font-size: 0.78rem; color: var(--text-muted);">Signed in as</div>
        <div style="font-weight: 600; font-size: 0.88rem; color: #fff; overflow: hidden; text-overflow: ellipsis;">${state.currentUser.email}</div>
      </div>
      <button class="dropdown-item" onclick="openOrdersModal()">
        <span>📦</span> My Orders & Receipts
      </button>
      <button class="dropdown-item" onclick="openProfileModal()">
        <span>👤</span> User Profile (Rewards: ₹450)
      </button>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item" onclick="handleLogout()" style="color: #ef5350;">
        <span>🚪</span> Logout
      </button>
    `;
  } else {
    if (accountBtnText) accountBtnText.textContent = 'Account';
    dropdownMenu.innerHTML = `
      <a href="/login" class="dropdown-item">
        <span>🔑</span> Login
      </a>
      <a href="/login?tab=register" class="dropdown-item">
        <span>📝</span> Register Account
      </a>
      <div class="dropdown-divider"></div>
      <button class="dropdown-item" onclick="quickDemoLogin('customer@juice-sh.op', 'juice123')">
        <span>⚡</span> Quick Demo Login (Aarav Sharma)
      </button>
    `;
  }
}

async function quickDemoLogin(email, password) {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('access_token', data.access_token);
      state.currentUser = data.user;
      updateAuthUI();
      await fetchBasket();
      showToast(`Welcome back, ${data.user.full_name}!`, 'success');
    } else {
      showToast(data.detail || 'Login failed', 'error');
    }
  } catch (err) {
    showToast('Failed to connect to server', 'error');
  }
}

async function handleLogout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    localStorage.removeItem('access_token');
    state.currentUser = null;
    updateAuthUI();
    await fetchBasket();
    showToast('Logged out successfully', 'info');
  } catch (err) {
    console.error(err);
  }
}

// ==========================================
// Catalog & Products (INR Currency ₹)
// ==========================================

async function fetchCategories() {
  try {
    const res = await fetch(`${API_BASE}/categories`);
    if (res.ok) {
      state.categories = await res.json();
      renderCategoryFilter();
    }
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

function renderCategoryFilter() {
  const select = document.getElementById('category-filter-select');
  if (!select) return;
  select.innerHTML = state.categories.map(cat =>
    `<option value="${cat}" ${state.activeCategory === cat ? 'selected' : ''}>${cat === 'All' ? 'All Categories' : cat}</option>`
  ).join('');
}

async function fetchProducts() {
  try {
    const params = new URLSearchParams();
    if (state.searchQuery) params.append('q', state.searchQuery);
    if (state.activeCategory && state.activeCategory !== 'All') params.append('category', state.activeCategory);
    if (state.sortBy && state.sortBy !== 'default') params.append('sort', state.sortBy);

    const res = await fetch(`${API_BASE}/products?${params.toString()}`);
    if (res.ok) {
      state.products = await res.json();
      renderProductsGrid();
    }
  } catch (err) {
    console.error('Error fetching products:', err);
  }
}

function renderProductsGrid() {
  const grid = document.getElementById('products-grid');
  const countBadge = document.getElementById('products-count-badge');
  if (!grid) return;

  if (countBadge) {
    countBadge.textContent = `${state.products.length} Products`;
  }

  if (state.products.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-secondary);">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔍</div>
        <h3>No juicy matches found</h3>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">Try searching for a different keyword or resetting your filter.</p>
        <button class="btn-secondary" style="margin-top: 1rem;" onclick="resetSearch()">Reset Filters</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = state.products.map(prod => {
    const ribbonHtml = prod.ribbon_badge ?
      `<div class="ribbon-badge">${prod.ribbon_badge}</div>` : '';

    return `
      <div class="product-card" onclick="openProductDetail(${prod.id})">
        <div class="product-image-box">
          ${ribbonHtml}
          <img src="${prod.image_url}" alt="${prod.name}" class="product-image" loading="lazy">
        </div>
        <div class="product-info">
          <div class="product-name" title="${prod.name}">${prod.name}</div>
          <div class="product-price-row">
            <span class="product-price">₹${prod.price.toFixed(0)}</span>
            <div class="product-rating-stars" title="${prod.rating} / 5 stars">
              <span>★</span>
              <span>${prod.rating}</span>
            </div>
          </div>
          <button class="btn-add-basket" onclick="event.stopPropagation(); addToBasket(${prod.id}, 1)">
            <span class="btn-cart-icon-badge">🛒</span>
            <span>Add to Basket</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function resetSearch() {
  state.searchQuery = '';
  state.activeCategory = 'All';
  state.sortBy = 'default';
  const searchInput = document.getElementById('nav-search-input');
  if (searchInput) searchInput.value = '';
  renderCategoryFilter();
  fetchProducts();
}

// ==========================================
// Product Details Modal
// ==========================================

let modalQuantity = 1;

let activeProductTab = 'overview';

function switchProductModalTab(tabKey) {
  activeProductTab = tabKey;
  if (state.selectedProduct) {
    renderProductDetailModal();
  }
}

async function openProductDetail(productId) {
  try {
    const res = await fetch(`${API_BASE}/products/${productId}`);
    if (!res.ok) return;
    const prod = await res.json();
    state.selectedProduct = prod;
    modalQuantity = 1;
    activeProductTab = 'overview';

    renderProductDetailModal();

    const modalBackdrop = document.getElementById('product-modal-backdrop');
    if (modalBackdrop) modalBackdrop.classList.add('active');
  } catch (err) {
    console.error(err);
  }
}

function renderProductDetailModal() {
  const prod = state.selectedProduct;
  const modalContent = document.getElementById('product-modal-content');
  if (!prod || !modalContent) return;

  const originalPrice = prod.original_price || Math.round(prod.price * 1.25);
  const savings = originalPrice - prod.price;
  const discountPercent = Math.round((savings / originalPrice) * 100);

  // Parse ingredients
  const ingredientsList = prod.ingredients ? prod.ingredients.split(',').map(i => i.trim()).filter(Boolean) : [
    '100% Cold Pressed Fruit Extracts',
    'Natural Vitamin C',
    'No Preservatives'
  ];
  const ingredientsHtml = ingredientsList.map(ing => `<span class="ingredient-pill">🍃 ${ing}</span>`).join('');

  // Parse nutrition facts
  const nutritionText = prod.nutrition_info || 'Calories: 110 kcal | Vitamin C: 50mg | Dietary Fiber: 2.5g | Sugars: 20g';
  const nutritionParts = nutritionText.split('|').map(p => p.trim()).filter(Boolean);
  const nutritionHtml = nutritionParts.map(part => {
    const [label, ...val] = part.split(':');
    return `
      <div class="nutrition-item">
        <span style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;">${label.trim()}</span>
        <strong>${val.join(':').trim()}</strong>
      </div>
    `;
  }).join('');

  // Reviews and Breakdown
  const reviews = prod.reviews || [];
  const totalRev = reviews.length;
  const starCounts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
  reviews.forEach(r => {
    const star = Math.min(5, Math.max(1, Math.round(r.rating || 5)));
    starCounts[star] = (starCounts[star] || 0) + 1;
  });

  const ratingBarsHtml = [5, 4, 3, 2, 1].map(s => {
    const count = starCounts[s] || 0;
    const pct = totalRev > 0 ? Math.round((count / totalRev) * 100) : (s === 5 ? 85 : s === 4 ? 15 : 0);
    return `
      <div class="rating-bar-row">
        <span style="min-width: 25px; text-align: right;">${s} ★</span>
        <div class="rating-bar-track">
          <div class="rating-bar-fill" style="width: ${pct}%;"></div>
        </div>
        <span style="min-width: 32px; font-size: 0.72rem;">${pct}%</span>
      </div>
    `;
  }).join('');

  const reviewsListHtml = (reviews.length > 0) ? reviews.map(r => {
    const name = r.author_name || r.author_email.split('@')[0] || 'Verified Buyer';
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    const city = r.city || 'India';
    const helpful = r.helpful_count || Math.floor(Math.random() * 8) + 3;

    return `
      <div class="review-item" id="review-card-${r.id}">
        <div class="review-header-flex">
          <div class="reviewer-meta">
            <div class="reviewer-avatar">${initials}</div>
            <div>
              <div class="reviewer-name-row">
                <span class="reviewer-name">${name}</span>
                <span class="verified-buyer-badge">✓ Verified Buyer</span>
                <span class="review-city-pill">• ${city}</span>
              </div>
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">
                Verified Purchase • Chilled Fresh Delivery
              </div>
            </div>
          </div>
          <div style="color: #ffc107; font-size: 0.95rem; font-weight: 700; letter-spacing: 1px;">
            ${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}
          </div>
        </div>

        <div class="review-text">${r.comment}</div>

        <div class="review-footer">
          <span>Was this review helpful?</span>
          <button class="btn-helpful" id="btn-helpful-${r.id}" onclick="handleHelpfulClick(${r.id}, ${helpful})">
            <span>👍</span> Helpful (<span id="helpful-cnt-${r.id}">${helpful}</span>)
          </button>
        </div>
      </div>
    `;
  }).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem;">No reviews yet. Be the first to taste and review!</p>';

  // Active Tab Body
  let tabBodyContent = '';

  if (activeProductTab === 'overview') {
    tabBodyContent = `
      <div class="product-detail-layout">
        <!-- Left: Image & Guarantees -->
        <div>
          <div class="detail-img-box">
            <img src="${prod.image_url}" alt="${prod.name}">
          </div>
          <div style="margin-top: 0.65rem; text-align: center; font-size: 0.76rem; color: #b0bec5; background: rgba(0,0,0,0.3); padding: 0.35rem 0.5rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
            <span>❄️ ${prod.shelf_life || '7 Days Refrigerated (0-4°C)'}</span>
          </div>
          <div class="trust-badges-row" style="margin-top: 0.5rem; justify-content: center;">
            <span class="trust-badge-item">🌱 100% Raw</span>
            <span class="trust-badge-item">🚫 Zero Sugar</span>
            <span class="trust-badge-item">🛡️ No Chemicals</span>
          </div>
        </div>

        <!-- Right: Details, Pricing, Cart -->
        <div class="detail-info">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;">
            <span class="detail-category-badge">${prod.category}</span>
            <span style="font-size: 0.78rem; color: var(--accent-green); font-weight: 600;">✓ In Stock (${prod.stock} left)</span>
          </div>

          <!-- Price & Discounts -->
          <div class="detail-price-row">
            <span class="detail-price" id="modal-price-val">₹${prod.price.toFixed(0)}</span>
            ${originalPrice > prod.price ? `
              <span class="detail-mrp">MRP ₹${originalPrice.toFixed(0)}</span>
              <span class="discount-savings-badge">Save ₹${savings.toFixed(0)} (${discountPercent}% OFF)</span>
            ` : ''}
          </div>

          <!-- Full Description -->
          <div class="detail-desc">${prod.description || 'Authentic cold-pressed pure Indian juice with no preservatives or chemicals.'}</div>

          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.85rem; flex-wrap: wrap;">
            <span class="detail-meta-chip">📍 ${prod.origin || 'Orchards of India'}</span>
            <span class="detail-meta-chip" style="color: #ffc107; font-weight: 700;">★ ${prod.rating.toFixed(1)} (${totalRev} Reviews)</span>
          </div>

          <!-- Quantity Stepper & Subtotal -->
          <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 0.5rem 0.75rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 0.82rem; color: var(--text-secondary);">Qty:</span>
              <div class="quantity-stepper-compact">
                <button class="stepper-btn-compact" onclick="changeModalQty(-1, ${prod.price})">-</button>
                <span class="stepper-val-compact" id="modal-qty-val">1</span>
                <button class="stepper-btn-compact" onclick="changeModalQty(1, ${prod.price})">+</button>
              </div>
            </div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #fff;">
              Subtotal: <span style="color: var(--accent-orange);" id="modal-subtotal-val">₹${prod.price.toFixed(0)}</span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="product-action-buttons">
            <button class="btn-add-cart-modal" onclick="addToBasket(${prod.id}, modalQuantity); closeModal('product-modal-backdrop');">
              <span>🛒</span> Add to Basket
            </button>
            <button class="btn-buy-now-modal" onclick="instantBuyNow(${prod.id}, modalQuantity)">
              <span>⚡</span> Buy Now (UPI / RuPay)
            </button>
          </div>
        </div>
      </div>
    `;
  }
  else if (activeProductTab === 'ingredients') {
    tabBodyContent = `
      <div class="product-detail-layout">
        <div>
          <div class="detail-img-box">
            <img src="${prod.image_url}" alt="${prod.name}">
          </div>
          <div style="margin-top: 0.75rem; text-align: center; font-size: 0.8rem; color: #90caf9; background: rgba(33, 150, 243, 0.1); border: 1px solid rgba(33, 150, 243, 0.2); padding: 0.5rem; border-radius: 6px;">
            <span>🛡️ 100% Traceable Organic Source</span>
          </div>
        </div>

        <div>
          <!-- Ingredients -->
          <div class="ingredients-box">
            <div class="ingredients-title">
              <span>🌿</span> Pure Ingredients & Botanicals (Zero Chemicals):
            </div>
            <div class="ingredients-tags-list">
              ${ingredientsHtml}
            </div>
          </div>

          <!-- Nutrition Grid -->
          <div class="nutrition-grid-box">
            <div class="ingredients-title" style="color: #90caf9;">
              <span>📊</span> Nutrition Facts (Per 1000ml Bottle):
            </div>
            <div class="nutrition-pills-row">
              ${nutritionHtml}
            </div>
          </div>

          <!-- Origin & Processing -->
          <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-md); padding: 0.85rem; margin-top: 0.75rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 0.35rem;">
              <span>🚜</span> Farm Origin & Extraction Process:
            </div>
            <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">
              Sourced directly from <strong style="color: #fff;">${prod.origin || 'Orchards of India'}</strong>. Slow hydraulic cold-pressing at 4°C extracts 100% live enzymes, antioxidants, and pure juice without any heat pasteurization degradation.
            </p>
          </div>

          <div style="margin-top: 1.25rem; display: flex; justify-content: flex-end;">
            <button class="btn-primary" style="padding: 0.6rem 1.5rem;" onclick="addToBasket(${prod.id}, modalQuantity); closeModal('product-modal-backdrop');">
              <span>🛒</span> Add to Basket (₹${(prod.price * modalQuantity).toFixed(0)})
            </button>
          </div>
        </div>
      </div>
    `;
  } else if (activeProductTab === 'reviews') {
    tabBodyContent = `
      <div>
        <!-- Overall Rating Breakdown Card -->
        <div class="reviews-summary-card">
          <div>
            <div class="rating-score-big">${prod.rating.toFixed(1)}</div>
            <div class="rating-stars-big">★★★★★</div>
            <div style="font-size: 0.78rem; color: var(--text-muted); font-weight: 500;">
              Based on ${totalRev || 28} ratings across India
            </div>
          </div>
          <div class="rating-bars-list">
            ${ratingBarsHtml}
          </div>
        </div>
        
        <!-- Reviews List -->
        <div id="modal-reviews-list" style="max-height: 340px; overflow-y: auto; padding-right: 0.25rem;">
          ${reviewsListHtml}
        </div>

        <!-- Add Review Form -->
        <div style="background: rgba(0,0,0,0.25); padding: 1.25rem; border-radius: 8px; margin-top: 1.25rem; border: 1px solid rgba(255,255,255,0.08);">
          <h5 style="color: #fff; margin-bottom: 0.75rem; font-size: 0.95rem; display: flex; align-items: center; gap: 0.35rem;">
            <span>✍️</span> Share Your Verified Experience
          </h5>
          <div class="form-row" style="margin-bottom: 0.65rem;">
            <div class="form-group">
              <label class="form-label">Your Name</label>
              <input type="text" id="new-review-name" class="form-control" placeholder="Aarav Sharma" value="${state.currentUser ? state.currentUser.full_name : 'Aarav Sharma'}">
            </div>
            <div class="form-group">
              <label class="form-label">Your City / State</label>
              <input type="text" id="new-review-city" class="form-control" placeholder="Mumbai, Maharashtra" value="${state.checkoutData.city || 'Mumbai'}">
            </div>
          </div>

          <div style="display: flex; gap: 0.75rem; margin-bottom: 0.65rem; align-items: center;">
            <span style="font-size: 0.85rem; color: var(--text-muted);">Your Rating:</span>
            <select id="new-review-rating" class="category-filter" style="padding: 0.3rem 0.65rem; font-weight: 600;">
              <option value="5">★★★★★ (5/5 Outstanding Freshness)</option>
              <option value="4">★★★★☆ (4/5 Very Good)</option>
              <option value="3">★★★☆☆ (3/5 Good Taste)</option>
              <option value="2">★★☆☆☆ (2/5 Average)</option>
              <option value="1">★☆☆☆☆ (1/5 Poor)</option>
            </select>
          </div>
          <textarea id="new-review-text" class="form-control" rows="2" placeholder="Tell other Indian buyers about the natural taste, freshness, cold delivery, and ingredients..." style="margin-bottom: 0.75rem; resize: none;"></textarea>
          <button class="btn-secondary" style="font-size: 0.85rem; padding: 0.45rem 1rem;" onclick="submitProductReview(${prod.id})">
            <span>🚀</span> Post Verified Review
          </button>
        </div>
      </div>
    `;
  }

  modalContent.innerHTML = `
    <div class="modal-header">
      <div class="modal-title" style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
        <span>🍹</span> 
        <span>${prod.name}</span>
        ${prod.origin ? `<span style="font-size: 0.75rem; background: rgba(255,152,0,0.15); border: 1px solid rgba(255,152,0,0.3); padding: 0.2rem 0.6rem; border-radius: 4px; color: var(--accent-orange);">📍 ${prod.origin}</span>` : ''}
      </div>
      <button class="modal-close-btn" onclick="closeModal('product-modal-backdrop')">&times;</button>
    </div>
    <div class="modal-body">
      <!-- Luxury Navigation Tabs -->
      <div class="product-modal-tabs">
        <button class="product-tab-btn ${activeProductTab === 'overview' ? 'active' : ''}" onclick="switchProductModalTab('overview')">
          <span>🏷️</span> Overview & Purchase
        </button>
        <button class="product-tab-btn ${activeProductTab === 'ingredients' ? 'active' : ''}" onclick="switchProductModalTab('ingredients')">
          <span>🌿</span> Ingredients & Nutrition
        </button>
        <button class="product-tab-btn ${activeProductTab === 'reviews' ? 'active' : ''}" onclick="switchProductModalTab('reviews')">
          <span>⭐</span> Reviews (${totalRev})
        </button>
      </div>

      ${tabBodyContent}
    </div>
  `;
}


function changeModalQty(delta, unitPrice) {
  modalQuantity = Math.max(1, modalQuantity + delta);
  const qtyEl = document.getElementById('modal-qty-val');
  const subtotalEl = document.getElementById('modal-subtotal-val');
  if (qtyEl) qtyEl.textContent = modalQuantity;
  if (subtotalEl && unitPrice) {
    subtotalEl.textContent = `₹${(unitPrice * modalQuantity).toFixed(0)}`;
  }
}

async function instantBuyNow(productId, quantity) {
  await addToBasket(productId, quantity);
  closeModal('product-modal-backdrop');
  openCheckoutPortal();
}

async function handleHelpfulClick(reviewId, initialCount) {
  const btn = document.getElementById(`btn-helpful-${reviewId}`);
  const countEl = document.getElementById(`helpful-cnt-${reviewId}`);
  if (btn && !btn.classList.contains('active')) {
    btn.classList.add('active');
    const newCount = initialCount + 1;
    if (countEl) countEl.textContent = newCount;
    showToast('Dhanyavaad! Marked as helpful.', 'info');
    try {
      await fetch(`${API_BASE}/reviews/${reviewId}/helpful`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  }
}

async function submitProductReview(productId) {
  const ratingEl = document.getElementById('new-review-rating');
  const textEl = document.getElementById('new-review-text');
  const nameEl = document.getElementById('new-review-name');
  const cityEl = document.getElementById('new-review-city');

  if (!textEl || !textEl.value.trim()) {
    showToast('Please write your thoughts for the review', 'error');
    return;
  }

  const rating = parseInt(ratingEl.value);
  const comment = textEl.value.trim();
  const author_name = nameEl ? nameEl.value.trim() : 'Verified Customer';
  const city = cityEl ? cityEl.value.trim() : 'India';

  try {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/products/${productId}/reviews`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        rating,
        comment,
        author_name,
        city
      })
    });

    if (res.ok) {
      showToast('Review posted successfully! Dhanyavaad for your feedback.', 'success');
      await openProductDetail(productId);
      await fetchProducts();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Could not submit review', 'error');
    }
  } catch (err) {
    showToast('Error submitting review', 'error');
  }
}


// ==========================================
// Basket / Cart Operations
// ==========================================

async function fetchBasket() {
  try {
    const token = localStorage.getItem('access_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    let url = `${API_BASE}/basket`;
    if (state.activeCoupon) url += `?coupon=${encodeURIComponent(state.activeCoupon)}`;

    const res = await fetch(url, { headers });
    if (res.ok) {
      state.basket = await res.json();
      updateBasketBadge();
    }
  } catch (err) {
    console.error('Error fetching basket:', err);
  }
}

function updateBasketBadge() {
  const badge = document.getElementById('nav-basket-badge');
  if (badge) {
    badge.textContent = state.basket.item_count || 0;
  }
}

async function addToBasket(productId, quantity = 1) {
  try {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/basket/add`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ product_id: productId, quantity })
    });

    if (res.ok) {
      state.basket = await res.json();
      updateBasketBadge();
      const product = state.products.find(p => p.id === productId);
      const name = product ? product.name : 'Juice';
      showToast(`Added ${quantity}x ${name} to your basket!`, 'success');
    }
  } catch (err) {
    showToast('Failed to add to basket', 'error');
  }
}

async function updateCartItemQuantity(itemId, quantity) {
  try {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/basket/item/${itemId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ quantity })
    });

    if (res.ok) {
      state.basket = await res.json();
      updateBasketBadge();
      renderBasketDrawer();
    }
  } catch (err) {
    showToast('Failed to update cart item', 'error');
  }
}

async function removeCartItem(itemId) {
  try {
    const token = localStorage.getItem('access_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    const res = await fetch(`${API_BASE}/basket/item/${itemId}`, {
      method: 'DELETE',
      headers
    });

    if (res.ok) {
      state.basket = await res.json();
      updateBasketBadge();
      renderBasketDrawer();
      showToast('Item removed from basket', 'info');
    }
  } catch (err) {
    showToast('Failed to remove item', 'error');
  }
}

function openBasketModal() {
  renderBasketDrawer();
  const modal = document.getElementById('basket-modal-backdrop');
  if (modal) modal.classList.add('active');
}

function renderBasketDrawer() {
  const container = document.getElementById('basket-modal-content');
  if (!container) return;

  const items = state.basket.items || [];

  if (items.length === 0) {
    container.innerHTML = `
      <div class="modal-header">
        <div class="modal-title"><span>🛒</span> Your Shopping Basket (0)</div>
        <button class="modal-close-btn" onclick="closeModal('basket-modal-backdrop')">&times;</button>
      </div>
      <div class="modal-body" style="text-align: center; padding: 3rem 1.5rem;">
        <div style="font-size: 3.5rem; margin-bottom: 1rem;">🧺</div>
        <h3 style="color: #fff; margin-bottom: 0.5rem;">Your basket is thirsty!</h3>
        <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">Explore our freshly squeezed organic juices and add some delicious drinks to get started.</p>
        <button class="btn-primary" onclick="closeModal('basket-modal-backdrop');">Start Shopping</button>
      </div>
    `;
    return;
  }

  const itemsHtml = items.map(item => `
    <div class="basket-item-row">
      <img src="${item.product.image_url}" alt="${item.product.name}" class="basket-thumb">
      <div>
        <div class="basket-item-name">${item.product.name}</div>
        <div class="basket-item-unit-price">₹${item.product.price.toFixed(0)} each</div>
      </div>
      <div class="quantity-stepper" style="margin: 0;">
        <button class="stepper-btn" style="width: 28px; height: 28px; font-size: 0.9rem;" onclick="updateCartItemQuantity(${item.id}, ${item.quantity - 1})">-</button>
        <span class="stepper-val" style="width: 28px; font-size: 0.9rem;">${item.quantity}</span>
        <button class="stepper-btn" style="width: 28px; height: 28px; font-size: 0.9rem;" onclick="updateCartItemQuantity(${item.id}, ${item.quantity + 1})">+</button>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div class="basket-item-total">₹${item.total_price.toFixed(0)}</div>
        <button class="btn-remove-item" onclick="removeCartItem(${item.id})" title="Remove item">🗑️</button>
      </div>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="modal-header">
      <div class="modal-title"><span>🛒</span> Your Shopping Basket (${state.basket.item_count})</div>
      <button class="modal-close-btn" onclick="closeModal('basket-modal-backdrop')">&times;</button>
    </div>
    <div class="modal-body">
      <div class="basket-items-list">
        ${itemsHtml}
      </div>

      <!-- Coupon Form -->
      <div class="coupon-form">
        <input type="text" id="cart-coupon-input" class="coupon-input" placeholder="Promo code (e.g. DESI10, NAMASTE20, INDIA50)" value="${state.activeCoupon || ''}">
        <button class="btn-apply-coupon" onclick="applyCouponCode()">Apply</button>
      </div>

      <!-- Bill Breakdown -->
      <div class="bill-summary">
        <div class="bill-row">
          <span>Item Subtotal:</span>
          <span>₹${state.basket.subtotal.toFixed(0)}</span>
        </div>
        ${state.basket.discount > 0 ? `
          <div class="bill-row discount-row">
            <span>Promo Discount (${state.activeCoupon}):</span>
            <span>-₹${state.basket.discount.toFixed(0)}</span>
          </div>
        ` : ''}
        <div class="bill-row">
          <span>Standard Delivery (Across India):</span>
          <span style="color: var(--accent-green); font-weight: 700;">FREE</span>
        </div>
        <div class="bill-row total-row">
          <span>Total Payable:</span>
          <span class="total-val">₹${state.basket.total.toFixed(0)}</span>
        </div>
        ${!state.currentUser ? `
          <div style="margin-top: 0.75rem; padding: 0.5rem 0.75rem; background: rgba(255, 152, 0, 0.12); border-left: 3px solid var(--accent-orange); border-radius: 4px; font-size: 0.8rem; color: #ffe082; display: flex; align-items: center; gap: 0.4rem;">
            <span>🔒</span>
            <span>Member sign-in required at checkout for order tracking and GST invoice.</span>
          </div>
        ` : ''}
      </div>

      <button class="btn-primary" onclick="openCheckoutPortal(); closeModal('basket-modal-backdrop');">
        <span>🔒</span> ${state.currentUser ? `Proceed to Indian Payment Gateway (₹${state.basket.total.toFixed(0)})` : `Sign In & Proceed to Checkout (₹${state.basket.total.toFixed(0)})`}
      </button>
    </div>
  `;
}

async function applyCouponCode() {
  const input = document.getElementById('cart-coupon-input');
  if (!input || !input.value.trim()) return;

  const code = input.value.trim().toUpperCase();
  try {
    const res = await fetch(`${API_BASE}/basket/coupon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    const data = await res.json();
    if (data.valid) {
      state.activeCoupon = data.code;
      showToast(data.message, 'success');
      await fetchBasket();
      renderBasketDrawer();
    } else {
      showToast(data.message || 'Invalid coupon', 'error');
    }
  } catch (err) {
    showToast('Failed to apply coupon', 'error');
  }
}

// ==========================================
// Multi-Step Indian Payment Portal (UPI / RuPay / NetBanking)
// ==========================================

let checkoutStep = 1;

function openCheckoutPortal() {
  if (!state.basket.items || state.basket.items.length === 0) {
    showToast('Please add items to your basket before checking out', 'error');
    return;
  }

  if (!state.currentUser) {
    checkoutStep = 0; // Show Member Authentication Gate
  } else {
    state.checkoutData.customer_name = state.currentUser.full_name || 'Aarav Sharma';
    state.checkoutData.email = state.currentUser.email;
    state.checkoutData.address = 'Flat 402, Palm Heights, Bandra West';
    state.checkoutData.city = 'Mumbai';
    state.checkoutData.zip_code = '400050';
    checkoutStep = 1;
  }

  renderCheckoutModal();
  const modal = document.getElementById('checkout-modal-backdrop');
  if (modal) modal.classList.add('active');
}

let checkoutAuthTab = 'login';

function switchCheckoutAuthTab(tab) {
  checkoutAuthTab = tab;
  renderCheckoutModal();
}

async function handleCheckoutInlineLogin(e) {
  e.preventDefault();
  const email = document.getElementById('chk-login-email').value.trim();
  const password = document.getElementById('chk-login-password').value;
  const btn = document.getElementById('btn-chk-login');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = 'Verifying credentials...';
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('access_token', data.access_token);
      state.currentUser = data.user;
      updateAuthUI();
      await fetchBasket();
      state.checkoutData.customer_name = state.currentUser.full_name || state.currentUser.email.split('@')[0];
      state.checkoutData.email = state.currentUser.email;
      showToast(`Welcome ${state.currentUser.full_name}! Continuing to delivery details...`, 'success');
      checkoutStep = 1;
      renderCheckoutModal();
    } else {
      showToast(data.detail || 'Login failed. Please check your credentials.', 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>🔑</span> Sign In & Continue to Checkout';
      }
    }
  } catch (err) {
    showToast('Server connection error', 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>🔑</span> Sign In & Continue to Checkout';
    }
  }
}

async function handleCheckoutInlineRegister(e) {
  e.preventDefault();
  const full_name = document.getElementById('chk-reg-name').value.trim();
  const email = document.getElementById('chk-reg-email').value.trim();
  const password = document.getElementById('chk-reg-password').value;
  const btn = document.getElementById('btn-chk-reg');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = 'Creating account...';
  }

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('access_token', data.access_token);
      state.currentUser = data.user;
      updateAuthUI();
      await fetchBasket();
      state.checkoutData.customer_name = state.currentUser.full_name;
      state.checkoutData.email = state.currentUser.email;
      showToast(`Namaste ${full_name}! Account created.`, 'success');
      checkoutStep = 1;
      renderCheckoutModal();
    } else {
      showToast(data.detail || 'Registration failed.', 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<span>📝</span> Register & Continue';
      }
    }
  } catch (err) {
    showToast('Server connection error', 'error');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>📝</span> Register & Continue';
    }
  }
}

async function quickDemoCheckoutLogin() {
  await quickDemoLogin('customer@juice-sh.op', 'juice123');
  if (state.currentUser) {
    state.checkoutData.customer_name = state.currentUser.full_name;
    state.checkoutData.email = state.currentUser.email;
    state.checkoutData.address = 'Flat 402, Palm Heights, Bandra West';
    state.checkoutData.city = 'Mumbai';
    state.checkoutData.zip_code = '400050';
    checkoutStep = 1;
    renderCheckoutModal();
  }
}

function renderCheckoutModal() {
  const container = document.getElementById('checkout-modal-content');
  if (!container) return;

  let bodyContent = '';

  if (checkoutStep === 0) {
    // Step 0: Professional Authentication Gate (Indian context)
    bodyContent = `
      <div class="checkout-auth-gate">
        <div class="auth-gate-header">
          <div class="auth-gate-icon">🔒</div>
          <div>
            <div class="auth-gate-title">Member Sign-In Required for Purchase</div>
            <div class="auth-gate-subtitle">Please sign in or register to place your order, track delivery, and receive GST tax invoices.</div>
          </div>
        </div>

        <div class="auth-benefits-grid">
          <div class="auth-benefit-item">
            <span class="auth-benefit-icon">✓</span>
            <span>Real-time Indian Live Tracking</span>
          </div>
          <div class="auth-benefit-item">
            <span class="auth-benefit-icon">✓</span>
            <span>GST Digital Invoices</span>
          </div>
          <div class="auth-benefit-item">
            <span class="auth-benefit-icon">✓</span>
            <span>Juice Club ₹ Rewards</span>
          </div>
        </div>

        <!-- Auth Tabs -->
        <div class="auth-tabs" style="border-radius: 6px; overflow: hidden; margin-bottom: 1rem;">
          <button class="auth-tab-btn ${checkoutAuthTab === 'login' ? 'active' : ''}" onclick="switchCheckoutAuthTab('login')">Sign In</button>
          <button class="auth-tab-btn ${checkoutAuthTab === 'register' ? 'active' : ''}" onclick="switchCheckoutAuthTab('register')">Create Free Account</button>
        </div>

        ${checkoutAuthTab === 'login' ? `
          <form onsubmit="handleCheckoutInlineLogin(event)">
            <div class="form-group">
              <label class="form-label">Email Address</label>
              <input type="email" id="chk-login-email" class="form-control" placeholder="customer@juice-sh.op" value="customer@juice-sh.op" required>
            </div>
            <div class="form-group">
              <label class="form-label">Password</label>
              <input type="password" id="chk-login-password" class="form-control" placeholder="••••••••" value="juice123" required>
            </div>
            <button type="submit" class="btn-primary" id="btn-chk-login" style="margin-top: 0.75rem;">
              <span>🔑</span> Sign In & Continue to Checkout
            </button>
          </form>
        ` : `
          <form onsubmit="handleCheckoutInlineRegister(event)">
            <div class="form-group">
              <label class="form-label">Full Name</label>
              <input type="text" id="chk-reg-name" class="form-control" placeholder="Aarav Sharma" required>
            </div>
            <div class="form-group">
              <label class="form-label">Email Address</label>
              <input type="email" id="chk-reg-email" class="form-control" placeholder="aarav@example.com" required>
            </div>
            <div class="form-group">
              <label class="form-label">Password</label>
              <input type="password" id="chk-reg-password" class="form-control" placeholder="Minimum 4 characters" minlength="4" required>
            </div>
            <button type="submit" class="btn-primary" id="btn-chk-reg" style="margin-top: 0.75rem;">
              <span>📝</span> Register & Continue to Checkout
            </button>
          </form>
        `}

        <div style="text-align: center; margin-top: 1rem; border-top: 1px dashed rgba(255,255,255,0.15); padding-top: 0.85rem;">
          <button class="demo-quick-btn" style="width: 100%; padding: 0.55rem; font-size: 0.84rem; background: #3e444b;" onclick="quickDemoCheckoutLogin()">
            <span>⚡</span> 1-Click Instant Demo Login (Aarav Sharma - Mumbai)
          </button>
        </div>
      </div>
    `;
  } else if (checkoutStep === 1) {
    // Step 1: Address in India
    bodyContent = `
      <div class="checkout-steps-indicator">
        <span class="step-pill active">1. Delivery Info (India)</span>
        <span class="step-pill">2. Shipping Speed</span>
        <span class="step-pill">3. Indian Payment</span>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h4 style="color: #fff; font-size: 1.05rem;">Delivery Address in India</h4>
        <div style="display: flex; gap: 0.35rem;">
          <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="autofillIndianAddress('mumbai')">Mumbai</button>
          <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="autofillIndianAddress('bangalore')">Bengaluru</button>
          <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="autofillIndianAddress('delhi')">Delhi</button>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Customer Name</label>
          <input type="text" id="chk-name" class="form-control" value="${state.checkoutData.customer_name}">
        </div>
        <div class="form-group">
          <label class="form-label">Email (Signed In)</label>
          <input type="email" id="chk-email" class="form-control" value="${state.checkoutData.email}" readonly style="opacity: 0.85; background: rgba(0,0,0,0.45);">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Flat / House / Street Address</label>
        <input type="text" id="chk-address" class="form-control" value="${state.checkoutData.address}">
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">City / District</label>
          <input type="text" id="chk-city" class="form-control" value="${state.checkoutData.city}">
        </div>
        <div class="form-group">
          <label class="form-label">PIN Code</label>
          <input type="text" id="chk-zip" class="form-control" maxlength="6" value="${state.checkoutData.zip_code}">
        </div>
      </div>

      <button class="btn-primary" onclick="proceedToStep(2)">
        Continue to Delivery Speed →
      </button>
    `;
  } else if (checkoutStep === 2) {
    // Step 2: Shipping Method (Indian Context)
    bodyContent = `
      <div class="checkout-steps-indicator">
        <span class="step-pill completed">✓ 1. Address</span>
        <span class="step-pill active">2. Delivery Speed</span>
        <span class="step-pill">3. Payment</span>
      </div>

      <h4 style="color: #fff; font-size: 1.05rem; margin-bottom: 1rem;">Choose Indian Delivery Partner</h4>

      <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem;">
        <label style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); border: 1px solid ${state.checkoutData.delivery_fee === 0 ? 'var(--accent-orange)' : 'rgba(255,255,255,0.1)'}; padding: 0.85rem 1rem; border-radius: 8px; cursor: pointer;">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <input type="radio" name="shipping_speed" value="0" ${state.checkoutData.delivery_fee === 0 ? 'checked' : ''} onchange="setDeliverySpeed('Standard Fresh Delivery (Free)', 0.0)">
            <div>
              <div style="font-weight: 600; color: #fff;">Standard Insulated Cold Van (2-3 Days)</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Temperature controlled chilled delivery across India</div>
            </div>
          </div>
          <span style="font-weight: 700; color: var(--accent-green);">FREE</span>
        </label>

        <label style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); border: 1px solid ${state.checkoutData.delivery_fee === 49 ? 'var(--accent-orange)' : 'rgba(255,255,255,0.1)'}; padding: 0.85rem 1rem; border-radius: 8px; cursor: pointer;">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <input type="radio" name="shipping_speed" value="49" ${state.checkoutData.delivery_fee === 49 ? 'checked' : ''} onchange="setDeliverySpeed('Blinkit / Zepto Superfast (Same Day)', 49.0)">
            <div>
              <div style="font-weight: 600; color: #fff;">⚡ Blinkit / Zepto Express (Same Day)</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Priority metro dispatch under 4 hours</div>
            </div>
          </div>
          <span style="font-weight: 700; color: #fff;">₹49</span>
        </label>

        <label style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); border: 1px solid ${state.checkoutData.delivery_fee === 99 ? 'var(--accent-orange)' : 'rgba(255,255,255,0.1)'}; padding: 0.85rem 1rem; border-radius: 8px; cursor: pointer;">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <input type="radio" name="shipping_speed" value="99" ${state.checkoutData.delivery_fee === 99 ? 'checked' : ''} onchange="setDeliverySpeed('Hyperlocal Lightning Delivery (Under 30 Mins)', 99.0)">
            <div>
              <div style="font-weight: 600; color: #fff;">🚀 Swiggy Instamart Hyperlocal (Under 30 Mins)</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Direct refrigerated runner from nearest micro-depot</div>
            </div>
          </div>
          <span style="font-weight: 700; color: #fff;">₹99</span>
        </label>
      </div>

      <div style="display: flex; gap: 0.75rem;">
        <button class="btn-secondary" style="flex: 1;" onclick="proceedToStep(1)">← Back</button>
        <button class="btn-primary" style="flex: 2; margin-top: 0;" onclick="proceedToStep(3)">Continue to Indian Payment →</button>
      </div>
    `;
  } else if (checkoutStep === 3) {
    // Step 3: Indian Payment Gateway (UPI, RuPay, NetBanking, COD)
    const grandTotal = Math.round(state.basket.total + state.checkoutData.delivery_fee);

    let methodFormHtml = '';

    if (state.checkoutData.payment_method === 'UPI / QR') {
      methodFormHtml = `
        <!-- UPI Apps Selector Grid -->
        <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.4rem;">Select UPI App / Wallet</div>
        <div class="upi-app-buttons-grid">
          <button class="upi-app-btn ${state.checkoutData.selected_upi_app === 'Google Pay' ? 'active' : ''}" onclick="selectUPIApp('Google Pay', 'aarav@okaxis')">
            <span>🟢</span> GPay
          </button>
          <button class="upi-app-btn ${state.checkoutData.selected_upi_app === 'PhonePe' ? 'active' : ''}" onclick="selectUPIApp('PhonePe', '9876543210@ybl')">
            <span>🟣</span> PhonePe
          </button>
          <button class="upi-app-btn ${state.checkoutData.selected_upi_app === 'Paytm' ? 'active' : ''}" onclick="selectUPIApp('Paytm', '9876543210@paytm')">
            <span>🔵</span> Paytm
          </button>
          <button class="upi-app-btn ${state.checkoutData.selected_upi_app === 'BHIM UPI' ? 'active' : ''}" onclick="selectUPIApp('BHIM UPI', 'aarav@upi')">
            <span>🇮🇳</span> BHIM
          </button>
        </div>

        <!-- Dynamic QR Box -->
        <div class="upi-qr-box">
          <svg viewBox="0 0 100 100" fill="#212121">
            <rect x="10" y="10" width="25" height="25" fill="#212121"/>
            <rect x="15" y="15" width="15" height="15" fill="#fff"/>
            <rect x="18" y="18" width="9" height="9" fill="#212121"/>
            
            <rect x="65" y="10" width="25" height="25" fill="#212121"/>
            <rect x="70" y="15" width="15" height="15" fill="#fff"/>
            <rect x="73" y="18" width="9" height="9" fill="#212121"/>
            
            <rect x="10" y="65" width="25" height="25" fill="#212121"/>
            <rect x="15" y="70" width="15" height="15" fill="#fff"/>
            <rect x="18" y="73" width="9" height="9" fill="#212121"/>
            
            <rect x="42" y="15" width="15" height="10"/>
            <rect x="42" y="32" width="15" height="35"/>
            <rect x="65" y="45" width="25" height="15"/>
            <rect x="65" y="68" width="12" height="22"/>
            <rect x="80" y="75" width="10" height="15"/>
            <rect x="10" y="42" width="25" height="15"/>
            <rect x="42" y="75" width="15" height="15"/>
          </svg>
          <div style="font-weight: 700; font-size: 0.88rem; color: #212121; margin-top: 0.5rem;">NPCI UPI Fast Scan</div>
          <div style="font-size: 0.72rem; color: #666; font-family: monospace;">UPI ID: juice.shop@okhdfcbank</div>
        </div>

        <div class="form-group">
          <label class="form-label">Or Enter Virtual Payment Address (VPA / UPI ID)</label>
          <input type="text" id="upi-vpa-input" class="form-control" placeholder="yourname@okhdfcbank" value="${state.checkoutData.upi_id}">
        </div>
      `;
    } else if (state.checkoutData.payment_method === 'RuPay / Cards') {
      methodFormHtml = `
        <!-- 3D RuPay Platinum Card Visual Preview -->
        <div class="card-preview-container">
          <div class="card-preview-inner" id="card-3d-element">
            <div class="card-face rupay-theme">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="card-chip"></div>
                <div class="rupay-logo-badge">
                  <span class="rupay-text">RuPay</span>
                  <span class="rupay-arrow">▶</span>
                  <span style="font-size: 0.65rem; color: #ffb74d; text-transform: uppercase;">Platinum</span>
                </div>
              </div>
              <div class="card-number-display" id="card-display-num">${state.checkoutData.card_number}</div>
              <div class="card-meta-display">
                <div>
                  <div style="font-size: 0.65rem; text-transform: uppercase; color: rgba(255,255,255,0.8);">Card Holder</div>
                  <div class="card-holder-name" id="card-display-name">${state.checkoutData.card_holder}</div>
                </div>
                <div>
                  <div style="font-size: 0.65rem; text-transform: uppercase; color: rgba(255,255,255,0.8);">Valid Thru</div>
                  <div class="card-expiry-val" id="card-display-exp">${state.checkoutData.expiry}</div>
                </div>
              </div>
            </div>
            <div class="card-face card-face-back">
              <div class="card-magnetic-strip"></div>
              <div class="card-cvv-band">
                <span id="card-display-cvv">${state.checkoutData.cvv}</span>
              </div>
              <div style="text-align: center; color: #fff; font-size: 0.7rem; margin-top: 0.5rem;">RuPay Verified by Visa/Mastercard • NPCI Safe</div>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">RuPay / Debit / Credit Card Number</label>
          <input type="text" id="card-num-input" class="form-control" maxlength="19" placeholder="6080 3214 5678 9012" value="6080 3214 5678 9012" oninput="updateCardNumber(this.value)">
        </div>

        <div class="form-group">
          <label class="form-label">Name on Card</label>
          <input type="text" id="card-holder-input" class="form-control" placeholder="AARAV SHARMA" value="${state.checkoutData.customer_name}" oninput="updateCardHolder(this.value)">
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Expiry (MM/YY)</label>
            <input type="text" id="card-exp-input" class="form-control" placeholder="MM/YY" maxlength="5" value="12/28" oninput="updateCardExpiry(this.value)">
          </div>
          <div class="form-group">
            <label class="form-label">CVV (3 Digits)</label>
            <input type="password" id="card-cvv-input" class="form-control" placeholder="•••" maxlength="3" value="888" onfocus="flipCard(true)" onblur="flipCard(false)" oninput="updateCardCVV(this.value)">
          </div>
        </div>
      `;
    } else if (state.checkoutData.payment_method === 'Net Banking') {
      methodFormHtml = `
        <div style="font-size: 0.85rem; color: #fff; font-weight: 600; margin-bottom: 0.5rem;">Select Popular Indian Bank</div>
        <div class="indian-banks-grid">
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'State Bank of India (SBI)' ? 'active' : ''}" onclick="selectIndianBank('State Bank of India (SBI)')">
            🏛️ SBI
          </div>
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'HDFC Bank' ? 'active' : ''}" onclick="selectIndianBank('HDFC Bank')">
            🏦 HDFC Bank
          </div>
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'ICICI Bank' ? 'active' : ''}" onclick="selectIndianBank('ICICI Bank')">
            🏦 ICICI Bank
          </div>
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'Axis Bank' ? 'active' : ''}" onclick="selectIndianBank('Axis Bank')">
            🏦 Axis Bank
          </div>
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'Kotak Mahindra Bank' ? 'active' : ''}" onclick="selectIndianBank('Kotak Mahindra Bank')">
            🏦 Kotak Bank
          </div>
          <div class="bank-choice-card ${state.checkoutData.bank_name === 'Punjab National Bank (PNB)' ? 'active' : ''}" onclick="selectIndianBank('Punjab National Bank (PNB)')">
            🏛️ PNB
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Selected Indian NetBanking Gateway</label>
          <input type="text" class="form-control" value="${state.checkoutData.bank_name}" readonly style="background: rgba(0,0,0,0.45); color: var(--accent-orange); font-weight: 600;">
        </div>

        <div style="background: rgba(41, 182, 246, 0.1); border-left: 3px solid var(--accent-blue); padding: 0.75rem; border-radius: 4px; font-size: 0.82rem; color: #b3e5fc; margin-bottom: 1rem;">
          ℹ️ Direct secure authorization via Indian RBI-regulated NetBanking Switch.
        </div>
      `;
    } else {
      methodFormHtml = `
        <div style="text-align: center; padding: 2rem 1rem; background: rgba(0,0,0,0.2); border-radius: 8px; margin: 1rem 0;">
          <div style="font-size: 3rem; margin-bottom: 0.5rem;">💵</div>
          <h4 style="color: #fff;">Cash on Delivery (COD)</h4>
          <p style="color: var(--text-secondary); font-size: 0.88rem; margin-top: 0.25rem;">
            Pay with cash or scan delivery partner's UPI QR code upon arrival at your doorstep.
          </p>
        </div>
      `;
    }

    bodyContent = `
      <div class="checkout-steps-indicator">
        <span class="step-pill completed">✓ 1. Info</span>
        <span class="step-pill completed">✓ 2. Shipping</span>
        <span class="step-pill active">3. Indian Payment (₹${grandTotal})</span>
      </div>

      <!-- Payment Tabs -->
      <div class="payment-tabs">
        <button class="payment-tab-btn ${state.checkoutData.payment_method === 'UPI / QR' ? 'active' : ''}" onclick="selectPaymentMethod('UPI / QR')">
          <span>📱</span> UPI / GPay
        </button>
        <button class="payment-tab-btn ${state.checkoutData.payment_method === 'RuPay / Cards' ? 'active' : ''}" onclick="selectPaymentMethod('RuPay / Cards')">
          <span>💳</span> RuPay / Card
        </button>
        <button class="payment-tab-btn ${state.checkoutData.payment_method === 'Net Banking' ? 'active' : ''}" onclick="selectPaymentMethod('Net Banking')">
          <span>🏦</span> NetBanking
        </button>
        <button class="payment-tab-btn ${state.checkoutData.payment_method === 'Cash on Delivery' ? 'active' : ''}" onclick="selectPaymentMethod('Cash on Delivery')">
          <span>💵</span> COD
        </button>
      </div>

      ${methodFormHtml}

      <div style="display: flex; gap: 0.75rem; margin-top: 1rem;">
        <button class="btn-secondary" style="flex: 1;" onclick="proceedToStep(2)">← Back</button>
        <button class="btn-primary" style="flex: 2; margin-top: 0;" onclick="executeDummyPayment()">
          <span>🔒</span> Pay ₹${grandTotal} & Confirm Order
        </button>
      </div>
    `;
  } else if (checkoutStep === 4) {
    // Step 4: Live Processing Animation
    bodyContent = `
      <div class="processing-overlay">
        <div class="spinner-juice"></div>
        <h3 style="color: #fff; margin-bottom: 0.5rem;" id="proc-stage-title">Contacting Indian Payment Switch (NPCI / Bank)...</h3>
        <p style="color: var(--text-secondary); font-size: 0.9rem;" id="proc-stage-desc">Verifying UPI VPA token and authorizing transaction...</p>
        <div style="margin-top: 1.5rem; display: flex; justify-content: center; gap: 0.5rem;">
          <span style="font-size: 0.78rem; background: rgba(0,0,0,0.3); padding: 0.2rem 0.6rem; border-radius: 4px; color: var(--accent-orange);">256-Bit SSL Encrypted</span>
          <span style="font-size: 0.78rem; background: rgba(0,0,0,0.3); padding: 0.2rem 0.6rem; border-radius: 4px; color: var(--accent-green);">NPCI & RBI Compliant Sandbox</span>
        </div>
      </div>
    `;
  }

  container.innerHTML = `
    <div class="modal-header">
      <div class="modal-title"><span>🛍️</span> Indian Checkout & Payment Gateway</div>
      <button class="modal-close-btn" onclick="closeModal('checkout-modal-backdrop')">&times;</button>
    </div>
    <div class="modal-body">
      ${bodyContent}
    </div>
  `;
}

function autofillIndianAddress(cityKey) {
  if (cityKey === 'mumbai') {
    state.checkoutData.address = 'Flat 402, Palm Heights, Bandra West';
    state.checkoutData.city = 'Mumbai';
    state.checkoutData.zip_code = '400050';
  } else if (cityKey === 'bangalore') {
    state.checkoutData.address = 'No 42, 12th Main Road, Indiranagar';
    state.checkoutData.city = 'Bengaluru';
    state.checkoutData.zip_code = '560038';
  } else if (cityKey === 'delhi') {
    state.checkoutData.address = 'Block B, Connaught Place';
    state.checkoutData.city = 'New Delhi';
    state.checkoutData.zip_code = '110001';
  }

  const addrEl = document.getElementById('chk-address');
  const cityEl = document.getElementById('chk-city');
  const zipEl = document.getElementById('chk-zip');

  if (addrEl) addrEl.value = state.checkoutData.address;
  if (cityEl) cityEl.value = state.checkoutData.city;
  if (zipEl) zipEl.value = state.checkoutData.zip_code;

  showToast(`Loaded ${state.checkoutData.city} address!`, 'info');
}

function proceedToStep(step) {
  if (step === 2) {
    const nameEl = document.getElementById('chk-name');
    const emailEl = document.getElementById('chk-email');
    const addrEl = document.getElementById('chk-address');
    const cityEl = document.getElementById('chk-city');
    const zipEl = document.getElementById('chk-zip');

    if (nameEl) state.checkoutData.customer_name = nameEl.value.trim();
    if (emailEl) state.checkoutData.email = emailEl.value.trim();
    if (addrEl) state.checkoutData.address = addrEl.value.trim();
    if (cityEl) state.checkoutData.city = cityEl.value.trim();
    if (zipEl) state.checkoutData.zip_code = zipEl.value.trim();

    if (!state.checkoutData.customer_name || !state.checkoutData.address || !state.checkoutData.email) {
      showToast('Please fill in your name, address, and city', 'error');
      return;
    }
  }

  checkoutStep = step;
  renderCheckoutModal();
}

function setDeliverySpeed(methodName, fee) {
  state.checkoutData.delivery_method = methodName;
  state.checkoutData.delivery_fee = fee;
  renderCheckoutModal();
}

function selectPaymentMethod(method) {
  state.checkoutData.payment_method = method;
  renderCheckoutModal();
}

function selectUPIApp(appName, defaultVpa) {
  state.checkoutData.selected_upi_app = appName;
  state.checkoutData.upi_id = defaultVpa;
  const input = document.getElementById('upi-vpa-input');
  if (input) input.value = defaultVpa;
  renderCheckoutModal();
  showToast(`Switched to ${appName} UPI!`, 'info');
}

function selectIndianBank(bankName) {
  state.checkoutData.bank_name = bankName;
  renderCheckoutModal();
  showToast(`Selected ${bankName} NetBanking!`, 'info');
}

function flipCard(isFlipped) {
  const card = document.getElementById('card-3d-element');
  if (card) {
    if (isFlipped) card.classList.add('flipped');
    else card.classList.remove('flipped');
  }
}

function updateCardNumber(val) {
  const display = document.getElementById('card-display-num');
  if (display) display.textContent = val || '6080 •••• •••• 9012';
}

function updateCardHolder(val) {
  const display = document.getElementById('card-display-name');
  if (display) display.textContent = val.toUpperCase() || 'AARAV SHARMA';
}

function updateCardExpiry(val) {
  const display = document.getElementById('card-display-exp');
  if (display) display.textContent = val || 'MM/YY';
}

function updateCardCVV(val) {
  const display = document.getElementById('card-display-cvv');
  if (display) display.textContent = val || '•••';
}

async function executeDummyPayment() {
  if (!state.currentUser) {
    showToast('Please sign in or register to complete your purchase', 'error');
    checkoutStep = 0;
    renderCheckoutModal();
    return;
  }

  checkoutStep = 4;
  renderCheckoutModal();

  const titleEl = document.getElementById('proc-stage-title');
  const descEl = document.getElementById('proc-stage-desc');

  setTimeout(() => {
    if (titleEl) titleEl.textContent = 'Authorizing with NPCI UPI / Bank Switch...';
    if (descEl) descEl.textContent = 'Connecting to Indian banking infrastructure...';
  }, 1000);

  setTimeout(() => {
    if (titleEl) titleEl.textContent = 'Payment Approved by Bank!';
    if (descEl) descEl.textContent = 'Generating GST Tax Invoice & alerting bottling facility...';
  }, 2200);

  setTimeout(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/checkout/process`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          customer_name: state.checkoutData.customer_name,
          email: state.checkoutData.email,
          address: state.checkoutData.address,
          city: state.checkoutData.city,
          zip_code: state.checkoutData.zip_code,
          country: 'India',
          delivery_method: state.checkoutData.delivery_method,
          delivery_fee: state.checkoutData.delivery_fee,
          coupon_code: state.activeCoupon,
          payment_method: state.checkoutData.payment_method
        })
      });

      if (res.ok) {
        const order = await res.json();
        await fetchBasket();
        renderOrderConfirmation(order);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Payment failed', 'error');
        if (res.status === 401) {
          checkoutStep = 0;
        } else {
          checkoutStep = 3;
        }
        renderCheckoutModal();
      }
    } catch (err) {
      showToast('Payment processing error', 'error');
      checkoutStep = 3;
      renderCheckoutModal();
    }
  }, 3200);
}

function renderOrderConfirmation(order) {
  const container = document.getElementById('checkout-modal-content');
  if (!container) return;

  const itemsHtml = order.items.map(item => `
    <div style="display: flex; justify-content: space-between; font-size: 0.88rem; margin-bottom: 0.35rem; color: #eceff1;">
      <span>${item.quantity}x ${item.product_name}</span>
      <span>₹${(item.price * item.quantity).toFixed(0)}</span>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="modal-header">
      <div class="modal-title" style="color: var(--accent-green);"><span>🎉</span> Payment Successful!</div>
      <button class="modal-close-btn" onclick="closeModal('checkout-modal-backdrop')">&times;</button>
    </div>
    <div class="modal-body" style="text-align: center;">
      <div style="font-size: 4rem; margin-bottom: 0.5rem; animation: bounce 0.6s ease;">🍹</div>
      <h3 style="color: #fff; margin-bottom: 0.25rem;">Dhanyavaad for Your Order!</h3>
      <p style="color: var(--text-secondary); font-size: 0.9rem;">Your freshly cold-pressed juice order is being packaged under 4°C refrigeration.</p>

      <div class="receipt-card" style="text-align: left;">
        <div class="receipt-header">
          <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">GST Tax Invoice #</div>
          <div class="receipt-order-id">${order.order_number}</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">Payment Ref: ${order.payment_reference}</div>
        </div>

        <div style="margin-bottom: 0.85rem;">
          <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem;">Items Purchased</div>
          ${itemsHtml}
        </div>

        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.5rem;">
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-secondary);">
            <span>Delivery Method:</span>
            <span>${order.delivery_method}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-secondary);">
            <span>Delivery Destination:</span>
            <span>${order.delivery_address}, ${order.city} - ${order.zip_code}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 1.15rem; color: #fff; margin-top: 0.5rem;">
            <span>Total Paid:</span>
            <span style="color: var(--accent-orange);">₹${order.total.toFixed(0)}</span>
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-top: 1.25rem;">
        <button class="btn-secondary" style="flex: 1;" onclick="window.print()">🖨️ Print GST Invoice</button>
        <button class="btn-primary" style="flex: 1; margin-top: 0;" onclick="closeModal('checkout-modal-backdrop')">Continue Shopping</button>
      </div>
    </div>
  `;
}

// ==========================================
// Orders & Profile Modals
// ==========================================

async function openOrdersModal() {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      showToast('Please log in to view your orders', 'error');
      return;
    }

    const res = await fetch(`${API_BASE}/orders`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (res.ok) {
      const orders = await res.json();
      const modalBackdrop = document.getElementById('generic-modal-backdrop');
      const modalContent = document.getElementById('generic-modal-content');

      const ordersListHtml = orders.length > 0 ? orders.map(o => `
        <div class="receipt-card" style="text-align: left; margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; margin-bottom: 0.5rem;">
            <div>
              <span style="font-weight: 700; color: var(--accent-orange); font-family: monospace;">${o.order_number}</span>
              <div style="font-size: 0.78rem; color: var(--text-muted);">${new Date(o.created_at).toLocaleString('en-IN')}</div>
            </div>
            <span style="background: rgba(76, 175, 80, 0.2); color: var(--accent-green); font-size: 0.78rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 4px;">${o.status}</span>
          </div>
          <div style="margin-bottom: 0.5rem;">
            ${o.items.map(i => `<div style="font-size: 0.85rem; color: #eceff1;">${i.quantity}x ${i.product_name} (₹${(i.price * i.quantity).toFixed(0)})</div>`).join('')}
          </div>
          <div style="display: flex; justify-content: space-between; font-weight: 700; color: #fff; font-size: 0.95rem; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.4rem;">
            <span>Total Paid:</span>
            <span style="color: var(--accent-orange);">₹${o.total.toFixed(0)}</span>
          </div>
        </div>
      `).join('') : '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No orders placed yet.</p>';

      modalContent.innerHTML = `
        <div class="modal-header">
          <div class="modal-title"><span>📦</span> My Orders & GST Receipts</div>
          <button class="modal-close-btn" onclick="closeModal('generic-modal-backdrop')">&times;</button>
        </div>
        <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
          ${ordersListHtml}
        </div>
      `;

      modalBackdrop.classList.add('active');
    }
  } catch (err) {
    showToast('Failed to load orders', 'error');
  }
}

function openProfileModal() {
  if (!state.currentUser) return;
  const modalBackdrop = document.getElementById('generic-modal-backdrop');
  const modalContent = document.getElementById('generic-modal-content');

  modalContent.innerHTML = `
    <div class="modal-header">
      <div class="modal-title"><span>👤</span> User Profile</div>
      <button class="modal-close-btn" onclick="closeModal('generic-modal-backdrop')">&times;</button>
    </div>
    <div class="modal-body">
      <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <div style="width: 60px; height: 60px; border-radius: 50%; background: var(--accent-orange); color: #212121; font-size: 1.8rem; font-weight: 700; display: flex; align-items: center; justify-content: center;">
          ${(state.currentUser.full_name || state.currentUser.email)[0].toUpperCase()}
        </div>
        <div>
          <h3 style="color: #fff;">${state.currentUser.full_name || 'Juice Member'}</h3>
          <div style="color: var(--text-muted); font-size: 0.88rem;">${state.currentUser.email}</div>
          <span style="font-size: 0.75rem; background: rgba(0,0,0,0.3); padding: 0.15rem 0.5rem; border-radius: 4px; color: var(--accent-green); text-transform: uppercase;">${state.currentUser.role}</span>
        </div>
      </div>
      <div class="bill-summary" style="margin-bottom: 1.5rem;">
        <div class="bill-row">
          <span>Member Since:</span>
          <span>${new Date(state.currentUser.created_at).toLocaleDateString('en-IN')}</span>
        </div>
        <div class="bill-row">
          <span>Juice Rewards Balance:</span>
          <span style="color: var(--accent-orange); font-weight: 700;">₹450 Cash Points</span>
        </div>
      </div>
      <button class="btn-primary" onclick="closeModal('generic-modal-backdrop')">Close</button>
    </div>
  `;

  modalBackdrop.classList.add('active');
}

// ==========================================
// Event Listeners & UI Helpers
// ==========================================

function setupEventListeners() {
  const accountBtn = document.getElementById('account-dropdown-btn');
  const accountDropdown = document.getElementById('account-dropdown-container');
  if (accountBtn && accountDropdown) {
    accountBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      accountDropdown.classList.toggle('active');
    });
  }

  document.addEventListener('click', () => {
    if (accountDropdown) accountDropdown.classList.remove('active');
  });

  const drawerToggleBtn = document.getElementById('nav-drawer-toggle');
  const drawerOverlay = document.getElementById('drawer-overlay');
  const drawer = document.getElementById('side-drawer');
  if (drawerToggleBtn && drawerOverlay && drawer) {
    drawerToggleBtn.addEventListener('click', () => {
      drawer.classList.add('active');
      drawerOverlay.classList.add('active');
    });
    drawerOverlay.addEventListener('click', () => {
      drawer.classList.remove('active');
      drawerOverlay.classList.remove('active');
    });
  }

  const searchInput = document.getElementById('nav-search-input');
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        state.searchQuery = e.target.value.trim();
        fetchProducts();
      }, 250);
    });
  }

  const catSelect = document.getElementById('category-filter-select');
  if (catSelect) {
    catSelect.addEventListener('change', (e) => {
      state.activeCategory = e.target.value;
      fetchProducts();
    });
  }

  const sortSelect = document.getElementById('sort-by-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      fetchProducts();
    });
  }
}

function closeModal(backdropId) {
  const el = document.getElementById(backdropId);
  if (el) el.classList.remove('active');
}

// ==========================================
// RasAI AI Assistant Chat Controller
// ==========================================

let aiChatOpen = false;
let aiMessages = [];

async function toggleAIChat() {
  const drawer = document.getElementById('ai-chat-drawer');
  if (!drawer) return;

  aiChatOpen = !aiChatOpen;
  if (aiChatOpen) {
    drawer.classList.add('active');
    if (aiMessages.length === 0) {
      initAIChat();
    }
    setTimeout(() => {
      const input = document.getElementById('ai-chat-input');
      if (input) input.focus();
    }, 200);
  } else {
    drawer.classList.remove('active');
  }
}

async function initAIChat() {
  const container = document.getElementById('ai-messages-container');
  if (!container) return;

  // Render initial greeting
  const welcomeMsg = {
    role: 'assistant',
    content: "Namaste! 🙏 I am RasAI, your live Indian Juice Specialist & Pricing Concierge.\n\nAsk me about:\n• Juice Pricing & Best Value Deals (e.g., drinks under ₹150)\n• Ingredients & Farm Origins (Kashmir, Ratnagiri, Wayanad)\n• Active Promo Coupons for checkout (`DESI10`, `INDIA50`)"
  };
  aiMessages = [welcomeMsg];
  renderAIMessagesList();
  fetchAISuggestions();
}

async function fetchAISuggestions() {
  const chipsContainer = document.getElementById('ai-quick-chips');
  if (!chipsContainer) return;

  try {
    const res = await fetch(`${API_BASE}/ai/suggestions`);
    if (res.ok) {
      const data = await res.json();
      chipsContainer.innerHTML = data.suggestions.map(s => `
        <button class="ai-chip-btn" onclick="selectAIChip('${s.replace(/'/g, "\\'")}')">${s}</button>
      `).join('');
    }
  } catch (err) {
    console.error("Failed to load AI suggestions", err);
  }
}

function selectAIChip(promptText) {
  const cleanPrompt = promptText.replace(/^[^\w\s]+/, '').trim();
  const input = document.getElementById('ai-chat-input');
  if (input) {
    input.value = cleanPrompt;
    sendAIChatMessage();
  }
}

function handleAIInputKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendAIChatMessage();
  }
}

function formatAIMarkdown(text) {
  if (!text) return '';
  // Basic markdown parser for bold, code, bullet points
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n\* /g, '<br>• ')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n/g, '<br>');
  return html;
}

function renderAIMessagesList() {
  const container = document.getElementById('ai-messages-container');
  if (!container) return;

  container.innerHTML = aiMessages.map((m, idx) => {
    const isUser = m.role === 'user';
    const avatar = isUser ? '👤' : '✨';
    const formattedText = isUser ? m.content : formatAIMarkdown(m.content);

    let productCardsHtml = '';
    if (m.suggested_products && m.suggested_products.length > 0) {
      productCardsHtml = m.suggested_products.map(p => `
        <div class="ai-product-card-mini">
          <div class="ai-prod-left">
            <div class="ai-prod-img">
              <img src="${p.image_url}" alt="${p.name}">
            </div>
            <div>
              <div class="ai-prod-name">${p.name}</div>
              <div class="ai-prod-price">₹${p.price.toFixed(0)} <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: normal;">• ${p.category}</span></div>
            </div>
          </div>
          <div style="display: flex; gap: 0.3rem;">
            <button class="ai-prod-btn" onclick="openProductDetail(${p.id})">🔍 View</button>
            <button class="ai-prod-btn" style="background: #ff9800; color: #000;" onclick="addToBasket(${p.id}, 1); showToast('Added ${p.name} to basket!', 'success');">🛒 Add</button>
          </div>
        </div>
      `).join('');
    }

    return `
      <div class="ai-msg-row ${isUser ? 'user' : 'assistant'}">
        <div class="ai-msg-avatar">${avatar}</div>
        <div class="ai-msg-bubble">
          <div>${formattedText}</div>
          ${productCardsHtml}
        </div>
      </div>
    `;
  }).join('');

  container.scrollTop = container.scrollHeight;
}

async function sendAIChatMessage() {
  const input = document.getElementById('ai-chat-input');
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  // Add user message
  aiMessages.push({ role: 'user', content: text });
  input.value = '';
  renderAIMessagesList();

  // Show typing indicator
  const container = document.getElementById('ai-messages-container');
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'ai-msg-row assistant';
  typingIndicator.id = 'ai-typing-temp';
  typingIndicator.innerHTML = `
    <div class="ai-msg-avatar">✨</div>
    <div class="ai-msg-bubble ai-typing-indicator">
      <div class="ai-typing-dot"></div>
      <div class="ai-typing-dot"></div>
      <div class="ai-typing-dot"></div>
    </div>
  `;
  container.appendChild(typingIndicator);
  container.scrollTop = container.scrollHeight;

  try {
    const currentProdId = state.selectedProduct ? state.selectedProduct.id : null;
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: aiMessages.map(m => ({ role: m.role, content: m.content })),
        current_product_id: currentProdId
      })
    });

    // Remove typing indicator
    const tempEl = document.getElementById('ai-typing-temp');
    if (tempEl) tempEl.remove();

    if (res.ok) {
      const data = await res.json();
      aiMessages.push({
        role: 'assistant',
        content: data.reply,
        suggested_products: data.suggested_products || []
      });
      renderAIMessagesList();
    } else {
      aiMessages.push({
        role: 'assistant',
        content: "Namaste! Our Indian juice catalog is currently available. You can ask about our cold-pressed prices, active promo coupons (`DESI10`), or pure ingredients!"
      });
      renderAIMessagesList();
    }
  } catch (err) {
    const tempEl = document.getElementById('ai-typing-temp');
    if (tempEl) tempEl.remove();

    aiMessages.push({
      role: 'assistant',
      content: "Namaste! For immediate answers:\n• Cheapest juices: Desi Shikanji (₹99) & Kerala Banana (₹129)\n• Active discount coupon: `DESI10` for 10% OFF\n• 100% cold-pressed with zero preservatives!"
    });
    renderAIMessagesList();
  }
}

function clearAIChat() {
  aiMessages = [];
  initAIChat();
}

