/**
 * AI猎头助手 - 完整版（所有代码合并）
 */

// ========== 配置 ==========
const CONFIG = {
  API_BASE_URL: 'http://localhost:18001',
  DEFAULT_JD: {
    position: 'AI产品经理（C端）',
    location: ['北京', '深圳'],
    salary_range: '30-60K',
    work_years: '3-5年',
    education: '本科及以上',
    required_skills: [
      'AI产品经验（2年以上）',
      'C端产品（DAU>100万）',
      '大模型应用（RAG/Agent）'
    ],
    optional_skills: [
      '大厂背景（BAT/字节/美团等）',
      '0-1产品经验',
      'B端+C端复合背景'
    ]
  },
  PROCESSING: {
    delay_min: 2000,
    delay_max: 5000
  }
};

// ========== 工具函数 ==========
const Utils = {
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  async randomDelay() {
    const delay = Math.random() * (CONFIG.PROCESSING.delay_max - CONFIG.PROCESSING.delay_min) + CONFIG.PROCESSING.delay_min;
    await this.sleep(delay);
  },

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[AI猎头助手 ${timestamp}]`;

    const colors = {
      success: 'color: green; font-weight: bold',
      error: 'color: red; font-weight: bold',
      warning: 'color: orange; font-weight: bold',
      info: 'color: blue'
    };

    console.log(`%c${prefix} ${message}`, colors[type] || colors.info);
  }
};

// ========== API 调用 ==========
class API {
  constructor() {
    this.baseURL = CONFIG.API_BASE_URL;
  }

  async testConnection() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processCandidate(candidateInfo, resumeText, jdConfig, resumeBase64 = 'mock_data') {
    try {
      const response = await fetch(`${this.baseURL}/api/candidates/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_info: candidateInfo,
          resume_file: resumeBase64,
          resume_text: resumeText,
          jd_config: jdConfig
        })
      });

      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          detail = `${detail}: ${errorData.error || JSON.stringify(errorData)}`;
        } catch (parseErr) {
          const text = await response.text();
          if (text) detail = `${detail}: ${text}`;
        }
        throw new Error(detail);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

// ========== 主应用 ==========
class AIHeadhunterExtension {
  constructor() {
    this.api = new API();
    this.isRunning = false;
    this.processedCount = 0;
    this.results = [];
    this.stats = { recommend: 0, normal: 0, notRecommend: 0, failed: 0 };

    this.init();
  }

  async init() {
    Utils.log('插件初始化中...');

    const result = await this.api.testConnection();
    if (result.success) {
      Utils.log('后台服务连接成功', 'success');
      this.createUI(true);
    } else {
      Utils.log(`后台服务连接失败: ${result.error}`, 'error');
      this.createUI(false);
    }
  }

  createUI(connected) {
    if (document.getElementById('ai-panel')) return;

    const panel = document.createElement('div');
    panel.id = 'ai-panel';
    panel.innerHTML = `
      <style>
        #ai-panel {
          position: fixed;
          bottom: 10px;
          left: 10px;
          width: 160px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.15);
          z-index: 999999;
          font-family: -apple-system, sans-serif;
          font-size: 11px;
        }
        .ai-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 6px 10px;
          border-radius: 8px 8px 0 0;
          font-weight: 600;
          font-size: 12px;
        }
        .ai-body {
          padding: 10px;
        }
        .ai-status {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 10px;
        }
        .ai-connected { color: #10b981; }
        .ai-disconnected { color: #ef4444; }
        .ai-input {
          width: 100%;
          padding: 4px 6px;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin-bottom: 8px;
          font-size: 11px;
        }
        .ai-btn {
          width: 100%;
          padding: 6px;
          border: none;
          border-radius: 4px;
          font-weight: 500;
          cursor: pointer;
          margin-bottom: 4px;
          font-size: 11px;
        }
        .ai-btn-primary {
          background: #667eea;
          color: white;
        }
        .ai-btn-primary:hover { background: #5568d3; }
        .ai-btn-primary:disabled { opacity: 0.5; }
        .ai-progress {
          height: 4px;
          background: #e5e7eb;
          border-radius: 2px;
          overflow: hidden;
          margin: 8px 0;
        }
        .ai-progress-bar {
          height: 100%;
          background: #667eea;
          width: 0%;
          transition: width 0.3s;
        }
        .ai-stats {
          font-size: 10px;
          color: #666;
          text-align: center;
          margin: 6px 0;
        }
        .ai-export {
          background: #10b981;
          color: white;
        }
        .ai-export:hover { background: #059669; }
      </style>
      
      <div class="ai-header">🤖 AI猎头助手</div>
      <div class="ai-body">
        <div class="ai-status">
          <span>后台服务:</span>
          <span class="${connected ? 'ai-connected' : 'ai-disconnected'}">
            ${connected ? '●已连接' : '●未连接'}
          </span>
        </div>
        
        <input type="number" class="ai-input" id="count-input" value="3" min="1" max="50" placeholder="处理数量">
        
        <button class="ai-btn ai-btn-primary" id="btn-start" ${connected ? '' : 'disabled'}>
          🚀 开始处理
        </button>
        
        <div class="ai-progress">
          <div class="ai-progress-bar" id="progress"></div>
        </div>
        
        <div class="ai-stats" id="stats">等待开始...</div>
        
        <button class="ai-btn ai-export" id="btn-export-csv" disabled>
          📊 导出结果 (CSV)
        </button>
        <button class="ai-btn ai-export" id="btn-export-md" disabled>
          📝 导出原文 (Markdown)
        </button>
      </div>
    `;

    document.body.appendChild(panel);
    this.bindEvents();
  }

