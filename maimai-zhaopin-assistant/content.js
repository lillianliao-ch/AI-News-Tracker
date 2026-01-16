// 脉脉招聘助手 - MVP 版本
// 基于"立即沟通"按钮锚点的 DOM 解析策略

(function () {
    'use strict';

    console.log('脉脉招聘助手: MVP 版本加载中...');

    // 防止重复注入
    if (window.maimaiAssistantLoaded) {
        console.log('脉脉招聘助手: 已加载，跳过');
        return;
    }
    window.maimaiAssistantLoaded = true;

    // ==================== 数据存储 ====================
    let extractedData = [];

    // ==================== DOM 解析核心 ====================

    /**
     * 查找所有"立即沟通"按钮作为锚点
     */
    function findChatButtons() {
        return [...document.querySelectorAll('button, a, div, span')]
            .filter(el => el.textContent && el.textContent.trim() === '立即沟通');
    }

    /**
     * 从按钮向上查找卡片根节点
     */
    function findCardRoot(el) {
        let cur = el;
        for (let i = 0; i < 12 && cur; i++) {
            const t = (cur.textContent || '').replace(/\s+/g, ' ').trim();
            // 条件：包含"立即沟通" + 包含学历/年限关键词 + 文本够长
            if (t.includes('立即沟通') &&
                (t.includes('年') || t.includes('硕士') || t.includes('博士') || t.includes('本科'))) {
                if (t.length > 80) return cur;
            }
            cur = cur.parentElement;
        }
        return null;
    }

    /**
     * 获取所有候选人卡片（去重）
     */
    function getAllCards() {
        const chatBtns = findChatButtons();
        const cards = chatBtns.map(findCardRoot).filter(Boolean);
        return Array.from(new Set(cards));
    }

    // ==================== 字段提取 ====================

    function pickFirst(re, text) {
        const m = text.match(re);
        return m ? m[1].trim() : '';
    }

    /**
     * 解析单个卡片
     */
    function parseCard(card) {
        const text = (card.innerText || '')
            .replace(/\u00A0/g, ' ')
            .replace(/\s+\n/g, '\n')
            .trim();

        // 1) 姓名：第一行文本
        const lines = text.split('\n').map(s => s.trim()).filter(Boolean);
        const name = lines[0] || '';

        // 2) 活跃度
        const active = pickFirst(/(刚刚活跃|今日活跃|近1周活跃|近1月活跃)/, text);

        // 3) 工作年限和年龄
        const years = pickFirst(/(\d+年)/, text);
        const age = pickFirst(/(\d+岁)/, text);

        // 4) 学历
        const degree = pickFirst(/(博士|硕士|本科)/, text);

        // 5) 城市
        const city = pickFirst(/(北京[^\s\n]*|上海[^\s\n]*|深圳[^\s\n]*|杭州[^\s\n]*|广州[^\s\n]*|成都[^\s\n]*|武汉[^\s\n]*|南京[^\s\n]*|西安[^\s\n]*|重庆[^\s\n]*|天津[^\s\n]*|苏州[^\s\n]*|海外[^\s\n]*|浙江[^\s\n]*|广东[^\s\n]*|四川[^\s\n]*)/, text);

        // 6) 当前工作
        const currentTime = pickFirst(/(\d{4}\.\d{2}\s*-\s*至今)/, text);
        let company = '';
        let title = '';

        if (currentTime) {
            const idx = text.indexOf(currentTime);
            const after = text.slice(idx + currentTime.length).split('\n').map(s => s.trim()).filter(Boolean);
            company = after[0] || '';

            // 查找包含"·"的行作为职位
            const dotLine = after.find(s => s.includes('·'));
            if (dotLine) {
                title = dotLine.split('·').slice(1).join('·').trim();
            } else {
                // 备选：查找常见职位关键词
                const maybe = after.find(s => /seed|Seed|算法|工程师|研究员|HR|招聘|销售|负责人|专家|经理|总监/.test(s));
                title = maybe || '';
            }
        }

        // 7) 期望
        const expect = pickFirst(/期望：([^\n]+)/, text);

        // 8) 职业标签
        const tagMatch = text.match(/职业标签：\s*([^\n]+)/);
        const tags = tagMatch ? tagMatch[1].trim() : '';

        return {
            name,
            active,
            age,
            years,
            degree,
            city,
            company,
            title,
            currentTime,
            expect,
            tags
        };
    }

    /**
     * 扫描并解析所有卡片
     */
    function scanAllCards() {
        const cards = getAllCards();
        console.log(`脉脉招聘助手: 找到 ${cards.length} 个候选人卡片`);

        extractedData = cards.map(parseCard);
        return extractedData;
    }

    // ==================== CSV 导出 ====================

    function toCSV(rows) {
        if (rows.length === 0) return '';

        const headers = ['姓名', '活跃度', '年龄', '工作年限', '学历', '城市', '公司', '职位', '入职时间', '期望', '职业标签'];
        const keys = ['name', 'active', 'age', 'years', 'degree', 'city', 'company', 'title', 'currentTime', 'expect', 'tags'];

        const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;

        const lines = [
            headers.join(','),
            ...rows.map(r => keys.map(k => esc(r[k])).join(','))
        ];

        return '\uFEFF' + lines.join('\n'); // BOM for Excel 中文支持
    }

    function downloadCSV(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ==================== UI 面板 ====================

    function createPanel() {
        // 删除已存在的面板
        const existing = document.getElementById('maimai-assistant-panel');
        if (existing) existing.remove();

        const panel = document.createElement('div');
        panel.id = 'maimai-assistant-panel';
        panel.innerHTML = `
            <style>
                #maimai-assistant-panel {
                    position: fixed;
                    left: 20px;
                    bottom: 20px;
                    width: 280px;
                    background: #fff;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    font-size: 14px;
                    overflow: hidden;
                }
                #maimai-assistant-panel .header {
                    background: linear-gradient(135deg, #2563eb, #3b82f6);
                    color: white;
                    padding: 12px 16px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                }
                #maimai-assistant-panel .header .toggle {
                    font-size: 12px;
                    opacity: 0.8;
                }
                #maimai-assistant-panel .content {
                    padding: 16px;
                }
                #maimai-assistant-panel .stats {
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 12px;
                    text-align: center;
                }
                #maimai-assistant-panel .stats .count {
                    font-size: 28px;
                    font-weight: 700;
                    color: #2563eb;
                }
                #maimai-assistant-panel .stats .label {
                    color: #64748b;
                    font-size: 12px;
                }
                #maimai-assistant-panel .btn {
                    width: 100%;
                    padding: 10px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    margin-bottom: 8px;
                    transition: all 0.2s;
                }
                #maimai-assistant-panel .btn:hover {
                    transform: translateY(-1px);
                }
                #maimai-assistant-panel .btn-primary {
                    background: linear-gradient(135deg, #2563eb, #3b82f6);
                    color: white;
                }
                #maimai-assistant-panel .btn-primary:hover {
                    box-shadow: 0 4px 12px rgba(37,99,235,0.4);
                }
                #maimai-assistant-panel .btn-success {
                    background: linear-gradient(135deg, #059669, #10b981);
                    color: white;
                }
                #maimai-assistant-panel .btn-success:hover {
                    box-shadow: 0 4px 12px rgba(5,150,105,0.4);
                }
                #maimai-assistant-panel .btn-secondary {
                    background: #f1f5f9;
                    color: #475569;
                }
                #maimai-assistant-panel .btn-secondary:hover {
                    background: #e2e8f0;
                }
                #maimai-assistant-panel .status {
                    text-align: center;
                    color: #64748b;
                    font-size: 12px;
                    padding: 8px 0;
                }
            </style>
            <div class="header">
                <span>🎯 脉脉招聘助手</span>
                <span class="toggle">▼</span>
            </div>
            <div class="content" id="panel-content">
                <div class="stats">
                    <div class="count" id="count-display">0</div>
                    <div class="label">已扫描人才</div>
                </div>
                <button class="btn btn-primary" id="scan-btn">🔍 扫描当前页面</button>
                <button class="btn btn-success" id="export-btn">📥 导出 CSV</button>
                <button class="btn btn-secondary" id="clear-btn">🗑️ 清空数据</button>
                <div class="status" id="status-display">就绪</div>
            </div>
        `;

        document.body.appendChild(panel);
        bindEvents(panel);
        console.log('脉脉招聘助手: 面板已创建');
    }

    function bindEvents(panel) {
        // 折叠/展开
        const header = panel.querySelector('.header');
        const content = panel.querySelector('#panel-content');
        const toggle = panel.querySelector('.toggle');

        header.addEventListener('click', () => {
            const isHidden = content.style.display === 'none';
            content.style.display = isHidden ? 'block' : 'none';
            toggle.textContent = isHidden ? '▼' : '▲';
        });

        // 扫描按钮
        const scanBtn = panel.querySelector('#scan-btn');
        scanBtn.addEventListener('click', () => {
            updateStatus('正在扫描...');
            setTimeout(() => {
                try {
                    const data = scanAllCards();
                    updateCount(data.length);
                    updateStatus(`扫描完成，找到 ${data.length} 人`);

                    // 打印前3条数据到控制台供调试
                    console.log('脉脉招聘助手: 提取数据示例:', data.slice(0, 3));
                } catch (error) {
                    console.error('扫描失败:', error);
                    updateStatus('扫描失败: ' + error.message);
                }
            }, 100);
        });

        // 导出按钮
        const exportBtn = panel.querySelector('#export-btn');
        exportBtn.addEventListener('click', () => {
            if (extractedData.length === 0) {
                updateStatus('没有数据可导出，请先扫描');
                return;
            }

            const csv = toCSV(extractedData);
            const filename = `脉脉人才_${new Date().toISOString().split('T')[0]}.csv`;
            downloadCSV(csv, filename);
            updateStatus(`已导出 ${extractedData.length} 条数据`);
        });

        // 清空按钮
        const clearBtn = panel.querySelector('#clear-btn');
        clearBtn.addEventListener('click', () => {
            extractedData = [];
            updateCount(0);
            updateStatus('数据已清空');
        });
    }

    function updateCount(count) {
        const countEl = document.getElementById('count-display');
        if (countEl) countEl.textContent = count;
    }

    function updateStatus(message) {
        const statusEl = document.getElementById('status-display');
        if (statusEl) statusEl.textContent = message;
    }

    // ==================== 初始化 ====================

    function init() {
        // 检查是否在脉脉招聘页面
        const url = window.location.href;
        if (!url.includes('maimai.cn')) {
            console.log('脉脉招聘助手: 非脉脉页面，不加载');
            return;
        }

        console.log('脉脉招聘助手: 初始化中...');

        // 等待页面加载完成后创建面板
        if (document.readyState === 'complete') {
            setTimeout(createPanel, 500);
        } else {
            window.addEventListener('load', () => setTimeout(createPanel, 500));
        }
    }

    init();

})();