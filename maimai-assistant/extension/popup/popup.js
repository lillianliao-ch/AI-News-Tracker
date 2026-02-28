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

    // ========== 服务器设置 ==========
    const apiInput = document.getElementById('apiBaseInput');
    const saveBtn = document.getElementById('saveApiBtn');
    const statusEl = document.getElementById('apiStatus');

    // 加载已保存的 URL
    try {
        const settings = await chrome.storage.sync.get(['apiBaseUrl']);
        if (settings.apiBaseUrl) {
            apiInput.value = settings.apiBaseUrl;
            statusEl.textContent = `当前: ${settings.apiBaseUrl}`;
            statusEl.style.color = '#4a90d9';
        } else {
            apiInput.placeholder = 'http://localhost:8502 (默认)';
            statusEl.textContent = '使用默认地址 localhost:8502';
        }
    } catch (e) {
        console.log('加载设置失败');
    }

    // 保存按钮
    saveBtn.addEventListener('click', async () => {
        const url = apiInput.value.trim();
        if (!url) {
            // 清除自定义设置，恢复默认
            await chrome.storage.sync.remove(['apiBaseUrl']);
            statusEl.textContent = '✅ 已恢复默认 localhost:8502';
            statusEl.style.color = '#4caf50';
            return;
        }

        // 验证 URL 格式
        if (!url.match(/^https?:\/\/.+/)) {
            statusEl.textContent = '❌ 请输入完整地址，如 http://192.168.1.100:8502';
            statusEl.style.color = '#e53935';
            return;
        }

        // 测试连接
        statusEl.textContent = '⏳ 正在测试连接...';
        statusEl.style.color = '#ff9800';

        try {
            const cleanUrl = url.replace(/\/+$/, '');
            const resp = await fetch(`${cleanUrl}/health`, { signal: AbortSignal.timeout(5000) });
            if (resp.ok) {
                await chrome.storage.sync.set({ apiBaseUrl: cleanUrl });
                statusEl.textContent = `✅ 连接成功，已保存`;
                statusEl.style.color = '#4caf50';
            } else {
                statusEl.textContent = `⚠️ 服务器返回 ${resp.status}，已保存`;
                statusEl.style.color = '#ff9800';
                await chrome.storage.sync.set({ apiBaseUrl: cleanUrl });
            }
        } catch (e) {
            statusEl.textContent = `❌ 无法连接: ${e.message}`;
            statusEl.style.color = '#e53935';
            // 仍然保存，因为可能服务器暂时离线
            const cleanUrl = url.replace(/\/+$/, '');
            await chrome.storage.sync.set({ apiBaseUrl: cleanUrl });
            statusEl.textContent += ' (已保存，待服务器启动后生效)';
        }
    });

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

