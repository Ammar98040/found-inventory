// نظام Live Updates - تحديث فوري بدون إعادة تحميل الصفحة
console.log('✓ Live Updates: النظام يعمل في وضع التحديث الذكي');

// متغيرات للـ Live Updates
let lastProductCount = 0;
let isUpdating = false;

// بدء فحص التحديثات كل 15 ثانية
setInterval(async () => {
    if (isUpdating) return;
    await checkLiveUpdates();
}, 15000); // فحص كل 15 ثانية

// فحص التحديثات بصمت
async function checkLiveUpdates() {
    try {
        isUpdating = true;
        
        // التحقق من عدد المنتجات
        const response = await fetch('/api/get-stats/');
        if (response.ok) {
            const data = await response.json();
            
            // إذا تغير عدد المنتجات، هناك تحديث
            if (data.products_count !== lastProductCount && lastProductCount !== 0) {
                // هناك تحديث!
                notifyLiveUpdate();
                lastProductCount = data.products_count;
            } else if (lastProductCount === 0) {
                lastProductCount = data.products_count;
            }
        }
    } catch (error) {
        // Silently fail
    } finally {
        isUpdating = false;
    }
}

// إشعار بصري للتحديث
function notifyLiveUpdate() {
    // فقط إذا كان المستخدم في صفحات المنتجات أو البحث
    if (window.location.pathname.includes('/products/') || 
        window.location.pathname === '/' ||
        window.location.pathname.includes('/dashboard/')) {
        
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 9999;
            font-weight: bold;
            animation: slideDown 0.3s;
            cursor: pointer;
        `;
        notification.textContent = '⚡ توجد تحديثات جديدة - اضغط للتحديث';
        notification.onclick = () => {
            window.location.reload();
        };
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'fadeOut 0.3s';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
}


// إضافة أنيميشن للتحديث
if (!document.getElementById('auto-refresh-styles')) {
    const style = document.createElement('style');
    style.id = 'auto-refresh-styles';
    style.textContent = `
        @keyframes slideDown {
            from {
                top: -100px;
                opacity: 0;
            }
            to {
                top: 20px;
                opacity: 1;
            }
        }
        
        @keyframes slideIn {
            from {
                right: -300px;
                opacity: 0;
            }
            to {
                right: 20px;
                opacity: 1;
            }
        }
        
        @keyframes fadeOut {
            from {
                opacity: 1;
            }
            to {
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

