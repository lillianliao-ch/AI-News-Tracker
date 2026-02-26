const refreshBtn = document.getElementById('refreshBtn');
const lastUpdateEl = document.getElementById('lastUpdate');
const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8502';

if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
        // 禁用按钮
        refreshBtn.disabled = true;
        refreshBtn.classList.add('spinning');

        try {
            // 触发后端爬虫
            const response = await fetch(`${API_URL}/api/crawl`, {
                method: 'POST'
            });

            const result = await response.json();

            // 等待几秒后刷新页面
            setTimeout(() => {
                window.location.reload();
            }, 3000);

        } catch (error) {
            console.error('刷新失败:', error);
            refreshBtn.disabled = false;
            refreshBtn.classList.remove('spinning');
            alert('刷新失败，请稍后重试');
        }
    });
}

// 显示最后更新时间
async function updateLastUpdateTime() {
    if (!lastUpdateEl) return;

    try {
        const response = await fetch(`${API_URL}/api/stats`);
        const stats = await response.json();

        if (stats.last_crawl) {
            const lastCrawl = new Date(stats.last_crawl);
            const now = new Date();
            const diffMinutes = Math.floor((now - lastCrawl) / 60000);

            if (diffMinutes < 1) {
                lastUpdateEl.textContent = '刚刚更新';
            } else if (diffMinutes < 60) {
                lastUpdateEl.textContent = `${diffMinutes}分钟前更新`;
            } else {
                lastUpdateEl.textContent = lastCrawl.toLocaleString('zh-CN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        }
    } catch (error) {
        console.error('获取更新时间失败:', error);
    }
}

// 初始化时更新
updateLastUpdateTime();

// 每分钟更新一次
setInterval(updateLastUpdateTime, 60000);
