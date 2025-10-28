let currentGrid = {
    rows: 6,
    columns: 15,
    grid: {}
};

// تحميل الشبكة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    refreshGrid();
});

// تحديث الشبكة
async function refreshGrid() {
    showLoading();
    
    try {
        const response = await fetch('/api/grid/');
        const data = await response.json();
        
        currentGrid = data;
        updateGridDisplay();
        updateInfoPanel();
        
    } catch (error) {
        showError('حدث خطأ أثناء تحميل الشبكة: ' + error.message);
    } finally {
        hideLoading();
    }
}

// عرض الشبكة
function updateGridDisplay() {
    const gridContainer = document.getElementById('warehouse-grid');
    gridContainer.innerHTML = '';
    
    // تعيين تنسيق flex مع عرض محدد للخلايا
    gridContainer.style.display = 'flex';
    gridContainer.style.flexDirection = 'column';
    gridContainer.style.gap = '0';
    
    // إنشاء رأس الأعمدة
    const headerRow = document.createElement('div');
    headerRow.style.display = 'flex';
    headerRow.style.gap = '0';
    
    // الخلية الفارغة في الزاوية
    const cornerCell = document.createElement('div');
    cornerCell.className = 'grid-cell grid-cell-header';
    cornerCell.style.width = '50px';
    cornerCell.style.height = '50px';
    headerRow.appendChild(cornerCell);
    
    // رؤوس الأعمدة
    for (let col = 1; col <= currentGrid.columns; col++) {
        const headerCell = document.createElement('div');
        headerCell.className = 'grid-cell grid-cell-header';
        headerCell.style.width = '50px';
        headerCell.style.height = '50px';
        headerCell.textContent = col;
        headerRow.appendChild(headerCell);
    }
    
    gridContainer.appendChild(headerRow);
    
    // إنشاء الصفوف
    for (let row = 1; row <= currentGrid.rows; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.style.display = 'flex';
        rowDiv.style.gap = '0';
        
        // رأس الصف
        const rowHeader = document.createElement('div');
        rowHeader.className = 'grid-cell grid-cell-header';
        rowHeader.style.width = '50px';
        rowHeader.style.height = '50px';
        rowHeader.textContent = row;
        rowDiv.appendChild(rowHeader);
        
        // الخلايا
        for (let col = 1; col <= currentGrid.columns; col++) {
            const cell = document.createElement('div');
            const key = `${row},${col}`;
            const cellData = currentGrid.grid[key] || {};
            
            cell.className = 'grid-cell';
            cell.style.width = '50px';
            cell.style.height = '50px';
            
            if (cellData.has_products) {
                cell.classList.add('has-products');
                // تصميم محسّن للموقع مع منتج (حجم صغير)
                cell.innerHTML = '<div style="padding: 2px; text-align: center; line-height: 1.2;">' + 
                                '<div style="font-size: 0.5rem; font-weight: bold; color: #059669;">R' + row + 'C' + col + '</div>' +
                                '<div style="font-size: 0.45rem; color: #065f46;">' + (cellData.products && cellData.products.length > 0 ? cellData.products[0].substring(0, 6) : '') + '</div>' +
                                '</div>';
            } else {
                // تصميم واضح للموقع الفارغ
                cell.classList.add('empty');
                cell.innerHTML = '<div style="font-size: 0.6rem; font-weight: bold; color: #94a3b8; text-align: center;">R' + row + 'C' + col + '</div>';
            }
            
            // معلومات عند التحويم
            cell.title = `الموقع: R${row}C${col}${cellData.notes ? '\nملاحظات: ' + cellData.notes : ''}${cellData.has_products && cellData.products ? '\nمنتج: ' + cellData.products.join(', ') : '\nموقع فارغ'}`;
            
            rowDiv.appendChild(cell);
        }
        
        gridContainer.appendChild(rowDiv);
    }
}

// تحديث لوحة المعلومات
function updateInfoPanel() {
    const rows = currentGrid.rows;
    const columns = currentGrid.columns;
    
    document.getElementById('rows-count').textContent = rows;
    document.getElementById('columns-count').textContent = columns;
    
    // حساب إجمالي المواقع
    const totalCells = rows * columns;
    document.getElementById('total-cells').textContent = totalCells;
}

// إضافة صف
async function addRow() {
    if (!confirm('هل تريد إضافة صف جديد؟')) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/add-row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('تم إضافة الصف بنجاح!');
            refreshGrid();
        } else {
            throw new Error(data.error || 'حدث خطأ');
        }
        
    } catch (error) {
        showError('حدث خطأ أثناء إضافة الصف: ' + error.message);
    } finally {
        hideLoading();
    }
}

// إضافة عمود
async function addColumn() {
    if (!confirm('هل تريد إضافة عمود جديد؟')) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/add-column/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('تم إضافة العمود بنجاح!');
            refreshGrid();
        } else {
            throw new Error(data.error || 'حدث خطأ');
        }
        
    } catch (error) {
        showError('حدث خطأ أثناء إضافة العمود: ' + error.message);
    } finally {
        hideLoading();
    }
}

// حذف آخر صف
async function deleteLastRow() {
    if (!confirm('هل تريد حذف آخر صف؟ سيتم حذف جميع المنتجات في هذا الصف!')) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/delete-row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `row=${currentGrid.rows}`
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('تم حذف الصف بنجاح!');
            refreshGrid();
        } else {
            throw new Error(data.error || 'حدث خطأ');
        }
        
    } catch (error) {
        showError('حدث خطأ أثناء حذف الصف: ' + error.message);
    } finally {
        hideLoading();
    }
}

// حذف آخر عمود
async function deleteLastColumn() {
    if (!confirm('هل تريد حذف آخر عمود؟ سيتم حذف جميع المنتجات في هذا العمود!')) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/delete-column/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `column=${currentGrid.columns}`
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('تم حذف العمود بنجاح!');
            refreshGrid();
        } else {
            throw new Error(data.error || 'حدث خطأ');
        }
        
    } catch (error) {
        showError('حدث خطأ أثناء حذف العمود: ' + error.message);
    } finally {
        hideLoading();
    }
}

// إخفاء/إظهار العناصر
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}

