// js/main.js - PriceTrack JavaScript

// Track Now (index.html / discover.html ke liye)
async function trackProduct() {
    const urlInput = document.getElementById('product-url');

    if (!urlInput) {
        alert("URL input nahi mila – page check kar!");
        return;
    }

    const url = urlInput.value.trim();

    if (!url) {
        alert("Product URL paste karo pehle!");
        return;
    }

    if (!url.startsWith('http') || (!url.includes('amazon') && !url.includes('flipkart') && !url.includes('myntra'))) {
        alert("Valid Amazon, Flipkart ya Myntra URL daalo!");
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Success! ${data.name} tracked at ₹${data.current_price}`);
            window.location.href = 'my-products.html';
        } else {
            alert('Error: ' + (data.error || 'Server issue'));
        }
    } catch (err) {
        alert('Backend nahi chal raha? Flask start kar!\n' + err.message);
    }
}

// My Products list load karo
async function loadMyProducts() {
    const container = document.getElementById('productsList');

    if (!container) return;

    container.innerHTML = '<p class="no-products">Loading your tracked products...</p>';

    try {
        const res = await fetch('http://localhost:5000/api/my-products');
        if (!res.ok) {
            throw new Error('Failed to fetch products');
        }

        const products = await res.json();

        container.innerHTML = '';

        if (products.length === 0) {
            container.innerHTML = '<p class="no-products">Abhi koi product track nahi kiya. Home page se shuru karo!</p>';
            return;
        }

        products.forEach(p => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <h3>${p.name || 'Unknown Product'}</h3>
                <div class="price">₹${p.current_price?.toLocaleString() || 'N/A'}</div>
                <p class="meta">Last checked: ${p.last_updated || 'Recently'}</p>
                <a href="${p.url}" target="_blank" class="link">View on Site →</a>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error('Load error:', err);
        container.innerHTML = '<p class="no-products" style="color:red;">Error loading products. Refresh karo ya backend check karo.</p>';
    }
}

// Page load pe sahi function call
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    if (path.includes('my-products.html') || path.endsWith('my-products.html')) {
        loadMyProducts();
    }
    // Agar track button wale page pe event listener chahiye to yahan add kar sakte hain
});