  bindEvents() {
    document.getElementById('btn-start').onclick = () => this.start();
    document.getElementById('btn-export-csv').onclick = () => this.exportCSV();
    document.getElementById('btn-export-md').onclick = () => this.exportMarkdown();
  }

  async start() {
    if (this.isRunning) return;

    this.isRunning = true;
    this.processedCount = 0;
    this.results = [];
    this.stats = { recommend: 0, normal: 0, notRecommend: 0, failed: 0 };

    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-export-csv').disabled = true;
    document.getElementById('btn-export-md').disabled = true;

    const count = parseInt(document.getElementById('count-input').value) || 3;

    Utils.log(`开始处理 ${count} 个候选人`, 'success');

    // 等待页面加载完成
    this.updateUI('等待页面加载...');
    await Utils.sleep(2000);

    try {
      const candidates = await this.getCandidates(count);
      Utils.log(`找到 ${candidates.length} 个候选人`);

      // ===== 第一轮：快速评级（不点击卡片）=====
      Utils.log('===== 第一轮：快速评级 =====', 'success');
      for (let i = 0; i < candidates.length; i++) {
        const candidate = candidates[i];
        this.updateUI(`快速评级: ${candidate.name} (${i + 1}/${candidates.length})`);

        try {
          await this.processOneQuick(candidate);
          this.processedCount++;
        } catch (error) {
          Utils.log(`处理失败: ${error.message}`, 'error');
          this.stats.failed++;
        }

        this.updateProgress((i + 1) / candidates.length * 50); // 前50%进度

        if (i < candidates.length - 1) {
          await Utils.randomDelay();
        }
      }

      // ===== 第二轮：只对"推荐"的候选人提取详细简历并重新解析 =====
      const recommendedResults = this.results.filter(r => r.evaluation.推荐等级 === '推荐');
      Utils.log(`===== 第二轮：提取 ${recommendedResults.length} 位推荐候选人的详细简历 =====`, 'success');

      for (let i = 0; i < recommendedResults.length; i++) {
        const result = recommendedResults[i];
        const candidate = candidates.find(c => c.name === result.candidate_info.name);

        if (!candidate) continue;

        this.updateUI(`提取简历: ${candidate.name} (${i + 1}/${recommendedResults.length})`);

        try {
          // 1. 提取简历原文和截图
          const resumeData = await this.extractDetailResume(candidate);
          const resumeText = resumeData.text || '';
          const screenshot = resumeData.screenshot || '';
          Utils.log(`✅ ${candidate.name} 简历已提取（文本: ${resumeText.length} 字符，截图: ${screenshot ? '已保存' : '无'}）`, 'success');

          // 2. 用真实简历文本重新调用后端解析（替换 mock 数据）
          if (resumeText && resumeText.length > 50) {
            Utils.log(`正在用真实简历重新解析 ${candidate.name}...`, 'info');
            const candidateInfo = {
              name: candidate.name,
              source_platform: 'Boss直聘',
              current_company: candidate.company,
              current_position: candidate.title,
              expected_salary: candidate.salary,
              age: candidate.age,
              work_years: candidate.workYears,
              education: candidate.education,
              active_status: candidate.activeStatus,
              employment_status: candidate.employmentStatus,
              recent_location: candidate.location,
              skills: candidate.tags,
              advantage: candidate.advantage,
              schools: candidate.schools,
              previous_companies: candidate.previousCompanies
            };

            const reParseResult = await this.api.processCandidate(
              candidateInfo,
              resumeText,
              CONFIG.DEFAULT_JD
            );

            if (reParseResult.success) {
              // 用真实解析结果替换 mock 数据
              result.structured_resume = reParseResult.data.structured_resume;
              result.evaluation = reParseResult.data.evaluation;
              result.resume_text = resumeText;
              result.resume_screenshot = screenshot;
              Utils.log(`✅ ${candidate.name} 真实简历解析完成`, 'success');
            } else {
              Utils.log(`❌ ${candidate.name} 真实简历解析失败，保留 mock 数据`, 'warning');
              result.resume_text = resumeText;
              result.resume_screenshot = screenshot;
            }
          } else {
            Utils.log(`⚠️ ${candidate.name} 简历文本过短（${resumeText.length} 字符），保留 mock 数据`, 'warning');
            result.resume_text = resumeText;
            result.resume_screenshot = screenshot;
          }
        } catch (error) {
          Utils.log(`❌ ${candidate.name} 简历提取失败: ${error.message}`, 'error');
          result.resume_text = `提取失败: ${error.message}`;
        }

        this.updateProgress(50 + ((i + 1) / recommendedResults.length * 50)); // 后50%进度

        if (i < recommendedResults.length - 1) {
          await Utils.randomDelay();
        }
      }

      Utils.log('任务完成！', 'success');
      this.updateUI('✅ 任务完成！');
      document.getElementById('btn-export-csv').disabled = false;
      document.getElementById('btn-export-md').disabled = false;

    } catch (error) {
      Utils.log(`任务失败: ${error.message}`, 'error');
      this.updateUI(`❌ 错误: ${error.message}`);
    }

    this.isRunning = false;
    document.getElementById('btn-start').disabled = false;
  }

