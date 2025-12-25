/**
 * Suwi - Main JavaScript
 * Cart, favorites, and UI functionality.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            mobileMenuBtn.classList.toggle('active');
        });
    }

    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.3s';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Phone input formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            // Remove non-digits except +
            let value = e.target.value.replace(/[^\d+]/g, '');

            // Ensure starts with + if has digits
            if (value && !value.startsWith('+')) {
                value = '+' + value;
            }

            e.target.value = value;
        });
    });

    // Initialize cart functionality
    initCart();

    // Initialize favorites functionality
    initFavorites();
});

/**
 * CSRF token helper for AJAX requests
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

/**
 * Fetch wrapper with CSRF token
 */
async function fetchWithCSRF(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    return fetch(url, mergedOptions);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close">&times;</button>
    `;

    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => toast.classList.add('show'), 10);

    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    });

    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    }, 3000);
}

/**
 * Update cart badge in header
 */
function updateCartBadge(count) {
    const badge = document.querySelector('.cart-count');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

/**
 * Initialize cart functionality
 */
function initCart() {
    // Add to cart buttons
    document.querySelectorAll('.btn-add-to-cart').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const productId = this.dataset.productId;
            const quantity = this.dataset.quantity || 1;

            addToCart(productId, quantity);
        });
    });
}

/**
 * Add product to cart
 */
function addToCart(productId, quantity = 1) {
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            showToast(data.message, 'success');
        } else {
            showToast('Ошибка при добавлении в корзину', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Ошибка соединения', 'error');
    });
}

/**
 * Initialize favorites functionality
 */
function initFavorites() {
    document.querySelectorAll('.btn-favorite').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const productId = this.dataset.productId;
            toggleFavorite(productId, this);
        });
    });
}

/**
 * Toggle favorite status
 */
function toggleFavorite(productId, button) {
    fetch(`/menu/favorite/toggle/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button state
            if (data.is_favorite) {
                button.classList.add('active');
                button.title = 'Удалить из избранного';
            } else {
                button.classList.remove('active');
                button.title = 'Добавить в избранное';
            }
            showToast(data.message, 'success');
        } else if (data.error === 'login_required') {
            showToast('Войдите, чтобы добавить в избранное', 'warning');
            // Optional: redirect to login
            // window.location.href = '/accounts/login/?next=' + window.location.pathname;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Ошибка соединения', 'error');
    });
}
