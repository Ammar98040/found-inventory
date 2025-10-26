// متغيرات عامة
let currentResults = [];

// عناصر DOM
const searchBtn = document.getElementById('search-btn');
const clearBtn = document.getElementById('clear-btn');
const productNumbersTextarea = document.getElementById('product-numbers');
const resultsSection = document.getElementById('results-section');
const resultsContainer = document.getElementById('results-container');
const resultsCount = document.getElementById('results-count');
const loadingEl = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const warehouseView = document.getElementById('warehouse-view');

// استمع للأحداث
searchBtn.addEventListener('click', handleSearch);
clearBtn.addEventListener('click', handleClear);
productNumbersTextarea.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        handleSearch();
    }
});

// معالج البحث
async function handleSearch() {
    const input = productNumbersTextarea.value.trim();
    
    if (!input) {
        showError('الرجاء إدخال أرقام المنتجات');
        return;
    }
    
    // تنظيف النتائج السابقة
    hideError();
    showLoading();
    
    try {
        // معالجة الإدخال (دعم الكمية)
        const searchData = parseSearchInput(input);
        
        const response = await fetch('/api/search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchData)
        });
        
        const data = await response.json();
        
        if (data.results) {
            currentResults = data.results;
            displayResults(data.results);
            updateResultsCount(data.results);
            drawWarehouse(data.results);
        } else {
            throw new Error('لم يتم إرجاع نتائج من الخادم');
        }
    } catch (error) {
        showError('حدث خطأ أثناء البحث: ' + error.message);
        hideResults();
    } finally {
        hideLoading();
    }
}

// معالجة الإدخال لفصل الأرقام والكميات
function parseSearchInput(input) {
    const lines = input.split('\n').filter(line => line.trim());
    const products = [];
    const seenNumbers = new Set();
    const duplicates = [];
    
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        
        // استخراج رقم المنتج
        let productNumber;
        if (trimmed.includes(':')) {
            const [productNum, quantityStr] = trimmed.split(':');
            productNumber = productNum.trim();
        } else {
            productNumber = trimmed;
        }
        
        // التحقق من التكرار
        if (seenNumbers.has(productNumber)) {
            duplicates.push(productNumber);
            continue;
        }
        
        seenNumbers.add(productNumber);
        
        // فحص إذا كان يحتوي على : (نموذج: PRODUCT-001:10)
        if (trimmed.includes(':')) {
            const [productNum, quantityStr] = trimmed.split(':');
            const quantity = parseInt(quantityStr.trim()) || 0;
            products.push({
                product_number: productNumber,
                quantity: quantity
            });
        } else {
            // بدون كمية
            products.push({
                product_number: productNumber,
                quantity: 0
            });
        }
    }
    
    // إظهار رسالة للأرقام المكررة
    if (duplicates.length > 0) {
        const uniqueDuplicates = [...new Set(duplicates)];
        const message = `⚠️ يوجد أرقام منتج مكررة:\n${uniqueDuplicates.join('\n')}\n\nتم تجاهل التكرارات وسيتم البحث عن كل منتج مرة واحدة فقط.`;
        
        // إظهار تنبيه
        alert(message);
        
        // إظهار رسالة في الواجهة
        showWarning(uniqueDuplicates);
    }
    
    return { products };
}

// إظهار تحذير في الواجهة
function showWarning(duplicates) {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
        errorEl.className = 'alert alert-warning';
        errorEl.style.display = 'block';
        errorEl.innerHTML = `
            <strong>⚠️ أرقام مكررة:</strong><br>
            ${duplicates.map(num => `<code>${num}</code>`).join(', ')}<br>
            <small>تم تجاهلها - سيظهر كل منتج مرة واحدة</small>
        `;
    }
}

// عرض النتائج
function displayResults(results) {
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">لم يتم العثور على منتجات</p>';
        return;
    }
    
    // تطبيق Grid Layout
    resultsContainer.style.display = 'grid';
    resultsContainer.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
    resultsContainer.style.gap = '10px';
    
    results.forEach((product, index) => {
        const card = createProductCard(product, index);
        resultsContainer.appendChild(card);
    });
    
    resultsSection.style.display = 'block';
}