  async getCandidates(count) {
    // Boss直聘使用了 iframe，需要先获取 iframe 内的 document
    let targetDoc = document;

    // 查找 iframe
    const iframe = document.querySelector('iframe[name="recommendFrame"]');
    if (iframe) {
      try {
        targetDoc = iframe.contentDocument || iframe.contentWindow.document;
        Utils.log('检测到 iframe，将在 iframe 内查找候选人', 'success');
      } catch (e) {
        Utils.log('无法访问 iframe 内容，使用主页面', 'warning');
      }
    }

    // 尝试多个可能的选择器
    const selectors = [
      '.card-item',                              // Boss直聘候选人卡片
      '.recommend-job-list .job-card-wrapper',  // 推荐页
      '.job-card-wrapper',                       // 通用
      '.geek-item',                              // 候选人列表
      'li.geek-list-item',                       // 另一种列表
      '.user-list li'                            // 用户列表
    ];

    let cards = [];
    let attempts = 0;
    const maxAttempts = 10;

    // 循环尝试，等待元素加载
    while (cards.length === 0 && attempts < maxAttempts) {
      for (const selector of selectors) {
        cards = targetDoc.querySelectorAll(selector);
        if (cards.length > 0) {
          Utils.log(`使用选择器找到 ${cards.length} 个候选人: ${selector}`, 'success');
          break;
        }
      }

      if (cards.length === 0) {
        Utils.log(`尝试 ${attempts + 1}/${maxAttempts}，等待元素加载...`, 'warning');
        await Utils.sleep(1000);
        attempts++;
      }
    }

    if (cards.length === 0) {
      Utils.log('未找到候选人列表，尝试手动查找...', 'warning');
      // 打印页面结构供调试
      console.log('页面 HTML 结构:', document.body.innerHTML.substring(0, 500));
      throw new Error('未找到候选人列表，请确保在正确的页面');
    }

    const candidates = [];

    const normalize = (text) => (text || '').replace(/\s+/g, ' ').trim();
    const extractJoinTexts = (element) => {
      if (!element) return [];
      const nodes = Array.from(element.childNodes)
        .map(node => normalize(node.textContent || ''))
        .filter(Boolean);
      return nodes;
    };

    for (let i = 0; i < Math.min(count, cards.length); i++) {
      const card = cards[i];
      const nameWrap = card.querySelector('.name-wrap');

      let activeStatus = null;
      if (nameWrap) {
        const activeCandidate = nameWrap.querySelector('[class*="status"], [class*="active"], [class*="online"], [class*="alive"], [class*="recent"]');
        if (activeCandidate) {
          activeStatus = normalize(
            activeCandidate.getAttribute('title') ||
            activeCandidate.getAttribute('alt') ||
            activeCandidate.textContent ||
            ''
          );
        }
      }
      if (!activeStatus) {
        const activeText = nameWrap?.textContent || '';
        const match = activeText.match(/(\d+日内活跃|活跃中|在线)/);
        if (match) {
          activeStatus = match[1];
        }
      }

      // 尝试多种方式提取信息
      const name =
        card.querySelector('.geek-name')?.textContent.trim() ||
        card.querySelector('.name')?.textContent.trim() ||
        card.querySelector('h3')?.textContent.trim() ||
        `候选人${i + 1}`;

      let company = normalize(
        card.querySelector('.company-name')?.textContent ||
        card.textContent.match(/公司[:：]\s*([^\n]+)/)?.[1] ||
        ''
      );

      let title = normalize(
        card.querySelector('.job-title')?.textContent ||
        card.querySelector('.info-desc')?.textContent ||
        card.textContent.match(/职位[:：]\s*([^\n]+)/)?.[1] ||
        ''
      );

      // 从时间轴提取最新工作经历
      const workTimeline = card.querySelector('.timeline-wrap.work-exps .timeline-item .content');
      if (workTimeline) {
        const pieces = extractJoinTexts(workTimeline);
        if (pieces.length >= 2) {
          if (!company || company === '未知公司') company = pieces[0];
          if (!title || title === '未知职位') title = pieces[1];
        } else {
          const text = normalize(workTimeline.textContent);
          const split = text.split(/[·•\u2022\u00b7丨\-]+/).map(item => item.trim()).filter(Boolean);
          if (split.length >= 2) {
            if (!company || company === '未知公司') company = split[0];
            if (!title || title === '未知职位') title = split[1];
          }
        }
      }

      const salary =
        card.querySelector('.salary-wrap')?.textContent.trim() ||
        card.querySelector('.salary')?.textContent.trim() ||
        card.querySelector('.tag-salary')?.textContent.trim() ||
        card.textContent.match(/\d+\s*-\s*\d+K/)?.[0] ||
        '面议';

      const baseInfo = card.querySelector('.base-info');
      let age = null;
      let workYears = null;
      let education = null;
      let employmentStatus = null;
      let schools = [];
      if (baseInfo) {
        const pieces = extractJoinTexts(baseInfo);
        pieces.forEach(text => {
          if (/\d+岁/.test(text)) {
            const match = text.match(/(\d+)\s*岁/);
            if (match) age = parseInt(match[1], 10);
          } else if (/年/.test(text)) {
            if (/(\d+)[\s]*年以上/.test(text)) {
              const match = text.match(/(\d+)[\s]*年以上/);
              if (match) workYears = parseInt(match[1], 10);
            } else if (/(\d+)[\s]*年/.test(text)) {
              const match = text.match(/(\d+)[\s]*年/);
              if (match) workYears = parseInt(match[1], 10);
            }
          } else if (/(本科|大专|硕士|博士|MBA|研究生)/.test(text)) {
            education = text;
          } else if (/到岗|离职|在职|可随时|可即时/.test(text)) {
            employmentStatus = employmentStatus || text;
          }
        });
      }
      const educationTimeline = card.querySelectorAll('.timeline-wrap.edu-exps .timeline-item .content');
      if (educationTimeline && educationTimeline.length > 0) {
        schools = Array.from(educationTimeline)
          .map(item => normalize(item.textContent))
          .filter(Boolean)
          .map(text => text.replace(/\s+/g, ' '))
          .slice(0, 2);
      }

      const workTimelineItems = Array.from(card.querySelectorAll('.timeline-wrap.work-exps .timeline-item .content'));
      let previousCompanies = [];
      if (workTimelineItems.length > 1) {
        previousCompanies = workTimelineItems.slice(1, 3).map(item => {
          const parts = extractJoinTexts(item);
          return parts[0] || normalize(item.textContent);
        }).filter(Boolean);
      }


      const locationWrap = card.querySelector('.row.row-flex .label')?.textContent.includes('最近关注')
        ? card.querySelector('.row.row-flex .content .join-text-wrap')
        : null;
      let location = null;
      if (locationWrap) {
        const parts = extractJoinTexts(locationWrap);
        if (parts.length > 0) {
          location = parts[0];
        }
      }

      const tags = Array.from(card.querySelectorAll('.tags .tag-item'))
        .map(tag => tag.textContent.trim())
        .filter(Boolean)
        .slice(0, 15);

      const advantage = normalize(
        card.querySelector('.geek-desc .content')?.textContent || ''
      );

      company = company || '未知公司';
      title = title || '未知职位';

      Utils.log(`提取候选人 ${i + 1}: ${name} - ${company} - ${title}`, 'info');

      candidates.push({
        name,
        company,
        title,
        salary,
        age,
        workYears,
        education,
        employmentStatus,
        activeStatus,
        location,
        tags,
        advantage,
        schools,
        previousCompanies,
        element: card
      });
    }

    return candidates;
  }

