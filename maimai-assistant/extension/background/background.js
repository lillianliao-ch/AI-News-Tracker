// Maimai Assistant - Background Service Worker
console.log('🚀 Maimai Assistant Background Service 启动...');

class BackgroundService {
    constructor() {
        this.candidates = [];
        this.stats = {
            today: 0,
            total: 0
        };
    }

    async init() {
        console.log('📦 初始化 Background Service...');

        // 加载存储数据
        await this.loadStorageData();

        // 设置消息监听
        this.setupMessageListeners();

        console.log('✅ Background Service 初始化完成');
    }

    // 加载存储数据
    async loadStorageData() {
        try {
            const result = await chrome.storage.local.get(['maimai_candidates', 'maimai_stats']);

            if (result.maimai_candidates) {
                this.candidates = result.maimai_candidates;
            }

            if (result.maimai_stats) {
                this.stats = result.maimai_stats;
            }

            console.log(`📊 加载数据: ${this.candidates.length} 个候选人`);
        } catch (error) {
            console.error('❌ 加载存储数据失败:', error);
        }
    }

    // 设置消息监听
    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            console.log('📨 Background 收到消息:', message.type);

            switch (message.type) {
                case 'SAVE_DATA':
                    this.saveData(message.data).then(result => sendResponse(result));
                    return true;

                case 'GET_DATA':
                    sendResponse({ success: true, data: this.candidates });
                    break;

                case 'GET_STATS':
                    sendResponse({ success: true, stats: this.stats });
                    break;

                case 'EXPORT_DATA':
                    this.exportData(message.options).then(result => sendResponse(result));
                    return true;

                case 'CLEAR_DATA':
                    this.clearData().then(result => sendResponse(result));
                    return true;

                case 'INTERCEPT_RESUME_DOWNLOAD':
                    this.interceptResumeDownload(message.candidateId, message.candidateName, message.apiBase)
                        .then(result => sendResponse(result));
                    return true;

                default:
                    sendResponse({ success: false, error: '未知消息类型' });
            }
        });
    }

    // 拦截简历下载并上传到后端
    async interceptResumeDownload(candidateId, candidateName, apiBase) {
        console.log(`📎 Background: 开始监听下载 (候选人: ${candidateName}, ID: ${candidateId})`);

        return new Promise((resolve) => {
            const timeout = setTimeout(() => {
                chrome.downloads.onChanged.removeListener(onChanged);
                console.log(`⏰ Background: 下载监听超时 (${candidateName})`);
                resolve({ success: false, error: '下载监听超时' });
            }, 30000); // 30 秒超时

            const onChanged = async (delta) => {
                // 只关心下载完成的事件
                if (!delta.state || delta.state.current !== 'complete') return;

                try {
                    // 获取下载项详情
                    const [item] = await chrome.downloads.search({ id: delta.id });
                    if (!item) return;

                    console.log(`📥 Background: 下载完成 - ${item.filename}`);

                    // 检查是否是简历文件（PDF/DOC）
                    const fileName = item.filename.split('/').pop() || item.filename.split('\\').pop();
                    const isResumeFile = /\.(pdf|doc|docx)$/i.test(fileName);
                    if (!isResumeFile) {
                        console.log(`  ⏭️ 非简历文件，跳过: ${fileName}`);
                        return;
                    }

                    // 清理监听器
                    clearTimeout(timeout);
                    chrome.downloads.onChanged.removeListener(onChanged);

                    // 获取文件内容：通过 file:// URL 读取
                    const fileUrl = item.url || `file://${item.filename}`;
                    console.log(`📤 Background: 上传附件到后端... (${fileName})`);

                    try {
                        // 用 fetch 获取下载的文件
                        const response = await fetch(fileUrl);
                        const blob = await response.blob();

                        // 上传到后端
                        const formData = new FormData();
                        formData.append('file', blob, fileName);
                        const uploadResp = await fetch(`${apiBase}/api/candidate/${candidateId}/resume-attachment`, {
                            method: 'POST',
                            body: formData
                        });
                        const result = await uploadResp.json();

                        if (result.success) {
                            console.log(`✅ Background: 附件已上传 (${candidateName}) - ${fileName}`);
                            resolve({ success: true, fileName });
                        } else {
                            console.warn(`❌ Background: 上传失败:`, result);
                            resolve({ success: false, error: result.detail || '上传失败' });
                        }
                    } catch (uploadErr) {
                        console.error(`❌ Background: 上传异常:`, uploadErr);
                        resolve({ success: false, error: uploadErr.message });
                    }
                } catch (err) {
                    console.error(`❌ Background: 处理下载事件异常:`, err);
                }
            };

            chrome.downloads.onChanged.addListener(onChanged);
        });
    }

    // 保存数据
    async saveData(newCandidates) {
        try {
            // 去重合并
            const existingIds = new Set(this.candidates.map(c => c.id));
            const uniqueNew = newCandidates.filter(c => !existingIds.has(c.id));

            this.candidates = [...this.candidates, ...uniqueNew];
            this.stats.total = this.candidates.length;
            this.stats.today += uniqueNew.length;

            // 保存到 storage
            await chrome.storage.local.set({
                maimai_candidates: this.candidates,
                maimai_stats: this.stats
            });

            console.log(`✅ 保存成功，新增 ${uniqueNew.length}，总计 ${this.candidates.length}`);

            return {
                success: true,
                added: uniqueNew.length,
                total: this.candidates.length
            };
        } catch (error) {
            console.error('❌ 保存失败:', error);
            return { success: false, error: error.message };
        }
    }

    // 导出数据
    async exportData(options = {}) {
        const { format = 'csv' } = options;

        try {
            if (this.candidates.length === 0) {
                return { success: false, error: '没有数据可导出' };
            }

            const filename = `maimai_candidates_${new Date().toISOString().split('T')[0]}`;
            let data, mimeType, extension;

            if (format === 'json') {
                data = JSON.stringify(this.candidates, null, 2);
                mimeType = 'application/json';
                extension = 'json';
            } else {
                data = this.convertToCSV(this.candidates);
                mimeType = 'text/csv;charset=utf-8';
                extension = 'csv';
            }

            // 创建下载
            const blob = new Blob([data], { type: mimeType });
            const url = URL.createObjectURL(blob);

            await chrome.downloads.download({
                url: url,
                filename: `${filename}.${extension}`,
                saveAs: true
            });

            return { success: true, count: this.candidates.length };
        } catch (error) {
            console.error('❌ 导出失败:', error);
            return { success: false, error: error.message };
        }
    }

    // 转换为 CSV
    convertToCSV(data) {
        const headers = ['ID', '姓名', '状态', '年龄', '工作年限', '学历', '所在地', '期望薪资', '期望城市', '期望职位', '标签', '提取时间'];

        const rows = data.map(item => [
            item.id || '',
            item.name || '',
            item.status || '',
            item.age || '',
            item.experience || '',
            item.education || '',
            item.location || '',
            item.expectedSalary || '',
            item.expectedLocation || '',
            item.expectedPosition || '',
            (item.tags || []).join('|'),
            item.extractedAt || ''
        ]);

        // BOM for Excel UTF-8
        const BOM = '\uFEFF';
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        ].join('\n');

        return BOM + csvContent;
    }

    // 清除数据
    async clearData() {
        try {
            this.candidates = [];
            this.stats = { today: 0, total: 0 };

            await chrome.storage.local.remove(['maimai_candidates', 'maimai_stats']);

            console.log('✅ 数据已清除');
            return { success: true };
        } catch (error) {
            console.error('❌ 清除失败:', error);
            return { success: false, error: error.message };
        }
    }
}

// 创建并初始化
const backgroundService = new BackgroundService();

// 扩展安装/更新时初始化
chrome.runtime.onInstalled.addListener(async () => {
    console.log('📦 扩展已安装/更新');
    await backgroundService.init();
});

// Service Worker 启动时初始化
backgroundService.init().catch(error => {
    console.error('❌ Background Service 初始化失败:', error);
});

console.log('✅ Background Service 脚本加载完成');