// إنشاء بطاقة منتج
function createProductCard(product, index) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    if (!product.found) {
        card.classList.add('not-found');
    }
    
    // إضافة كلاس للكمية غير كافية
    if (product.found && product.requested_quantity && product.quantity < product.requested_quantity) {
        card.classList.add('low-quantity');
        card.style.background = '#fef2f2';
        card.style.borderColor = '#ef4444';
    }
    
    let locationsHtml = '';
    if (product.found && product.locations && product.locations.length > 0) {
        locationsHtml = '<div class="locations-list">';
        locationsHtml += '<h4>📍 الأماكن:</h4>';
        
        product.locations.forEach((location, idx) => {
            locationsHtml += `
                <div class="location-item">
                    <div class="location-info">
                        <div class="location-id">${location.full_location}</div>
                        ${location.notes ? `<div class="location-details">${location.notes}</div>` : ''}
                    </div>
                    <div class="location-actions">
                        <button onclick="highlightLocation(${location.x}, ${location.y})">
                            🔍 عرض على الخريطة
                        </button>
                    </div>
                </div>
            `;
        });
        
        locationsHtml += '</div>';
    } else if (product.found) {
        locationsHtml = '<p style="color: var(--error-color);">لا يوجد مواقع مسجلة لهذا المنتج</p>';
    }
    
    // معلومات الكمية
    let quantityInfo = '';
    if (product.found) {
        if (product.requested_quantity) {
            const shortage = product.requested_quantity - product.quantity;
            if (shortage > 0) {
                quantityInfo = `
                    <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 15px 0; border-right: 4px solid #ef4444;">
                        <div style="color: #991b1b; font-weight: bold; margin-bottom: 5px;">⚠️ الكمية غير كافية</div>
                        <div style="color: #991b1b;">
                            المطلوب: <strong>${product.requested_quantity}</strong> | 
                            المتوفر: <strong>${product.quantity}</strong> | 
                            النقص: <strong style="color: #dc2626;">${shortage}</strong>
                        </div>
                    </div>
                `;
            } else {
                quantityInfo = `
                    <div style="background: #dcfce7; padding: 15px; border-radius: 8px; margin: 15px 0; border-right: 4px solid #10b981;">
                        <div style="color: #065f46; font-weight: bold; margin-bottom: 5px;">✓ الكمية متوفرة</div>
                        <div style="color: #047857;">
                            المطلوب: <strong>${product.requested_quantity}</strong> | 
                            المتوفر: <strong>${product.quantity}</strong>
                        </div>
                    </div>
                `;
            }
        }
    }
    
    card.innerHTML = `
        <div class="product-header">
            <div class="product-info" style="display: flex; align-items: center; gap: 10px; flex: 1;">
                ${product.found ? `
                    <input type="checkbox" id="product-${index}" 
                           onchange="handleProductCheck(${index}, '${product.product_number}', ${product.quantity}, ${product.requested_quantity || 0})"
                           style="width: 18px; height: 18px; cursor: pointer;">
                ` : ''}
                <div style="flex: 1;">
                    <h3 style="margin: 0; font-size: 1rem;">
                        <span class="product-number">${product.product_number}</span>
                        ${product.name ? `<span class="product-name"> - ${product.name}</span>` : ''}
                    </h3>
                    ${product.category ? `<p style="color: var(--text-secondary); font-size: 0.85rem; margin: 3px 0;">فئة: ${product.category}</p>` : ''}
                </div>
            </div>
            <span class="status ${product.found ? 'found' : 'not-found'}" style="font-size: 0.85rem;">
                ${product.found ? '✓ موجود' : '✗ غير موجود'}
            </span>
        </div>
        ${quantityInfo}
        ${locationsHtml}
        ${!product.found ? `<p style="color: var(--error-color); margin-top: 10px; font-size: 0.85rem;">${product.error || 'لم يتم العثور على هذا المنتج'}</p>` : ''}
    `;
    
    // إضافة تأثير الظهور
    setTimeout(() => {
        card.style.opacity = '1';
    }, index * 50);
    
    return card;
}

// تحديث عدد النتائج
function updateResultsCount(results) {
    const foundCount = results.filter(r => r.found).length;
    const totalCount = results.length;
    
    resultsCount.textContent = `تم العثور على ${foundCount} من أصل ${totalCount}`;
}