  // 快速评级（不点击卡片）
  async processOneQuick(candidate) {
    const candidateInfo = {
      name: candidate.name,
      source_platform: 'Boss直聘',
      current_company: candidate.company,
      current_position: candidate.title,
      expected_salary: candidate.salary,
      age: candidate.age,
      work_years: candidate.workYears,
      education: candidate.education,
      active_status: candidate.activeStatus,
      employment_status: candidate.employmentStatus,
      recent_location: candidate.location,
      skills: candidate.tags,
      advantage: candidate.advantage,
      schools: candidate.schools,
      previous_companies: candidate.previousCompanies
    };

    // 不传 resumeText，后端会走 mock 评级
    const result = await this.api.processCandidate(
      candidateInfo,
      '', // 空字符串
      CONFIG.DEFAULT_JD
    );

    if (!result.success) {
      throw new Error(result.error);
    }

    const level = result.data.evaluation.推荐等级;
    if (level === '推荐') this.stats.recommend++;
    else if (level === '一般') this.stats.normal++;
    else this.stats.notRecommend++;

    this.results.push({ ...result.data, resume_text: '' });

    Utils.log(`✅ ${candidate.name} - ${result.data.evaluation.综合匹配度}% - ${level}`, 'success');
  }

  // 提取详细简历（点击卡片）
  async extractDetailResume(candidate) {
    let screenshot = null;
    let resumeText = '';

    try {
      // 1. 打开弹层
      await openDetail(candidate.element);
      Utils.log('弹层已打开，等待内容加载...', 'info');

      // 2. 等待更长时间，确保 iframe 和 Canvas 完全加载
      await Utils.sleep(2000);

      // 3. 尝试提取文本
      resumeText = extractResumeText();
      Utils.log(`提取文本: ${resumeText.length} 字符`, 'info');

      // 4. 截取 Canvas 图片
      screenshot = await captureResumeScreenshot();

      if (!screenshot) {
        Utils.log('⚠️ 截图失败，但会继续处理', 'warning');
      }

    } catch (error) {
      Utils.log(`提取简历时出错: ${error.message}`, 'error');
    } finally {
      // 5. 关闭弹层
      await closeDetail();
      await Utils.sleep(500); // 等待弹层关闭
    }

    return {
      text: resumeText,
      screenshot: screenshot
    };
  }

