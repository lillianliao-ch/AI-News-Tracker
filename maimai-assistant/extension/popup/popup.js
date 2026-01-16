// Popup 脚本
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Popup loaded');

    // 加载统计数据
    try {
        const result = await chrome.storage.local.get(['maimai_stats', 'maimai_candidates']);

        if (result.maimai_stats) {
            document.getElementById('todayCount').textContent = result.maimai_stats.today || 0;
            document.getElementById('totalCount').textContent = result.maimai_stats.total || 0;
        }
    } catch (e) {
        console.log('加载统计失败');
    }

    // 打开脉脉
    document.getElementById('openMaimaiBtn').addEventListener('click', () => {
        chrome.tabs.create({
            url: 'https://maimai.cn/ent/v41/recruit/talents?tab=1'
        });
    });

    // 导出数据
    document.getElementById('exportBtn').addEventListener('click', async () => {
        try {
            const response = await chrome.runtime.sendMessage({
                type: 'EXPORT_DATA',
                options: { format: 'csv' }
            });

            if (response.success) {
                document.getElementById('statusText').textContent = '导出成功';
            } else {
                document.getElementById('statusText').textContent = response.error || '导出失败';
            }
        } catch (e) {
            document.getElementById('statusText').textContent = '导出失败';
        }
    });

    // 清除数据
    document.getElementById('clearBtn').addEventListener('click', async () => {
        if (confirm('确定要清除所有数据吗？')) {
            try {
                await chrome.runtime.sendMessage({ type: 'CLEAR_DATA' });
                document.getElementById('todayCount').textContent = '0';
                document.getElementById('totalCount').textContent = '0';
                document.getElementById('statusText').textContent = '已清除';
            } catch (e) {
                document.getElementById('statusText').textContent = '清除失败';
            }
        }
    });
});