// رسم خريطة المستودع - الحصول على البيانات من السيرفر
async function drawWarehouse(results) {
    const foundProducts = results.filter(p => p.found && p.locations && p.locations.length > 0);
    
    if (foundProducts.length === 0) {
        warehouseView.style.display = 'none';
        return;
    }
    
    warehouseView.style.display = 'block';
    
    // الحصول على أبعاد المستودع من السيرفر
    let warehouseData;
    try {
        const response = await fetch('/api/grid/');
        warehouseData = await response.json();
    } catch (error) {
        console.error('Error fetching warehouse data:', error);
        warehouseData = { rows: 6, columns: 15 };
    }
    
    const rows = warehouseData.rows || 6;
    const columns = warehouseData.columns || 15;
    const grid = warehouseData.grid || {};
    
    // إنشاء شبكة HTML
    const gridContainer = document.getElementById('warehouse-grid');
    gridContainer.innerHTML = '';
    gridContainer.style.display = 'flex';
    gridContainer.style.flexDirection = 'column';
    gridContainer.style.gap = '0';
    
    // إنشاء رأس الأعمدة
    const headerRow = document.createElement('div');
    headerRow.style.display = 'flex';
    headerRow.style.gap = '0';
    
    const cornerCell = document.createElement('div');
    cornerCell.style.cssText = 'width: 50px; height: 50px; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3;';
    headerRow.appendChild(cornerCell);
    
    for (let col = 1; col <= columns; col++) {
        const headerCell = document.createElement('div');
        headerCell.style.cssText = 'width: 80px; height: 50px; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3;';
        headerCell.textContent = col;
        headerRow.appendChild(headerCell);
    }
    
    gridContainer.appendChild(headerRow);
    
    // إنشاء الصفوف
    for (let row = 1; row <= rows; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.style.display = 'flex';
        rowDiv.style.gap = '0';
        
        // رأس الصف
        const rowHeader = document.createElement('div');
        rowHeader.style.cssText = 'width: 50px; height: 80px; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3;';
        rowHeader.textContent = row;
        rowDiv.appendChild(rowHeader);
        
        // الخلايا
        for (let col = 1; col <= columns; col++) {
            const cell = document.createElement('div');
            const key = `${row},${col}`;
            const cellData = grid[key] || {};
            const hasProduct = foundProducts.some(p => 
                p.locations && p.locations.some(loc => loc.row === row && loc.column === col)
            );
            
            cell.style.cssText = 'width: 80px; height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px solid #e2e8f0;';
            
            if (hasProduct) {
                cell.style.background = '#34d399';
                cell.style.borderColor = '#059669';
                // العثور على المنتج في هذا الموقع
                const product = foundProducts.find(p => 
                    p.locations && p.locations.some(loc => loc.row === row && loc.column === col)
                );
                const location = product.locations.find(loc => loc.row === row && loc.column === col);
                
                cell.innerHTML = '<div style="padding: 5px; text-align: center; line-height: 1.3; width: 100%;">' + 
                                '<div style="background: #ffffff; color: #059669; padding: 3px 5px; border-radius: 3px; margin-bottom: 4px; font-size: 0.65rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">' + `R${row}C${col}` + '</div>' +
                                '<div style="background: #f0fdf4; color: #065f46; padding: 3px 5px; border-radius: 3px; font-size: 0.6rem; font-weight: bold; border: 1px solid #10b981;">' + product.product_number + '</div>' +
                                '</div>';
                cell.title = `الموقع: R${row}C${col}\nالمنتج: ${product.product_number}`;
            } else {
                cell.style.background = '#f1f5f9';
                cell.style.color = '#64748b';
                cell.innerHTML = '<div style="font-size: 0.7rem; font-weight: bold; color: #94a3b8; text-align: center; padding-top: 8px;">' + `R${row}C${col}` + '</div>';
                cell.title = `الموقع: R${row}C${col}\nموقع فارغ`;
            }
            
            rowDiv.appendChild(cell);
        }
        
        gridContainer.appendChild(rowDiv);
    }
}

