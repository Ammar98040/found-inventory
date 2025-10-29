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
                        ${location.notes ? `<div class="location-details" style="color: #64748b; font-size: 0.85rem; margin-top: 5px; padding: 8px; background: #f1f5f9; border-radius: 6px; border-right: 3px solid #667eea;">
                            📝 ${location.notes}
                        </div>` : ''}
                    </div>
                    <div class="location-actions">
                        <button onclick="highlightLocation(${location.column}, ${location.row})">
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

// متغيرات التحكم بالمستودع
let zoomLevel = 1;
let showOnlyProducts = false;

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
    
    // التحقق من حجم الشاشة
    const isMobile = window.innerWidth <= 768;
    const isVerySmall = window.innerWidth <= 480;
    
    // تحديد أحجام الخلايا بناءً على حجم الشاشة - دقة عالية
    let cellSize, headerCellWidth, headerCellHeight, fontSize, locationFontSize, productFontSize;
    
    if (isVerySmall) {
        cellSize = '40px';
        headerCellWidth = '40px';
        headerCellHeight = '40px';
        fontSize = '0.7rem';
        locationFontSize = '0.45rem';
        productFontSize = '0.5rem';
    } else if (isMobile) {
        cellSize = '45px';
        headerCellWidth = '45px';
        headerCellHeight = '45px';
        fontSize = '0.75rem';
        locationFontSize = '0.5rem';
        productFontSize = '0.55rem';
    } else {
        cellSize = '50px';
        headerCellWidth = '50px';
        headerCellHeight = '50px';
        fontSize = '0.8rem';
        locationFontSize = '0.5rem';
        productFontSize = '0.65rem';
    }
    
    // إنشاء شبكة HTML
    const gridContainer = document.getElementById('warehouse-grid');
    gridContainer.innerHTML = '';
    // CSS مسؤول عن العرض - لا نحتاج to inline styles
    
    // إنشاء رأس الأعمدة
    const headerRow = document.createElement('div');
    headerRow.style.display = 'flex';
    headerRow.style.gap = '0';
    headerRow.classList.add('grid-row');
    
    const cornerCell = document.createElement('div');
    cornerCell.style.cssText = `width: ${headerCellWidth}; height: ${headerCellHeight}; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3; font-size: ${fontSize}; flex-shrink: 0;`;
    headerRow.appendChild(cornerCell);
    
    for (let col = 1; col <= columns; col++) {
        const headerCell = document.createElement('div');
        headerCell.style.cssText = `width: ${cellSize}; height: ${headerCellHeight}; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3; font-size: ${fontSize}; flex-shrink: 0;`;
        headerCell.textContent = col;
        headerCell.classList.add('grid-header-cell');
        headerRow.appendChild(headerCell);
    }
    
    gridContainer.appendChild(headerRow);
    
    // إنشاء الصفوف
    for (let row = 1; row <= rows; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.style.display = 'flex';
        rowDiv.style.gap = '0';
        rowDiv.classList.add('grid-row');
        
        // رأس الصف
        const rowHeader = document.createElement('div');
        rowHeader.style.cssText = `width: ${headerCellWidth}; height: ${cellSize}; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 1px solid #5568d3; font-size: ${fontSize}; flex-shrink: 0;`;
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
            
            // جعل جميع الخلايا بنفس الحجم والتصميم لمنع التداخل - دقة عالية
            cell.style.cssText = `width: ${cellSize}; height: ${cellSize}; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px solid #e2e8f0; flex-shrink: 0; position: relative; overflow: hidden;`;
            cell.classList.add('warehouse-grid-cell');
            
            const locationText = `R${row}C${col}`;
            
            if (hasProduct) {
                // خلية تحتوي على منتج
                cell.classList.add('has-product');
                cell.style.background = '#ef4444';
                cell.style.border = '3px solid #dc2626';
                cell.style.color = 'white';
                cell.style.fontWeight = 'bold';
                cell.style.boxShadow = '0 2px 4px rgba(239, 68, 68, 0.3)';
                
                const product = foundProducts.find(p => 
                    p.locations && p.locations.some(loc => loc.row === row && loc.column === col)
                );
                const location = product.locations.find(loc => loc.row === row && loc.column === col);
                
                // عرض رقم المنتج كامل بتصميم أفضل
                let displayProductText = product.product_number;
                
                // استخدام الأنماط الداخلية للتصميم - تحسين التنسيق
                cell.innerHTML = `
                    <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; width: 100%; padding: 2px; box-sizing: border-box;">
                        <div style="font-size: ${locationFontSize}; color: rgba(255,255,255,0.7); font-weight: bold; line-height: 1.1; margin-bottom: 2px;">${locationText}</div>
                        <div style="font-size: ${productFontSize}; color: white; font-weight: bold; word-break: break-all; overflow-wrap: break-word; max-width: 100%;">${displayProductText}</div>
                    </div>
                `;
                cell.title = `الموقع: R${row}C${col}\nالمنتج: ${product.product_number}\nالكمية: ${product.quantity}`;
                
                // إضافة event listener لعرض تفاصيل المنتج
                cell.addEventListener('click', function() {
                    showProductDetails(product, row, col);
                });
                
                // إضافة cursor pointer للإشارة إلى أنه يمكن النقر
                cell.style.cursor = 'pointer';
            } else {
                // خلية فارغة
                cell.style.background = '#f1f5f9';
                cell.style.color = '#64748b';
                cell.innerHTML = `
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%; padding: 2px; box-sizing: border-box;">
                        <div style="font-size: ${locationFontSize}; font-weight: bold; text-align: center; color: #64748b;">${locationText}</div>
                    </div>
                `;
                cell.title = `الموقع: R${row}C${col}\nموقع فارغ`;
            }
            
            rowDiv.appendChild(cell);
        }
        
        gridContainer.appendChild(rowDiv);
    }
}

