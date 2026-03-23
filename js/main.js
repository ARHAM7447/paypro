// Track Now
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
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✅ ${data.name} tracked at ₹${data.current_price}`);
            
            // 🔥 FIXED REDIRECT
            window.location.href = '/my-products';
        } else {
            alert('Error: ' + (data.error || 'Server issue'));
        }
    } catch (err) {
        alert('Backend nahi chal raha? Flask start kar!\n' + err.message);
    }
}


// Load My Products
async function loadMyProducts() {
    const container = document.getElementById('productsList');

    if (!container) return;

    container.innerHTML = '<p class="no-products">Loading your tracked products...</p>';

    try {
        const res = await fetch('/api/my-products');

        if (!res.ok) throw new Error('Failed');

        const products = await res.json();

        container.innerHTML = '';

        if (products.length === 0) {
            container.innerHTML = '<p class="no-products">Abhi koi product track nahi kiya.</p>';
            return;
        }

        products.forEach(p => {
            const card = document.createElement('div');
            card.className = 'product-card';

            card.innerHTML = `
                <h3>${p.name || 'Unknown Product'}</h3>
                <div class="price">₹${p.current_price || 'N/A'}</div>
                <p class="meta">Last checked: ${p.last_updated || 'Recently'}</p>
                <a href="${p.url}" target="_blank">View Product →</a>
            `;

            container.appendChild(card);
        });

    } catch (err) {
        console.error(err);
        container.innerHTML = '<p style="color:red;">Error loading products</p>';
    }
}


// Page Load Detection
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    // 🔥 FIXED
    if (path === '/my-products') {
        loadMyProducts();
    }
});