// تمييز موقع معين
function highlightLocation(x, y) {
    const gridContainer = document.getElementById('warehouse-grid');
    const cells = gridContainer.querySelectorAll('div[style*="width: 80px"]');
    
    cells.forEach(cell => {
        const cellText = cell.textContent;
        if (cellText.includes(`R${y}C${x}`)) {
            cell.style.borderColor = '#ef4444';
            cell.style.borderWidth = '5px';
            cell.style.transition = 'all 0.3s';
            
            setTimeout(() => {
                cell.style.borderColor = cell.style.background === '#34d399' ? '#059669' : '#e2e8f0';
                cell.style.borderWidth = '2px';
            }, 2000);
        }
    });
    
    gridContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// معالج المسح
function handleClear() {
    productNumbersTextarea.value = '';
    hideResults();
    hideError();
}

// معالجة تحديد المنتجات
let selectedProducts = [];

function handleProductCheck(index, productNumber, availableQuantity, requestedQuantity) {
    const checkbox = document.getElementById(`product-${index}`);
    const isChecked = checkbox.checked;
    
    if (isChecked) {
        // إضافة المنتج للمحددة
        if (!selectedProducts.find(p => p.number === productNumber)) {
            selectedProducts.push({
                number: productNumber,
                quantity: requestedQuantity || availableQuantity,
                index: index
            });
        }
    } else {
        // إزالة المنتج من المحددة
        selectedProducts = selectedProducts.filter(p => p.number !== productNumber);
    }
    
    updateConfirmButton();
}

// تحديث زر التأكيد
function updateConfirmButton() {
    let existingBtn = document.getElementById('confirm-selected-btn');
    
    if (selectedProducts.length > 0 && !existingBtn) {
        const btn = document.createElement('button');
        btn.id = 'confirm-selected-btn';
        btn.className = 'btn btn-primary';
        btn.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1000; padding: 15px 30px; font-size: 1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3);';
        btn.innerHTML = `✓ تأكيد أخذ المنتجات (${selectedProducts.length})`;
        btn.onclick = confirmSelectedProducts;
        document.body.appendChild(btn);
    } else if (existingBtn) {
        if (selectedProducts.length > 0) {
            existingBtn.innerHTML = `✓ تأكيد أخذ المنتجات (${selectedProducts.length})`;
            existingBtn.style.display = 'block';
        } else {
            existingBtn.style.display = 'none';
        }
    }
    
    if (selectedProducts.length === 0 && existingBtn) {
        existingBtn.remove();
    }
}

// تأكيد أخذ المنتجات
async function confirmSelectedProducts() {
    if (selectedProducts.length === 0) {
        alert('لم يتم تحديد أي منتج');
        return;
    }
    
    if (!confirm(`هل تريد تأكيد أخذ ${selectedProducts.length} منتج؟`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/confirm-products/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ products: selectedProducts })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✓ تم خصم الكميات بنجاح');
            // إزالة المنتجات المأخوذة
            selectedProducts.forEach(product => {
                const checkbox = document.getElementById(`product-${product.index}`);
                if (checkbox) checkbox.checked = false;
            });
            selectedProducts = [];
            updateConfirmButton();
            // إعادة البحث لتحديث الكميات
            handleSearch();
        } else {
            alert('✗ خطأ: ' + (data.error || 'حدث خطأ'));
        }
    } catch (error) {
        alert('✗ خطأ: ' + error.message);
    }
}

// إخفاء/إظهار العناصر
function showLoading() {
    loadingEl.style.display = 'block';
    searchBtn.disabled = true;
}

function hideLoading() {
    loadingEl.style.display = 'none';
    searchBtn.disabled = false;
}

function hideResults() {
    resultsSection.style.display = 'none';
    warehouseView.style.display = 'none';
    resultsContainer.innerHTML = '';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.className = 'alert alert-error';
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
    errorMessage.textContent = '';
}

function showWarning(duplicates) {
    if (duplicates && duplicates.length > 0) {
        errorMessage.innerHTML = `
            <strong>⚠️ أرقام مكررة:</strong><br>
            ${duplicates.map(num => `<code>${num}</code>`).join(', ')}<br>
            <small>تم تجاهلها - سيظهر كل منتج مرة واحدة</small>
        `;
        errorMessage.className = 'alert alert-warning';
        errorMessage.style.display = 'block';
        
        // إخفاء التحذير بعد 5 ثوان
        setTimeout(() => {
            if (errorMessage.className.includes('alert-warning')) {
                hideError();
            }
        }, 5000);
    }
}