  updateProgress(percent) {
    document.getElementById('progress').style.width = percent + '%';
  }

  updateUI(message) {
    const stats = `${message} | 推荐:${this.stats.recommend} 一般:${this.stats.normal} 不推荐:${this.stats.notRecommend} 失败:${this.stats.failed}`;
    document.getElementById('stats').textContent = stats;
  }

  exportCSV() {
    if (this.results.length === 0) {
      alert('没有可导出的数据');
      return;
    }

    const headers = [
      '姓名',
      '年龄',
      '工作年限',
      '活跃度',
      '学历',
      '到岗状态',
      '当前公司',
      '当前职位',
      '期望薪资',
      '前公司1',
      '前公司2',
      '学校1',
      '学校2',
      '匹配度',
      '推荐等级',
      '核心优势',
      '潜在风险'
    ];
    const rows = this.results.map(r => {
      const info = r.candidate_info;
      const ev = r.evaluation;
      return [
        info.name,
        info.age ?? '',
        info.work_years ?? '',
        info.active_status || '',
        info.education || '',
        info.employment_status || '',
        info.current_company || '',
        info.current_position || '',
        info.expected_salary || '',
        info.previous_companies?.[0] || '',
        info.previous_companies?.[1] || '',
        info.schools?.[0] || '',
        info.schools?.[1] || '',
        ev.综合匹配度,
        ev.推荐等级,
        ev.核心优势.join('; '),
        ev.潜在风险.join('; ')
      ];
    });

    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `AI猎头助手-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();

    Utils.log('CSV已导出', 'success');
  }

  exportMarkdown() {
    if (this.results.length === 0) {
      alert('没有可导出的数据');
      return;
    }

    const joinList = (list, fallback = '无') => (Array.isArray(list) && list.length ? list.join('、') : fallback);
    const bulletList = (list, fallback = '- 无') => (Array.isArray(list) && list.length ? list.map(item => `- ${item}`).join('\n') : fallback);

    const today = new Date().toISOString().slice(0, 10);
    const timestamp = new Date().getTime();
    const sections = [`# AI猎头助手候选人解析 ${today}`];

    // 用于存储需要单独导出的图片
    const screenshots = [];

    this.results.forEach((r, idx) => {
      const info = r.candidate_info || {};
      const ev = r.evaluation || {};
      const resumeText = r.resume_text || '';
      const screenshot = r.resume_screenshot;

      sections.push('');
      sections.push(`## 候选人 ${idx + 1} · ${info.name || '未知'}`);
      sections.push(`- 年龄：${info.age ?? '未知'}｜工作年限：${info.work_years ?? '未知'}`);
      sections.push(`- 当前：${info.current_company || '未知公司'}｜${info.current_position || '未知职位'}`);
      sections.push(`- 学历：${info.education || '未知'}｜活跃度：${info.active_status || '未知'}`);
      sections.push(`- 到岗状态：${info.employment_status || '未知'}｜期望薪资：${info.expected_salary || '未填写'}`);
      sections.push(`- 前公司：${joinList(info.previous_companies, '无')}`);
      sections.push(`- 学校：${joinList(info.schools, '无')}`);
      sections.push('');
      sections.push('### AI 评估摘要');
      sections.push(`- 综合匹配度：${ev.综合匹配度 ?? '-'}（${ev.推荐等级 || '-'}）`);
      sections.push(`- 技能匹配度：${ev.技能匹配度 ?? '-'}`);
      sections.push(`- 经验匹配度：${ev.经验匹配度 ?? '-'}`);
      sections.push(`- 教育背景得分：${ev.教育背景得分 ?? '-'}`);
      sections.push(`- 稳定性得分：${ev.稳定性得分 ?? '-'}`);
      sections.push('');
      sections.push('**核心优势**');
      sections.push(bulletList(ev.核心优势));
      sections.push('');
      sections.push('**潜在风险**');
      sections.push(bulletList(ev.潜在风险));
      sections.push('');
      sections.push('**技能标签**');
      sections.push(bulletList(ev.技能标签));
      sections.push('');
      sections.push('### 简历原文');
      if (resumeText && resumeText.length > 20) {
        sections.push('```text');
        sections.push(resumeText);
        sections.push('```');
      } else {
        sections.push('（Boss 直聘简历已加密，无法提取文本）');
      }

      // 添加截图信息
      if (screenshot) {
        const filename = `${info.name || `候选人${idx + 1}`}_简历_${timestamp}.png`;
        sections.push('');
        sections.push('### 简历截图');
        sections.push(`![${info.name}的简历](${filename})`);
        sections.push('');
        sections.push('> 💡 提示：截图已单独保存为 PNG 文件');

        // 保存截图信息供后续导出
        screenshots.push({
          filename: filename,
          dataUrl: screenshot,
          name: info.name || `候选人${idx + 1}`
        });
      }
    });

    // 1. 导出 Markdown 文件
    const markdown = sections.join('\n');
    const mdBlob = new Blob([markdown], { type: 'text/markdown;charset=utf-8;' });
    const mdLink = document.createElement('a');
    mdLink.href = URL.createObjectURL(mdBlob);
    mdLink.download = `AI猎头助手-${today}.md`;
    mdLink.click();

    Utils.log('Markdown已导出', 'success');

    // 2. 导出所有截图文件
    if (screenshots.length > 0) {
      Utils.log(`开始导出 ${screenshots.length} 个截图文件...`, 'info');

      screenshots.forEach((item, index) => {
        setTimeout(() => {
          // 将 Base64 转换为 Blob
          const base64Data = item.dataUrl.split(',')[1];
          const byteCharacters = atob(base64Data);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: 'image/png' });

          // 下载图片
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = item.filename;
          link.click();

          Utils.log(`✅ 已导出截图: ${item.filename}`, 'success');
        }, index * 500); // 每个文件间隔 500ms，避免浏览器阻止多文件下载
      });

