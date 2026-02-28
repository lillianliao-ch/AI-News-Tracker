// Maimai Assistant - Background Service Worker
console.log('🚀 Maimai Assistant Background Service 启动...');

// ========== 状态 ==========
let candidates = [];
let stats = { today: 0, total: 0 };

// ========== 必须在顶层同步注册事件监听器（MV3 要求） ==========

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('📨 Background 收到消息:', message.type);

    switch (message.type) {
        case 'SAVE_DATA':
            _saveData(message.data).then(result => sendResponse(result));
            return true;

        case 'GET_DATA':
            sendResponse({ success: true, data: candidates });
            break;

        case 'GET_STATS':
            sendResponse({ success: true, stats: stats });
            break;

        case 'EXPORT_DATA':
            _exportData(message.options).then(result => sendResponse(result));
            return true;

        case 'CLEAR_DATA':
            _clearData().then(result => sendResponse(result));
            return true;

        case 'INTERCEPT_RESUME_DOWNLOAD':
            _interceptResumeDownload(message.candidateId, message.candidateName, message.apiBase)
                .then(result => sendResponse(result));
            return true;

        default:
            sendResponse({ success: false, error: '未知消息类型' });
    }
});

chrome.runtime.onInstalled.addListener(() => {
    console.log('📦 扩展已安装/更新');
    _loadStorageData();
});

// ========== 初始化：加载存储数据 ==========

async function _loadStorageData() {
    try {
        const result = await chrome.storage.local.get(['maimai_candidates', 'maimai_stats']);
        if (result.maimai_candidates) candidates = result.maimai_candidates;
        if (result.maimai_stats) stats = result.maimai_stats;
        console.log(`📊 加载数据: ${candidates.length} 个候选人`);
    } catch (error) {
        console.error('❌ 加载存储数据失败:', error);
    }
}

// 启动时加载
_loadStorageData();

// ========== 简历下载拦截 ==========

async function _uploadToBackend(blob, fileName, candidateId, candidateName, apiBase) {
    const formData = new FormData();
    formData.append('file', blob, fileName);
    const uploadResp = await fetch(`${apiBase}/api/candidate/${candidateId}/resume-attachment`, {
        method: 'POST',
        body: formData
    });
    const result = await uploadResp.json();
    if (result.success) {
        console.log(`✅ Background: 附件已上传 (${candidateName}) - ${fileName}`);
        return { success: true, fileName };
    } else {
        console.warn(`❌ Background: 后端返回失败:`, result);
        return { success: false, error: result.detail || '后端上传失败' };
    }
}

async function _interceptResumeDownload(candidateId, candidateName, apiBase) {
    console.log(`📎 Background: 开始监听下载 (候选人: ${candidateName}, ID: ${candidateId})`);

    return new Promise((resolve) => {
        let resolved = false;
        const done = (result) => {
            if (resolved) return;
            resolved = true;
            cleanup();
            resolve(result);
        };

        const cleanup = () => {
            try { clearTimeout(timer); } catch (e) { }
            try { chrome.downloads.onCreated.removeListener(onCreated); } catch (e) { }
            try { chrome.downloads.onChanged.removeListener(onChanged); } catch (e) { }
        };

        const timer = setTimeout(() => {
            console.log(`⏰ Background: 下载监听超时 (${candidateName})`);
            done({ success: false, error: '下载监听超时(30s)' });
        }, 30000);

        let capturedDownloadId = null;
        let capturedUrl = null;

        const onCreated = async (item) => {
            try {
                capturedDownloadId = item.id;
                capturedUrl = item.url;
                const urlForName = (item.url || '').split('/').pop().split('?')[0];
                const safeName = urlForName || `${candidateName}_resume.pdf`;
                console.log(`📥 Background: 捕获下载 #${item.id} - url=${(item.url || '').substring(0, 100)} mime=${item.mime}`);

                chrome.downloads.onCreated.removeListener(onCreated);

                if (!item.url || item.url.startsWith('blob:') || item.url.startsWith('data:')) {
                    console.log(`📎 Background: URL 类型为 ${item.url?.substring(0, 10)}，等待下载完成后处理...`);
                    return;
                }

                try {
                    console.log(`📤 Background: 从原始URL获取文件...`);
                    const resp = await fetch(item.url);
                    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                    const blob = await resp.blob();
                    console.log(`📦 Background: 文件大小 ${(blob.size / 1024).toFixed(0)}KB`);
                    const result = await _uploadToBackend(blob, safeName, candidateId, candidateName, apiBase);
                    done(result);
                } catch (err) {
                    console.warn(`⚠️ Background: 从URL获取失败: ${err.message}, 等待下载完成后重试...`);
                }
            } catch (e) {
                console.error(`❌ Background: onCreated异常:`, e);
            }
        };

        const onChanged = async (delta) => {
            try {
                if (resolved) return;
                if (delta.state?.current !== 'complete') return;
                if (capturedDownloadId && delta.id !== capturedDownloadId) return;

                const [item] = await chrome.downloads.search({ id: delta.id });
                if (!item) return;

                const fileName = (item.filename || '').split('/').pop() || `${candidateName}_resume.pdf`;
                console.log(`📥 Background: 下载完成 #${item.id} - ${fileName}`);

                const fetchUrl = capturedUrl || item.url;
                if (!fetchUrl || fetchUrl.startsWith('blob:') || fetchUrl.startsWith('file:')) {
                    console.warn(`❌ Background: 无可用URL，无法上传`);
                    done({ success: false, error: '无可用下载URL' });
                    return;
                }

                const resp = await fetch(fetchUrl);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const blob = await resp.blob();
                console.log(`📦 Background: (onChanged) 文件大小 ${(blob.size / 1024).toFixed(0)}KB`);
                const result = await _uploadToBackend(blob, fileName, candidateId, candidateName, apiBase);
                done(result);
            } catch (err) {
                console.error(`❌ Background: onChanged处理异常:`, err);
                done({ success: false, error: err.message });
            }
        };

        chrome.downloads.onCreated.addListener(onCreated);
        chrome.downloads.onChanged.addListener(onChanged);
    });
}

