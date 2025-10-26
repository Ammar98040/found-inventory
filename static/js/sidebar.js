// نافذة Sidebar للملاحة السهلة
let sidebarOpen = false;

// دالة فتح/إغلاق الـ Sidebar
function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (sidebarOpen) {
        sidebar.classList.add('sidebar-open');
        if (overlay) overlay.style.display = 'block';
    } else {
        sidebar.classList.remove('sidebar-open');
        if (overlay) overlay.style.display = 'none';
    }
}

// إغلاق الـ Sidebar عند الضغط على Overlay
document.addEventListener('DOMContentLoaded', function() {
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
    
    // إغلاق بـ Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebarOpen) {
            toggleSidebar();
        }
    });
    
    // تحديث الإحصائيات عند تحميل الصفحة
    updateSidebarStats();
    
    // تحديث الإحصائيات كل 15 ثانية
    setInterval(updateSidebarStats, 15000);
});

// إغلاق الـ Sidebar عند الضغط على رابط
document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                toggleSidebar(); // إغلاق على الجوال
            }
        });
    });
});

// تحديث الإحصائيات الحية
function updateSidebarStats() {
    fetch('/api/get-stats/')
        .then(response => response.json())
        .then(data => {
            // 📦 المنتجات
            // إجمالي
            const productsElement = document.getElementById('stats-products');
            if (productsElement && data.products_count !== undefined) {
                productsElement.textContent = data.products_count;
                productsElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
            
            // لها موقع
            const productsWithLocElement = document.getElementById('stats-products-with-locations');
            if (productsWithLocElement && data.products_with_locations !== undefined) {
                productsWithLocElement.textContent = data.products_with_locations;
                productsWithLocElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
            
            // بدون موقع
            const productsWithoutLocElement = document.getElementById('stats-products-without-locations');
            if (productsWithoutLocElement && data.products_without_locations !== undefined) {
                productsWithoutLocElement.textContent = data.products_without_locations;
                productsWithoutLocElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
            
            // 📍 الأماكن
            // السعة الإجمالية
            const capacityElement = document.getElementById('stats-capacity');
            if (capacityElement) {
                const totalCapacity = data.total_capacity || 0;
                const rows = data.warehouse_rows || 0;
                const columns = data.warehouse_columns || 0;
                capacityElement.textContent = `${totalCapacity} (${rows}×${columns})`;
                capacityElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
            
            // مشغولة
            const occupiedElement = document.getElementById('stats-occupied');
            if (occupiedElement && data.occupied_locations !== undefined) {
                occupiedElement.textContent = data.occupied_locations;
                occupiedElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
            
            // فارغة
            const emptyElement = document.getElementById('stats-empty');
            if (emptyElement && data.empty_locations !== undefined) {
                emptyElement.textContent = data.empty_locations;
                emptyElement.parentElement.parentElement.classList.remove('loading', 'error');
            }
        })
        .catch(error => {
            console.error('خطأ في جلب الإحصائيات:', error);
            // وضع الحالة على "خطأ"
            document.querySelectorAll('.stat-item').forEach(item => {
                item.classList.add('error');
                const valueElement = item.querySelector('.stat-value');
                if (valueElement) {
                    valueElement.textContent = '!';
                }
            });
        });
}

// البحث في الـ Sidebar
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('sidebar-search-input');
    const searchResults = document.getElementById('sidebar-search-results');
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    // قائمة بالروابط
    const linksData = [];
    sidebarLinks.forEach(link => {
        const text = link.querySelector('.text');
        const icon = link.querySelector('.icon');
        if (text && icon) {
            linksData.push({
                text: text.textContent,
                icon: icon.textContent,
                href: link.getAttribute('href'),
                link: link
            });
        }
    });
    
    // البحث
    searchInput.addEventListener('input', function() {
        const query = this.value.trim().toLowerCase();
        const resultsContainer = searchResults;
        
        if (query === '') {
            resultsContainer.classList.remove('show');
            return;
        }
        
        // البحث في الروابط
        const filtered = linksData.filter(item => 
            item.text.toLowerCase().includes(query) ||
            item.icon.includes(query)
        );
        
        // عرض النتائج
        if (filtered.length > 0) {
            resultsContainer.innerHTML = '';
            filtered.forEach(item => {
                const resultItem = document.createElement('div');
                resultItem.className = 'search-result-item';
                resultItem.innerHTML = `
                    <span class="icon">${item.icon}</span>
                    <span class="text">${item.text}</span>
                `;
                resultItem.addEventListener('click', function() {
                    window.location.href = item.href;
                });
                resultsContainer.appendChild(resultItem);
            });
            resultsContainer.classList.add('show');
        } else {
            resultsContainer.innerHTML = '<div class="search-result-item" style="color: #94a3b8; text-align: center;">لا توجد نتائج</div>';
            resultsContainer.classList.add('show');
        }
    });
    
    // إغلاق نتائج البحث عند الضغط خارجها
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('show');
        }
    });
    
    // البحث باستخدام Enter
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const firstResult = searchResults.querySelector('.search-result-item');
            if (firstResult) {
                firstResult.click();
            }
        }
    });
});