      Utils.log(`所有截图将在 ${screenshots.length * 0.5} 秒内完成下载`, 'success');
    }
  }
}

// ===== 新增：简历弹层交互 =====
async function openDetail(card) {
  Utils.log(`尝试打开候选人详情，卡片元素: ${card.tagName}.${card.className}`, 'info');

  // 滚动到可视区域
  if (card.scrollIntoView) {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    await Utils.sleep(300);
  }

  // 检查卡片是否在 iframe 内
  const iframe = document.querySelector('iframe[name="recommendFrame"]');
  let iframeDoc = null;
  if (iframe) {
    try {
      iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
      Utils.log('检测到 iframe，将在 iframe 和顶层同时查找弹层', 'info');
    } catch (e) {
      Utils.log('无法访问 iframe', 'warning');
    }
  }

  // 尝试多种点击方式
  Utils.log('执行点击...', 'info');

  // 方式1: 直接点击卡片
  card.click();
  await Utils.sleep(500);

  // 方式2: 如果没反应，尝试点击卡片内的链接或按钮
  const clickable = card.querySelector('a, button, .geek-name, .info-border, .name-wrap');
  if (clickable && !document.querySelector('.resume-detail-wrap') && !(iframeDoc && iframeDoc.querySelector('.resume-detail-wrap'))) {
    Utils.log('尝试点击卡片内部元素...', 'info');
    clickable.click();
    await Utils.sleep(500);
  }

  // 方式3: 模拟鼠标事件
  if (!document.querySelector('.resume-detail-wrap') && !(iframeDoc && iframeDoc.querySelector('.resume-detail-wrap'))) {
    Utils.log('尝试模拟鼠标事件...', 'info');
    const mouseEvent = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true
    });
    card.dispatchEvent(mouseEvent);
    await Utils.sleep(500);
  }

  // 等待弹层出现（最多8秒，在顶层和 iframe 内同时查找）
  for (let i = 0; i < 80; i++) {
    // 在顶层查找
    let wrap = document.querySelector('.resume-detail-wrap');
    if (wrap) {
      Utils.log(`✅ 弹层已出现在顶层页面（等待 ${i * 100}ms）`, 'success');
      await Utils.sleep(500);
      return;
    }

    // 在 iframe 内查找
    if (iframeDoc) {
      wrap = iframeDoc.querySelector('.resume-detail-wrap');
      if (wrap) {
        Utils.log(`✅ 弹层已出现在 iframe 内（等待 ${i * 100}ms）`, 'success');
        await Utils.sleep(500);
        return;
      }
    }

    await Utils.sleep(100);
  }

  Utils.log('❌ 弹层未出现，尝试查找其他可能的弹层选择器...', 'warning');
  const alternatives = ['.dialog-wrap', '.modal', '.popup', '.detail-dialog', '[role="dialog"]', '.geek-detail', '.resume-dialog'];

  // 在顶层查找备选
  for (const selector of alternatives) {
    if (document.querySelector(selector)) {
      Utils.log(`找到备选弹层（顶层）: ${selector}`, 'success');
      await Utils.sleep(500);
      return;
    }
  }

  // 在 iframe 内查找备选
  if (iframeDoc) {
    for (const selector of alternatives) {
      if (iframeDoc.querySelector(selector)) {
        Utils.log(`找到备选弹层（iframe）: ${selector}`, 'success');
        await Utils.sleep(500);
        return;
      }
    }
  }

  // 打印调试信息
  Utils.log('调试信息：顶层页面所有 dialog/modal 类元素:', 'warning');
  const allDialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="popup"], [class*="detail"]');
  console.log('顶层 dialogs:', allDialogs);

  if (iframeDoc) {
    const iframeDialogs = iframeDoc.querySelectorAll('[class*="dialog"], [class*="modal"], [class*="popup"], [class*="detail"]');
    console.log('iframe dialogs:', iframeDialogs);
  }

  throw new Error('简历弹层未出现，请确认页面结构');
}

