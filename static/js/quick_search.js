// البحث السريع (Quick Search) - Ctrl+K

let quickSearchOpen = false;

// دالة فتح/إغلاق البحث السريع
function toggleQuickSearch() {
    const overlay = document.getElementById('quick-search-overlay');
    const input = document.getElementById('quick-search-input');
    
    if (!overlay || !input) {
        return;
    }
    
    quickSearchOpen = !quickSearchOpen;
    
    if (quickSearchOpen) {
        overlay.classList.add('show');
        input.focus();
        document.body.style.overflow = 'hidden';
    } else {
        overlay.classList.remove('show');
        document.body.style.overflow = '';
        input.value = '';
    }
}

// استدعاء البحث السريع بـ Ctrl+K
document.addEventListener('keydown', function(e) {
    // Ctrl+K أو Cmd+K على Mac
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        toggleQuickSearch();
    }
    
    // إغلاق بـ Escape
    if (e.key === 'Escape' && quickSearchOpen) {
        toggleQuickSearch();
    }
});

// إغلاق عند الضغط على الـ overlay
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('quick-search-overlay');
    
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                toggleQuickSearch();
            }
        });
    }
});

// البحث في المنتجات والمواقع
async function performQuickSearch(query) {
    if (!query || query.trim() === '') {
        clearQuickSearchResults();
        return;
    }
    
    const resultsDiv = document.getElementById('quick-search-results');
    if (!resultsDiv) return;
    
    resultsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #94a3b8;">جاري البحث...</div>';
    
    try {
        // البحث في المنتجات
        const productsResponse = await fetch(`/api/search-products/?q=${encodeURIComponent(query)}`);
        const productsData = await productsResponse.json();
        
        // البحث في المواقع
        const locationsResponse = await fetch(`/api/search-locations/?q=${encodeURIComponent(query)}`);
        const locationsData = await locationsResponse.json();
        
        // عرض النتائج
        displayQuickSearchResults(productsData, locationsData);
    } catch (error) {
        console.error('خطأ في البحث:', error);
        if (resultsDiv) {
            resultsDiv.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">⚠️</div>
                    <p>حدث خطأ أثناء البحث</p>
                </div>
            `;
        }
    }
}

// عرض نتائج البحث
function displayQuickSearchResults(products, locations) {
    const resultsDiv = document.getElementById('quick-search-results');
    let html = '';
    
    const hasResults = (products && products.length > 0) || (locations && locations.length > 0);
    
    if (!hasResults) {
        html = `
            <div class="no-results">
                <div class="no-results-icon">🔍</div>
                <p>لا توجد نتائج</p>
            </div>
        `;
    } else {
        // المنتجات
        if (products && products.length > 0) {
            html += '<div class="search-result-category">';
            html += '<div class="search-result-category-title">📦 المنتجات</div>';
            
            products.slice(0, 5).forEach(product => {
                const locationText = product.location ? `📍 ${product.location}` : '❌ لا يوجد موقع';
                html += `
                    <div class="search-result-item" onclick="window.location.href='/products/${product.id}/'">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="result-icon">📦</div>
                            <div class="result-content">
                                <div class="result-title">${product.product_number}</div>
                                <div class="result-subtitle">${product.name || 'بدون اسم'}</div>
                            </div>
                            <div class="result-badge">${locationText}</div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // المواقع
        if (locations && locations.length > 0) {
            html += '<div class="search-result-category">';
            html += '<div class="search-result-category-title">📍 الأماكن</div>';
            
            locations.slice(0, 5).forEach(location => {
                const status = location.has_product ? '🟢 مشغول' : '⚪ فارغ';
                html += `
                    <div class="search-result-item" onclick="window.location.href='/locations/${location.id}/'">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div class="result-icon">📍</div>
                            <div class="result-content">
                                <div class="result-title">${location.full_location}</div>
                                <div class="result-subtitle">${status}</div>
                            </div>
                            <div class="result-badge">${location.warehouse}</div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
    }
    
    resultsDiv.innerHTML = html;
}

// مسح النتائج
function clearQuickSearchResults() {
    const resultsDiv = document.getElementById('quick-search-results');
    resultsDiv.innerHTML = '';
}

// استدعاء البحث عند الكتابة
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('quick-search-input');
    
    if (input) {
        input.addEventListener('input', function() {
            const query = this.value.trim();
            performQuickSearch(query);
        });
        
        // إغلاق بـ Enter على النتيجة الأولى
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const firstResult = document.querySelector('.search-result-item');
                if (firstResult) {
                    firstResult.click();
                }
            }
        });
    }
});