// تم حذف دوال العرض البسيط - الآن نعرض الشبكة دائماً على جميع الأحجام بدقة عالية


// تمييز موقع معين
function highlightLocation(column, row) {
    console.log('Highlighting location:', `R${row}C${column}`);
    const gridContainer = document.getElementById('warehouse-grid');
    
    if (!gridContainer) {
        console.error('Grid container not found!');
        alert('يرجى عرض الخريطة أولاً');
        return;
    }
    
    // البحث عن الخلايا بشكل أفضل
    const cells = gridContainer.querySelectorAll('.warehouse-grid-cell');
    
    let found = false;
    
    cells.forEach((cell, index) => {
        const cellText = cell.textContent || cell.innerHTML;
        const cellTitle = cell.title || '';
        
        // البحث عن الموقع المطابق - استخدام row و column
        if (cellText.includes(`R${row}C${column}`) || cellTitle.includes(`R${row}C${column}`)) {
            found = true;
            console.log('Found cell at index:', index);
            
            // حفظ الحالة الأصلية
            const originalStyles = {
                borderColor: cell.style.borderColor || getComputedStyle(cell).borderColor,
                borderWidth: cell.style.borderWidth || getComputedStyle(cell).borderWidth,
                boxShadow: cell.style.boxShadow || getComputedStyle(cell).boxShadow,
                zIndex: cell.style.zIndex || getComputedStyle(cell).zIndex,
                transform: cell.style.transform || getComputedStyle(cell).transform
            };
            
            // تطبيق التأثير الاصفر بشكل مباشر
            cell.style.cssText += 'border: 6px solid #fbbf24 !important; box-shadow: 0 0 25px rgba(251, 191, 36, 1) !important; z-index: 1000 !important; transform: scale(1.2) !important; transition: all 0.3s ease !important;';
            
            console.log('Applied highlight effect');
            
            // إعادة الحالة الأصلية بعد 3 ثواني
            setTimeout(() => {
                const bgColor = cell.style.background;
                
                if (bgColor && (bgColor.includes('#ef4444') || bgColor.includes('239, 68, 68'))) {
                    // خلية تحتوي على منتج - لون أحمر
                    cell.style.border = '3px solid #dc2626';
                } else {
                    // خلية فارغة
                    cell.style.border = '2px solid #e2e8f0';
                }
                
                cell.style.boxShadow = originalStyles.boxShadow;
                cell.style.zIndex = '1';
                cell.style.transform = 'scale(1)';
                
                console.log('Removed highlight effect');
            }, 3000);
            
            // التمرير للموقع
            setTimeout(() => {
                cell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            }, 100);
        }
    });
    
    if (!found) {
        console.error('Cell not found for location:', `R${row}C${column}`);
    }
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
    
    // التحقق من أن جميع المنتجات التي لها كميات مطلوبة قد تم تحديدها
    const productsWithRequestedQty = currentResults.filter(p => 
        p.found && p.requested_quantity && p.requested_quantity > 0
    );
    
    if (productsWithRequestedQty.length > 0) {
        const selectedNumbers = selectedProducts.map(p => p.number);
        const missingProducts = productsWithRequestedQty.filter(p => 
            !selectedNumbers.includes(p.product_number)
        );
        
        if (missingProducts.length > 0) {
            const missingNumbers = missingProducts.map(p => p.product_number).join(', ');
            alert(`⚠️ يجب تحديد جميع المنتجات التي لها كميات مطلوبة!\n\nالمنتجات غير المحددة:\n${missingNumbers}\n\nالمنتجات غير المحددة سيتم تجاهلها ولن تتغير كميتها.`);
            
            // سؤال للمستخدم إذا كان يريد المتابعة
            if (!confirm('هل تريد المتابعة مع المنتجات المحددة فقط؟\nالمنتجات غير المحددة ستبقى كميتها كما هي.')) {
                return;
            }
        }
    }
    
    // التحقق النهائي
    if (!confirm(`هل تريد تأكيد أخذ ${selectedProducts.length} منتج؟\n\nالمنتجات المحددة: ${selectedProducts.map(p => p.number).join(', ')}`)) {
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
            // إظهار إشعار بالنجاح وحفظ الطلبية
            if (data.order_number) {
                alert('✓ تم خصم الكميات بنجاح\n📋 تم حفظ الطلبية في السجل\nرقم الطلبية: ' + data.order_number);
            } else {
                alert('✓ تم خصم الكميات بنجاح');
            }
            
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

// تصدير إلى PDF مع خريطة المستودع
async function exportToPDF() {
    const results = currentResults;
    
    if (!results || results.length === 0) {
        alert('لا توجد نتائج للتصدير');
        return;
    }
    
    // الحصول على معلومات المستودع
    let warehouseData;
    try {
        const response = await fetch('/api/grid/');
        warehouseData = await response.json();
    } catch (error) {
        warehouseData = { rows: 6, columns: 15 };
    }
    
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('l', 'mm', 'a4'); // Landscape
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    
    // نص بسيط بدلاً من النص العربي لتفادي مشاكل الترميز
    const today = new Date().toISOString().split('T')[0];
    
    // العنوان (بدون نص عربي لإصلاح مشكلة الترميز)
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('Warehouse Map', pageWidth / 2, 15, { align: 'center' });
    
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    doc.text(`Date: ${today}`, pageWidth / 2, 23, { align: 'center' });
    doc.text(`Total Products: ${results.length}`, pageWidth / 2, 30, { align: 'center' });
    
    // رسم الخريطة بقياس أكبر وأوضح
    const rows = warehouseData.rows || 6;
    const columns = warehouseData.columns || 15;
    const cellWidth = 16;  
    const cellHeight = 16;
    const gridTotalWidth = columns * cellWidth;
    const gridTotalHeight = rows * cellHeight;
    
    // RTL: حساب البداية من اليمين
    const gridStartX = pageWidth - gridTotalWidth - 15; // من اليمين بمسافة 15mm
    const startX = gridStartX - cellWidth; // بداية الشبكة بدون رأس الصفوف
    const startY = 45;
    
    // تجميع المواقع
    const locationMap = new Map();
    results.forEach(product => {
        if (product.found && product.locations && product.locations.length > 0) {
            product.locations.forEach(loc => {
                const key = `${loc.row},${loc.column}`;
                if (!locationMap.has(key)) {
                    locationMap.set(key, []);
                }
                locationMap.get(key).push(product.product_number);
            });
        }
    });
    
    // RTL: رسم رأس الأعمدة من اليمين إلى اليسار (العمود 15 في أقصى اليمين، والعمود 1 في أقصى اليسار)
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(40, 40, 40);
    for (let col = 1; col <= columns; col++) {
        // RTL: حساب x من اليمين
        const x = gridStartX + (columns - col) * cellWidth;
        // خلفية رمادية للرأس
        doc.setFillColor(241, 245, 249);
        doc.rect(x, startY, cellWidth, cellHeight, 'F');
        // حدود
        doc.setDrawColor(200, 200, 200);
        doc.setLineWidth(0.3);
        doc.rect(x, startY, cellWidth, cellHeight);
        // النص
        doc.text(col.toString(), x + cellWidth/2, startY + 11, { align: 'center' });
    }
    
    // رسم رأس الصفوف والخلايا
    for (let row = 1; row <= rows; row++) {
        // رأس الصف (على اليمين)
        const y = startY + row * cellHeight;
        // خلفية رمادية للرأس
        doc.setFillColor(241, 245, 249);
        doc.rect(gridStartX + columns * cellWidth, y, cellWidth, cellHeight, 'F');
        // حدود
        doc.setDrawColor(200, 200, 200);
        doc.setLineWidth(0.3);
        doc.rect(gridStartX + columns * cellWidth, y, cellWidth, cellHeight);
        // النص
        doc.text(row.toString(), gridStartX + columns * cellWidth + cellWidth/2, y + 11, { align: 'center' });
        
        // RTL: الخلايا من اليمين إلى اليسار
        for (let col = 1; col <= columns; col++) {
            // حساب x من اليمين
            const x = gridStartX + (columns - col) * cellWidth;
            const key = `${row},${col}`;
            const hasProduct = locationMap.has(key);
            
            if (hasProduct) {
                // خلفية خضراء
                doc.setFillColor(16, 185, 129);
                doc.rect(x, y, cellWidth, cellHeight, 'F');
                
                // نص الموقع
                doc.setFontSize(8);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(0, 71, 55);
                doc.text(`R${row}C${col}`, x + cellWidth/2, y + 6, { align: 'center' });
                
                // رقم المنتج
                const products = locationMap.get(key);
                if (products.length > 0) {
                    doc.setFontSize(7);
                    doc.setFont('helvetica', 'normal');
                    doc.text(products[0].substring(0, 6), x + cellWidth/2, y + 12, { align: 'center' });
                }
                
                // حدود خضراء
                doc.setDrawColor(5, 150, 105);
                doc.setLineWidth(0.4);
                doc.rect(x, y, cellWidth, cellHeight);
            } else {
                // خلفية رمادية فاتحة
                doc.setFillColor(248, 250, 252);
                doc.rect(x, y, cellWidth, cellHeight, 'F');
                
                // حدود رمادية
                doc.setDrawColor(226, 232, 240);
                doc.setLineWidth(0.2);
                doc.rect(x, y, cellWidth, cellHeight);
            }
        }
    }
    
    // إضافة مفتاح الألوان في أسفل الصفحة (RTL)
    let yPos = startY + rows * cellHeight + 20;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    
    // RTL: مفتاح بعلامات ملونة (من اليمين)
    let xPos = pageWidth - 80;
    
    // مربع أخضر
    doc.setFillColor(16, 185, 129);
    doc.rect(xPos, yPos, 6, 6, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.text('Has Product', xPos + 9, yPos + 4.5);
    
    yPos += 10;
    // مربع رمادي
    doc.setFillColor(241, 245, 249);
    doc.rect(xPos, yPos, 6, 6, 'F');
    doc.setDrawColor(200, 200, 200);
    doc.setLineWidth(0.2);
    doc.rect(xPos, yPos, 6, 6);
    doc.text('Empty', xPos + 9, yPos + 4.5);
    
    // RTL: ملخص في الجهة اليسرى
    xPos = 20;
    yPos = startY + rows * cellHeight + 20;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('Summary:', xPos, yPos);
    yPos += 8;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.text(`Used Locations: ${locationMap.size}`, xPos, yPos);
    yPos += 6;
    doc.text(`Total Products: ${results.length}`, xPos, yPos);
    
    // حفظ PDF
    const filename = `Warehouse_Map_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(filename);
    
    alert('PDF exported successfully!');
}

// طباعة مواقع المنتجات
function printLocations() {
    const results = currentResults;
    
    if (!results || results.length === 0) {
        alert('لا توجد نتائج للطباعة');
        return;
    }
    
    // إنشاء نافذة طباعة جديدة
    const printWindow = window.open('', '_blank');
    
    const today = new Date().toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    // تجميع المواقع
    const locationMap = new Map();
    
    results.forEach(product => {
        if (product.found && product.locations && product.locations.length > 0) {
            product.locations.forEach(loc => {
                const key = `R${loc.row}C${loc.column}`;
                if (!locationMap.has(key)) {
                    locationMap.set(key, []);
                }
                locationMap.get(key).push({
                    product_number: product.product_number,
                    quantity: product.quantity
                });
            });
        }
    });
    
    // ترتيب المواقع
    const sortedLocations = Array.from(locationMap.entries()).sort((a, b) => {
        const [rowA, colA] = a[0].replace('R', '').replace('C', ',').split(',');
        const [rowB, colB] = b[0].replace('R', '').replace('C', ',').split(',');
        if (rowA !== rowB) return rowA - rowB;
        return colA - colB;
    });
    
    // بناء محتوى HTML
    let htmlContent = `
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>طباعة مواقع المنتجات</title>
            <style>
                @page { margin: 2cm; }
                body {
                    font-family: Arial, sans-serif;
                    direction: rtl;
                    padding: 20px;
                    background: white;
                    color: black;
                }
                .print-header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #000;
                    padding-bottom: 20px;
                }
                .print-header h1 {
                    font-size: 2rem;
                    color: #000;
                    margin: 0;
                }
                .print-item {
                    padding: 15px;
                    margin-bottom: 10px;
                    border: 2px solid #000;
                    border-radius: 8px;
                    page-break-inside: avoid;
                    background: #f9f9f9;
                }
                .print-item strong {
                    font-size: 1.2rem;
                    color: #000;
                }
            </style>
        </head>
        <body>
            <div class="print-header">
                <h1>📦 مواقع المنتجات في المستودع</h1>
                <p style="margin: 10px 0; font-size: 1.2rem;">تاريخ: ${today}</p>
                <p style="margin: 5px 0; font-size: 1rem;">إجمالي المنتجات: ${results.length}</p>
            </div>
    `;
    
    // بناء HTML للمواقع
    sortedLocations.forEach(([locationKey, products]) => {
        const productInfo = products.map(p => 
            `${p.product_number} (${p.quantity} قطعة)`
        ).join(' | ');
        
        htmlContent += `
            <div class="print-item">
                <strong>📍 ${locationKey}</strong><br>
                <span>${productInfo}</span>
            </div>
        `;
    });
    
    // إضافة ملخص
    htmlContent += `
            <div class="print-item" style="background: #f0f0f0;">
                <strong>📊 الملخص</strong><br>
                <span>إجمالي المواقع: ${locationMap.size} | إجمالي المنتجات: ${results.length}</span>
            </div>
        </body>
        </html>
    `;
    
    // كتابة المحتوى للنافذة
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // انتظر ثم طباعة
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// عرض تفاصيل المنتج عند النقر على الخلية
function showProductDetails(product, row, col) {
    // إنشاء modal للتفاصيل
    const modal = document.createElement('div');
    modal.id = 'product-details-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    // حساب الكمية المطلوبة والمتوفرة
    const availableQty = product.quantity || 0;
    const requestedQty = product.requested_quantity || 0;
    const shortage = requestedQty - availableQty;
    
    // تحديد حالة التوفر
    let statusIcon = '✅';
    let statusText = 'متوفر';
    let statusColor = '#10b981';
    let bgColor = '#dcfce7';
    let borderColor = '#22c55e';
    
    if (shortage > 0) {
        statusIcon = '⚠️';
        statusText = 'كمية غير كافية';
        statusColor = '#f59e0b';
        bgColor = '#fef3c7';
        borderColor = '#fbbf24';
    }
    
    if (!product.found) {
        statusIcon = '❌';
        statusText = 'غير موجود';
        statusColor = '#ef4444';
        bgColor = '#fee2e2';
        borderColor = '#f87171';
    }
    
    // محتوى Modal
    modal.innerHTML = `
        <div style="
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            max-width: 500px;
            width: 90%;
            position: relative;
            direction: rtl;
        ">
            <button onclick="this.closest('#product-details-modal').remove()" style="
                position: absolute;
                top: 15px;
                left: 15px;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #64748b;
            ">×</button>
            
            <h2 style="margin-bottom: 20px; color: #1e293b; text-align: center;">📦 تفاصيل المنتج</h2>
            
            <div style="margin-bottom: 15px;">
                <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 5px;">رقم المنتج</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #1e293b; font-family: monospace;">${product.product_number}</div>
            </div>
            
            ${product.name ? `
            <div style="margin-bottom: 15px;">
                <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 5px;">اسم المنتج</div>
                <div style="font-size: 1rem; color: #1e293b;">${product.name}</div>
            </div>
            ` : ''}
            
            <div style="margin-bottom: 15px;">
                <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 5px;">الموقع</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: #667eea; font-family: monospace;">R${row}C${col}</div>
            </div>
            
            <div style="background: ${bgColor}; padding: 20px; border-radius: 8px; border-right: 4px solid ${borderColor}; margin: 20px 0;">
                <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 15px; color: ${statusColor}; text-align: center;">
                    ${statusIcon} ${statusText}
                </div>
                
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="color: #64748b;">الكمية المتوفرة:</span>
                    <strong style="color: #059669; font-size: 1.1rem;">${availableQty} ${availableQty === 1 ? 'حبة' : 'حبات'}</strong>
                </div>
                
                ${requestedQty > 0 ? `
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="color: #64748b;">الكمية المطلوبة:</span>
                    <strong style="color: #1e293b; font-size: 1.1rem;">${requestedQty} ${requestedQty === 1 ? 'حبة' : 'حبات'}</strong>
                </div>
                
                ${shortage > 0 ? `
                <div style="display: flex; justify-content: space-between; padding-top: 10px; border-top: 2px solid ${borderColor};">
                    <span style="color: ${statusColor}; font-weight: bold;">النقص:</span>
                    <strong style="color: ${statusColor}; font-size: 1.2rem;">${shortage} ${shortage === 1 ? 'حبة' : 'حبات'}</strong>
                </div>
                ` : ''}
                ` : ''}
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button onclick="this.closest('#product-details-modal').remove()" style="
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s;
                " onmouseover="this.style.background='#5568d3'" 
                   onmouseout="this.style.background='#667eea'">
                    إغلاق
                </button>
            </div>
        </div>
    `;
    
    // إغلاق عند النقر خارج Modal
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // إضافة Modal إلى الصفحة
    document.body.appendChild(modal);
}