// ========== 数据管理 ==========

async function _saveData(newCandidates) {
    try {
        const existingIds = new Set(candidates.map(c => c.id));
        const uniqueNew = newCandidates.filter(c => !existingIds.has(c.id));
        candidates = [...candidates, ...uniqueNew];
        stats.total = candidates.length;
        stats.today += uniqueNew.length;
        await chrome.storage.local.set({
            maimai_candidates: candidates,
            maimai_stats: stats
        });
        console.log(`✅ 保存成功，新增 ${uniqueNew.length}，总计 ${candidates.length}`);
        return { success: true, added: uniqueNew.length, total: candidates.length };
    } catch (error) {
        console.error('❌ 保存失败:', error);
        return { success: false, error: error.message };
    }
}

async function _exportData(options = {}) {
    const { format = 'csv' } = options;
    try {
        if (candidates.length === 0) {
            return { success: false, error: '没有数据可导出' };
        }
        const filename = `maimai_candidates_${new Date().toISOString().split('T')[0]}`;
        let data, mimeType, extension;
        if (format === 'json') {
            data = JSON.stringify(candidates, null, 2);
            mimeType = 'application/json';
            extension = 'json';
        } else {
            data = _convertToCSV(candidates);
            mimeType = 'text/csv;charset=utf-8';
            extension = 'csv';
        }
        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);
        await chrome.downloads.download({ url, filename: `${filename}.${extension}`, saveAs: true });
        return { success: true, count: candidates.length };
    } catch (error) {
        console.error('❌ 导出失败:', error);
        return { success: false, error: error.message };
    }
}

function _convertToCSV(data) {
    const headers = ['ID', '姓名', '状态', '年龄', '工作年限', '学历', '所在地', '期望薪资', '期望城市', '期望职位', '标签', '提取时间'];
    const rows = data.map(item => [
        item.id || '', item.name || '', item.status || '', item.age || '',
        item.experience || '', item.education || '', item.location || '',
        item.expectedSalary || '', item.expectedLocation || '', item.expectedPosition || '',
        (item.tags || []).join('|'), item.extractedAt || ''
    ]);
    const BOM = '\uFEFF';
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    return BOM + csvContent;
}

async function _clearData() {
    try {
        candidates = [];
        stats = { today: 0, total: 0 };
        await chrome.storage.local.remove(['maimai_candidates', 'maimai_stats']);
        console.log('✅ 数据已清除');
        return { success: true };
    } catch (error) {
        console.error('❌ 清除失败:', error);
        return { success: false, error: error.message };
    }
}

console.log('✅ Background Service 脚本加载完成');