function extractResumeText() {
  Utils.log('开始提取简历文本...', 'info');

  // 尝试多个可能的选择器
  const selectors = [
    '.resume-detail-wrap',
    '.dialog-wrap',
    '.modal',
    '.popup',
    '.detail-dialog',
    '[role="dialog"]',
    '.geek-detail',
    '.resume-dialog'
  ];

  // 先在顶层查找
  let wrap = null;
  for (const selector of selectors) {
    wrap = document.querySelector(selector);
    if (wrap) {
      Utils.log(`使用选择器提取文本（顶层）: ${selector}`, 'info');
      break;
    }
  }

  // 如果顶层没找到，在 iframe 内查找
  if (!wrap) {
    const iframe = document.querySelector('iframe[name="recommendFrame"]');
    if (iframe) {
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        for (const selector of selectors) {
          wrap = iframeDoc.querySelector(selector);
          if (wrap) {
            Utils.log(`使用选择器提取文本（iframe）: ${selector}`, 'info');
            break;
          }
        }
      } catch (e) {
        Utils.log('无法访问 iframe 内容', 'warning');
      }
    }
  }

  if (!wrap) {
    Utils.log('❌ 未找到弹层元素', 'error');
    return '';
  }

  const text = wrap.innerText || wrap.textContent || '';
  const lines = text
    .split('\n')
    .map(line => line.replace(/\s+/g, ' ').trim())
    .filter(Boolean);

  const result = lines.join('\n');
  Utils.log(`✅ 提取文本完成，长度: ${result.length} 字符`, 'success');

  return result;
}

