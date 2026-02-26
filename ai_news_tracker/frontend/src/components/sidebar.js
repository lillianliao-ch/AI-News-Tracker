// src/components/sidebar.js

// 加载统计信息
async function loadStats() {
    try {
        const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8502';
        const response = await fetch(`${API_URL}/api/stats`);
        const stats = await response.json();

        const totalEl = document.getElementById('totalNews');
        const todayEl = document.getElementById('todayNews');

        if (totalEl) totalEl.textContent = stats.total_news || 0;
        if (todayEl) todayEl.textContent = stats.today_news || 0;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 页面加载时获取统计
loadStats();

// 每30秒更新一次
setInterval(loadStats, 30000);