// 截取简历 Canvas 图片
async function captureResumeScreenshot() {
  Utils.log('开始截取简历截图...', 'info');

  try {
    // 等待一下，确保 Canvas 渲染完成
    await Utils.sleep(500);

    // 1. 查找弹层
    const wrap = document.querySelector('.resume-detail-wrap');
    if (!wrap) {
      Utils.log('❌ 未找到弹层，无法截图', 'error');
      return null;
    }
    Utils.log('✅ 找到弹层', 'info');

    // 2. 查找 iframe
    const iframe = wrap.querySelector('iframe');
    if (!iframe) {
      Utils.log('❌ 弹层内未找到 iframe', 'error');
      return null;
    }
    Utils.log(`✅ 找到 iframe: ${iframe.src}`, 'info');

    // 3. 访问 iframe 内容
    let iframeDoc;
    try {
      iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
      if (!iframeDoc) {
        throw new Error('iframe document is null');
      }
      Utils.log('✅ 成功访问 iframe 内容', 'info');
    } catch (e) {
      Utils.log(`❌ 无法访问 iframe: ${e.message}`, 'error');
      return null;
    }

    // 4. 查找 Canvas
    const canvas = iframeDoc.querySelector('canvas#wasm_canvas, canvas');
    if (!canvas) {
      Utils.log('❌ iframe 内未找到 Canvas 元素', 'error');
      // 打印 iframe 内的所有元素供调试
      const allElements = iframeDoc.querySelectorAll('*');
      Utils.log(`iframe 内共有 ${allElements.length} 个元素`, 'info');
      const canvasLike = iframeDoc.querySelectorAll('[id*="canvas"], [class*="canvas"], canvas');
      Utils.log(`找到 ${canvasLike.length} 个可能的 Canvas 元素`, 'info');
      return null;
    }

    Utils.log(`✅ 找到 Canvas: ${canvas.width}x${canvas.height}`, 'success');

    // 5. 从 Canvas 导出图片
    try {
      const dataUrl = canvas.toDataURL('image/png');
      const sizeKB = (dataUrl.length / 1024).toFixed(2);
      Utils.log(`✅ Canvas 截图完成，大小: ${sizeKB} KB`, 'success');

      // 如果图片太小（可能是空白），警告
      if (dataUrl.length < 1000) {
        Utils.log('⚠️ 截图文件过小，可能是空白图片', 'warning');
      }

      return dataUrl;
    } catch (e) {
      Utils.log(`❌ Canvas 导出失败（被污染）: ${e.message}`, 'error');

      // Canvas 被污染，使用 Chrome 截屏 API
      Utils.log('尝试使用 Chrome 截屏 API...', 'info');
      try {
        // 截图前隐藏控制面板
        const panel = document.getElementById('ai-headhunter-panel');
        const panelWasVisible = panel && panel.style.display !== 'none';
        if (panel) {
          panel.style.display = 'none';
          Utils.log('📸 截图前已隐藏控制面板', 'info');
        }

        // 等待一下让页面渲染
        await Utils.sleep(200);

        const screenshot = await captureVisibleTab();

        // 截图后恢复控制面板
        if (panel && panelWasVisible) {
          panel.style.display = 'block';
          Utils.log('✅ 截图后已恢复控制面板', 'info');
        }

        if (screenshot) {
          Utils.log(`✅ 使用截屏 API 成功`, 'success');
          return screenshot;
        }
      } catch (e3) {
        Utils.log(`❌ 截屏 API 也失败: ${e3.message}`, 'error');

        // 确保恢复控制面板
        const panel = document.getElementById('ai-headhunter-panel');
        if (panel) {
          panel.style.display = 'block';
        }
      }

      return null;
    }

  } catch (error) {
    Utils.log(`❌ 截图过程出错: ${error.message}`, 'error');
    console.error('截图详细错误:', error);
    return null;
  }
}

// 使用 Chrome 截屏 API（通过 background script）
async function captureVisibleTab() {
  return new Promise((resolve, reject) => {
    try {
      // 向 background script 发送截屏请求
      chrome.runtime.sendMessage(
        { action: 'captureScreenshot' },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (response && response.success) {
            resolve(response.dataUrl);
          } else {
            reject(new Error(response?.error || '截屏失败'));
          }
        }
      );
    } catch (error) {
      reject(error);
    }
  });
}

// 辅助函数：截取 DOM 元素为图片
async function captureElement(element) {
  try {
    // 使用 html2canvas 库（如果可用）
    if (typeof html2canvas !== 'undefined') {
      const canvas = await html2canvas(element, {
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff'
      });
      return canvas.toDataURL('image/png');
    }

    // 兜底：返回提示信息
    Utils.log('html2canvas 不可用，无法截取 DOM 元素', 'warning');
    return null;
  } catch (error) {
    Utils.log(`DOM 元素截图失败: ${error.message}`, 'error');
    return null;
  }
}

async function closeDetail() {
  Utils.log('关闭弹层...', 'info');

  // 尝试多种关闭方式
  const closeSelectors = [
    '.resume-detail-wrap .btn-close',
    '.resume-detail-wrap .icon-close',
    '.dialog-wrap .close',
    '.modal .close',
    '[aria-label="关闭"]',
    '.close-btn',
    '.icon-close'
  ];

  // 先在顶层查找关闭按钮
  for (const selector of closeSelectors) {
    const closeBtn = document.querySelector(selector);
    if (closeBtn) {
      Utils.log(`点击关闭按钮（顶层）: ${selector}`, 'info');
      closeBtn.click();
      await Utils.sleep(300);
      return;
    }
  }

  // 在 iframe 内查找关闭按钮
  const iframe = document.querySelector('iframe[name="recommendFrame"]');
  if (iframe) {
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
      for (const selector of closeSelectors) {
        const closeBtn = iframeDoc.querySelector(selector);
        if (closeBtn) {
          Utils.log(`点击关闭按钮（iframe）: ${selector}`, 'info');
          closeBtn.click();
          await Utils.sleep(300);
          return;
        }
      }
    } catch (e) {
      Utils.log('无法访问 iframe 内容', 'warning');
    }
  }

  // 兜底：按 ESC
  Utils.log('尝试按 ESC 键关闭', 'info');
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
  await Utils.sleep(300);
}

// ========== 初始化 ==========
console.log('🤖 AI猎头助手完整版加载中...');

// 防止重复注入：检查是否已经存在控制面板
if (document.getElementById('ai-headhunter-panel')) {
  console.log('⚠️ 控制面板已存在，跳过重复注入');
} else {
  new AIHeadhunterExtension();
}

