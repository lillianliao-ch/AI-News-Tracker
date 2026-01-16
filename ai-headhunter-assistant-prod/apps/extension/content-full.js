/**
 * AI猎头助手 - 完整版（所有代码合并）
 */

// ========== 配置 ==========
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000',
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
  },
  BATCH: {
    page_size: 16,
    max_total: 500,
    max_load_cycles: 6,
    scroll_step_px: 900,
    scroll_attempts_per_cycle: 3,
    load_wait_ms: 1200,
    inter_batch_pause_ms: 35000,
    inter_batch_jitter_ms: 8000
  },
  EXPORT: {
    auto_batch_export: true,
    flush_screenshots_after_batch: true,
    screenshot_format: 'image/jpeg',
    screenshot_quality: 0.86
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
  
  async processCandidate(candidateInfo, resumeText, jdConfig, resumeBase64 = 'mock_data', resumeScreenshot = null) {
    try {
      const requestBody = {
          candidate_info: candidateInfo,
          resume_file: resumeBase64,
          resume_text: resumeText,
          jd_config: jdConfig
      };
      
      // 添加截图（如果有）
      if (resumeScreenshot) {
        requestBody.resume_screenshot = resumeScreenshot;
      }
      
      const response = await fetch(`${this.baseURL}/api/candidates/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
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
    this.detailProcessedCount = 0;
    this.seenCandidateKeys = new Set();
    this.candidateLookup = new Map();
    this.detailProcessedKeys = new Set();
    this.cardAutoIncrement = 0;
    
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
        
        <input type="number" class="ai-input" id="count-input" value="3" min="1" max="500" placeholder="处理数量">
        
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
    this.detailProcessedCount = 0;
    this.results = [];
    this.stats = { recommend: 0, normal: 0, notRecommend: 0, failed: 0 };
    this.seenCandidateKeys = new Set();
    this.candidateLookup = new Map();
    this.detailProcessedKeys = new Set();
    this.cardAutoIncrement = 0;
    
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-export-csv').disabled = true;
    document.getElementById('btn-export-md').disabled = true;
    
    const requested = parseInt(document.getElementById('count-input').value) || 3;
    const targetTotal = Math.min(Math.max(requested, 1), CONFIG.BATCH.max_total);
    const batchSize = CONFIG.BATCH.page_size;
    
    Utils.log(`开始批量处理 ${targetTotal} 个候选人（每批最多 ${batchSize} 个，自动滚动加载）`, 'success');
    
    this.updateUI('初始化中...');
    await Utils.sleep(1500);
    
    try {
      let batchNumber = 0;
      while (this.processedCount < targetTotal) {
        batchNumber++;
        const remaining = targetTotal - this.processedCount;
        const desiredBatchSize = Math.min(batchSize, remaining);
        Utils.log(`===== 第 ${batchNumber} 批：准备处理 ${desiredBatchSize} 人 =====`, 'success');
        this.updateUI(`准备第 ${batchNumber} 批（目标 ${desiredBatchSize} 人）`);
        
        const batchCandidates = await this.collectNextBatch(desiredBatchSize, targetTotal);
        if (batchCandidates.length === 0) {
          Utils.log('⚠️ 未能获取新的候选人，提前结束批量处理', 'warning');
          break;
        }
        
        this.updateUI(`批次 ${batchNumber}：快速评级中...`);
        await this.processBatch(batchCandidates, targetTotal, batchNumber);
        
        if (this.processedCount >= targetTotal) {
          break;
        }
        
        await this.pauseBetweenBatches(batchNumber);
      }
      
      if (this.stats.recommend === 0) {
        this.updateProgress(100);
      }
      
      if (this.processedCount === 0) {
        throw new Error('未成功处理任何候选人');
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
  
  async collectNextBatch(desiredBatchSize, targetTotal) {
    const collected = [];
    let loadCycles = 0;
    
    while (collected.length < desiredBatchSize) {
      // 抓取当前已加载的候选人（数量设置为目标总量，避免被 Math.min 截断）
      let snapshot = [];
      try {
        snapshot = await this.getCandidates(Math.min(targetTotal, 1000));
      } catch (error) {
        Utils.log(`读取候选人列表失败: ${error.message}`, 'error');
        break;
      }
      
      Utils.log(`当前 DOM 中共有 ${snapshot.length} 个候选人卡片，已收集 ${collected.length}/${desiredBatchSize}`, 'info');
      
      for (const candidate of snapshot) {
        if (!candidate.key) {
          candidate.key = this.getCandidateKey(candidate);
        }
        if (!this.seenCandidateKeys.has(candidate.key)) {
          this.seenCandidateKeys.add(candidate.key);
          this.candidateLookup.set(candidate.key, candidate);
          collected.push(candidate);
          Utils.log(`  新增候选人: ${candidate.name} (key: ${candidate.key.substring(0, 20)}...)`, 'info');
          if (collected.length >= desiredBatchSize) break;
        }
      }
      
      if (collected.length >= desiredBatchSize) {
        Utils.log(`✅ 已收集足够候选人: ${collected.length}/${desiredBatchSize}`, 'success');
        break;
      }
      
      if (loadCycles >= CONFIG.BATCH.max_load_cycles) {
        Utils.log(`已达到最大自动加载次数（${CONFIG.BATCH.max_load_cycles}），停止继续下拉`, 'warning');
        break;
      }
      
      Utils.log(`⏬ 尝试加载更多候选人（第 ${loadCycles + 1} 次滚动）...`, 'info');
      const loaded = await this.loadMoreCandidates();
      loadCycles++;
      if (!loaded) {
        Utils.log('⚠️ 无法加载更多候选人，可能已到底部', 'warning');
        break;
      }
      
      // 加载后额外等待，确保新卡片渲染完成
      Utils.log('等待新卡片渲染...', 'info');
      await Utils.sleep(2000);
    }
    
    Utils.log(`本轮共获取 ${collected.length} 个新候选人（期望 ${desiredBatchSize}）`, collected.length ? 'success' : 'warning');
    return collected;
  }
  
  async processBatch(batchCandidates, targetTotal, batchNumber) {
    const batchResults = [];
    const batchKeys = new Set(batchCandidates.map(c => c.key));
    
    Utils.log(`===== 第 ${batchNumber} 批 · 第一轮快速评级（${batchCandidates.length} 人）=====`, 'success');
    for (let i = 0; i < batchCandidates.length; i++) {
      const candidate = batchCandidates[i];
      this.updateUI(`批次 ${batchNumber} · 快速评级: ${candidate.name} (${i + 1}/${batchCandidates.length})`);
      try {
        const quickResult = await this.processOneQuick(candidate);
        batchResults.push(quickResult);
          this.processedCount++;
        } catch (error) {
          Utils.log(`处理失败: ${error.message}`, 'error');
          this.stats.failed++;
        }
        
      this.updateProgress(Math.min((this.processedCount / targetTotal) * 50, 50));
        
      if (i < batchCandidates.length - 1) {
          await Utils.randomDelay();
        }
      }
      
    const batchRecommended = batchResults.filter(r => r.evaluation.推荐等级 === '推荐' && !this.detailProcessedKeys.has(r.aiCandidateKey));
    if (batchRecommended.length === 0) {
      Utils.log(`第 ${batchNumber} 批无推荐候选人，跳过第二轮`, 'warning');
      return;
    }
    
    Utils.log(`===== 第 ${batchNumber} 批 · 第二轮详细提取（${batchRecommended.length} 人）=====`, 'success');
    for (let i = 0; i < batchRecommended.length; i++) {
      const result = batchRecommended[i];
      const candidate = this.candidateLookup.get(result.aiCandidateKey);
      if (!candidate) {
        Utils.log(`未找到推荐候选人的 DOM 节点，跳过: ${result.candidate_info?.name}`, 'warning');
        continue;
      }
      
      this.updateUI(`批次 ${batchNumber} · 提取简历: ${candidate.name} (${i + 1}/${batchRecommended.length})`);
      
      try {
        const resumeData = await this.extractDetailResume(candidate, true);
          const resumeText = resumeData.text || '';
          const screenshot = resumeData.screenshot || '';
        Utils.log(`✅ ${candidate.name} 简历已提取（文本: ${resumeText.length} 字，截图: ${screenshot ? '有' : '无'}）`, 'success');
          
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
            CONFIG.DEFAULT_JD,
            'mock_data',
            screenshot
            );
            
            if (reParseResult.success) {
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
        
        this.detailProcessedKeys.add(result.aiCandidateKey);
        this.detailProcessedCount++;
        const recommendTotal = Math.max(this.stats.recommend, 1);
        this.updateProgress(50 + Math.min((this.detailProcessedCount / recommendTotal) * 50, 50));
        
        } catch (error) {
          Utils.log(`❌ ${candidate.name} 简历提取失败: ${error.message}`, 'error');
          result.resume_text = `提取失败: ${error.message}`;
        }
        
      if (i < batchRecommended.length - 1) {
        Utils.log(`等待 2 秒后继续下一位推荐候选人...`, 'info');
        await Utils.sleep(2000);
          await Utils.randomDelay();
        }
      }
      
    await this.handleBatchPostProcessing(batchResults, batchNumber);
  }
  
  async handleBatchPostProcessing(batchResults, batchNumber) {
    if (!batchResults || batchResults.length === 0) return;
    if (!CONFIG.EXPORT.auto_batch_export) return;
    
    const suffix = `batch-${String(batchNumber).padStart(2, '0')}`;
    Utils.log(`📁 第 ${batchNumber} 批处理完成，开始自动导出（${suffix}）`, 'info');
    
    this.exportCSV(batchResults, suffix);
    this.exportMarkdown(batchResults, suffix, { flushScreenshots: CONFIG.EXPORT.flush_screenshots_after_batch });
    
    if (CONFIG.EXPORT.flush_screenshots_after_batch) {
      batchResults.forEach(result => {
        if (result.resume_screenshot) {
          result.resume_screenshot = null;
        }
      });
    }
  }
  
  async pauseBetweenBatches(batchNumber) {
    const base = CONFIG.BATCH.inter_batch_pause_ms;
    const jitter = Math.floor(Math.random() * CONFIG.BATCH.inter_batch_jitter_ms);
    const waitMs = base + jitter;
    Utils.log(`第 ${batchNumber} 批结束，为防止风控将休息 ${Math.round(waitMs/1000)} 秒后继续...`, 'warning');
    this.updateUI(`批次 ${batchNumber} 完成，防封休息中...`);
    await Utils.sleep(waitMs);
  }
  
  async loadMoreCandidates() {
    Utils.log('尝试下拉加载更多候选人...', 'info');
    const initialCount = this.countAvailableCards();
    if (initialCount === 0) {
      Utils.log('当前页面未检测到候选人卡片，无法下拉', 'error');
      return false;
    }
    
    Utils.log(`加载前：页面共有 ${initialCount} 个候选人卡片`, 'info');
    
    const scrollTargets = [];
    const iframe = document.querySelector('iframe[name="recommendFrame"]');
    if (iframe) {
      try {
        const iframeWin = iframe.contentWindow;
        if (iframeWin) scrollTargets.push(iframeWin);
      } catch (e) {
        Utils.log('无法访问 iframe 进行滚动', 'warning');
      }
    }
    scrollTargets.push(window);
    
    const containerSelectors = [
      '.recommend-job-list',
      '.geek-list',
      '.geek-item-list',
      '.user-list',
      '.list-wrap',
      '.infinite-container',
      '.job-card-wrapper'
    ];
    
    containerSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(elem => scrollTargets.push(elem));
      if (iframe?.contentDocument) {
        iframe.contentDocument.querySelectorAll(selector).forEach(elem => scrollTargets.push(elem));
      }
    });
    
    Utils.log(`准备滚动 ${scrollTargets.length} 个目标（包括 window/iframe/容器）`, 'info');
    
    for (let cycle = 0; cycle < CONFIG.BATCH.scroll_attempts_per_cycle; cycle++) {
      Utils.log(`  第 ${cycle + 1}/${CONFIG.BATCH.scroll_attempts_per_cycle} 次滚动...`, 'info');
      scrollTargets.forEach(target => {
        try {
          if (target === window) {
            window.scrollBy({ top: CONFIG.BATCH.scroll_step_px, behavior: 'smooth' });
          } else if (target instanceof Window) {
            target.scrollBy(0, CONFIG.BATCH.scroll_step_px);
          } else if (target && typeof target.scrollTop === 'number') {
            target.scrollTop += CONFIG.BATCH.scroll_step_px;
          }
        } catch (e) {
          // ignore scroll errors
        }
      });
      
      await Utils.sleep(CONFIG.BATCH.load_wait_ms);
      const currentCount = this.countAvailableCards();
      Utils.log(`  滚动后：页面共有 ${currentCount} 个候选人卡片`, 'info');
      if (currentCount > initialCount) {
        Utils.log(`✅ 新增 ${currentCount - initialCount} 个候选人卡片（滚动成功）`, 'success');
        return true;
      }
    }
    
    // 兜底：尝试点击"加载更多"或"下一页"按钮
    const fallbackButtons = Array.from(document.querySelectorAll('button, a')).filter(elem => {
      if (elem.offsetParent === null) return false;
      const text = elem.textContent.trim();
      return ['下一页', '加载更多', '查看更多', '继续加载'].some(keyword => text.includes(keyword));
    });
    
    if (fallbackButtons.length > 0) {
      Utils.log(`尝试点击 "${fallbackButtons[0].textContent.trim()}" 以加载更多`, 'info');
      fallbackButtons[0].click();
      await Utils.sleep(CONFIG.BATCH.load_wait_ms * 3);
      const currentCount = this.countAvailableCards();
      Utils.log(`点击按钮后：页面共有 ${currentCount} 个候选人卡片`, 'info');
      if (currentCount > initialCount) {
        Utils.log(`✅ 点击按钮后新增 ${currentCount - initialCount} 个候选人`, 'success');
        return true;
      }
    }
    
    Utils.log('⚠️ 无法再加载更多候选人（滚动和点击均无效）', 'warning');
    return false;
  }
  
  countAvailableCards() {
    const selectors = [
      '.card-item',
      '.recommend-job-list .job-card-wrapper',
      '.job-card-wrapper',
      '.geek-item',
      'li.geek-list-item',
      '.user-list li'
    ];
    let maxCount = 0;
    
    const docs = [document];
    const iframe = document.querySelector('iframe[name="recommendFrame"]');
    if (iframe) {
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        if (iframeDoc) docs.unshift(iframeDoc);
      } catch (e) {
        Utils.log('无法访问 iframe，使用主文档统计', 'warning');
      }
    }
    
    for (const doc of docs) {
      for (const selector of selectors) {
        try {
          const nodes = doc.querySelectorAll(selector);
          if (nodes.length > 0) {
            maxCount = Math.max(maxCount, nodes.length);
            break;
          }
        } catch (e) {
          continue;
        }
      }
      if (maxCount > 0) break;
    }
    
    return maxCount;
  }
  
  getCandidateKey(candidate) {
    const card = candidate.element;
    if (card) {
      const keyAttrs = [
        'data-resumeid',
        'data-geekid',
        'data-uid',
        'data-id',
        'data-profileid',
        'data-ai-key'
      ];
      for (const attr of keyAttrs) {
        const value = card.getAttribute(attr);
        if (value) {
          return value;
        }
      }
    }
    
    const fallback = [
      candidate.name || 'unknown',
      candidate.company || 'company',
      candidate.title || 'title',
      this.cardAutoIncrement++
    ].join('|');
    return fallback;
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
        `候选人${i+1}`;
      
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
      
      Utils.log(`提取候选人 ${i+1}: ${name} - ${company} - ${title}`, 'info');
      
      const candidateData = { 
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
      };
      
      candidateData.key = this.getCandidateKey(candidateData);
      card.setAttribute('data-ai-key', candidateData.key);
      
      candidates.push(candidateData);
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

    const enrichedResult = { 
      ...result.data, 
      resume_text: '', 
      resume_screenshot_filename: null,
      aiCandidateKey: candidate.key 
    };
    this.results.push(enrichedResult);

    Utils.log(`✅ ${candidate.name} - ${result.data.evaluation.综合匹配度}% - ${level}`, 'success');
    return enrichedResult;
  }
  
  // 提取详细简历（点击卡片）- 包含收藏和转发
  async extractDetailResume(candidate, shouldFavoriteAndForward = false) {
    let screenshot = null;
    let resumeText = '';
    let favoriteResult = null;
    let forwardResult = null;
    
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
      
      // 5. 如果需要，在弹层打开时执行收藏和转发（此时按钮可见）
      if (shouldFavoriteAndForward) {
        Utils.log(`开始自动收藏和转发 ${candidate.name}...`, 'info');
        
        // 5.1 自动收藏
        favoriteResult = await this.autoFavorite(candidate);
        if (favoriteResult.success) {
          Utils.log(`⭐ ${candidate.name} 收藏${favoriteResult.alreadyCollected ? '(已收藏)' : '成功'}`, 'success');
        } else {
          Utils.log(`⚠️ ${candidate.name} 收藏失败: ${favoriteResult.error}`, 'warning');
        }
        
        await Utils.sleep(1000);
        
        // 5.2 自动转发到邮箱
        forwardResult = await this.autoForward(candidate, 'liao412@gmail.com');
        if (forwardResult.success) {
          Utils.log(`📧 ${candidate.name} 已转发到 liao412@gmail.com`, 'success');
        } else {
          Utils.log(`⚠️ ${candidate.name} 转发失败: ${forwardResult.error}`, 'warning');
        }
      }
      
    } catch (error) {
      Utils.log(`提取简历时出错: ${error.message}`, 'error');
    } finally {
      // 6. 关闭弹层（closeDetail 内部已经有验证和等待）
      await closeDetail();
      // 额外等待1秒，确保所有对话框都关闭
      Utils.log(`额外等待 1 秒，确保所有对话框都关闭...`, 'info');
      await Utils.sleep(1000);
    }
    
    return {
      text: resumeText,
      screenshot: screenshot,
      favoriteResult: favoriteResult,
      forwardResult: forwardResult
    };
  }
  
  // 辅助函数：列出详情弹层中的所有可点击元素
  listClickableElements(detailDialog) {
    if (!detailDialog) return;
    
    // 查找所有可能可点击的元素（包括图标、链接、按钮等）
    const allElements = detailDialog.querySelectorAll('button, a, [onclick], [class*="btn"], [class*="icon"], i, span, div[class*="operate"]');
    Utils.log(`  详情弹层中共有 ${allElements.length} 个可能可点击的元素`, 'info');
    
    // 列出所有元素的详细信息（前50个）
    for (let i = 0; i < Math.min(50, allElements.length); i++) {
      const elem = allElements[i];
      const text = elem.textContent.trim().substring(0, 30);
      const title = elem.getAttribute('title') || '';
      const ariaLabel = elem.getAttribute('aria-label') || '';
      const dataAction = elem.getAttribute('data-action') || '';
      Utils.log(`    [${i+1}] tag="${elem.tagName}" class="${elem.className}" text="${text}" title="${title}" aria="${ariaLabel}" data-action="${dataAction}"`, 'info');
    }
    
    // 特别查找包含"communication"的元素（操作按钮区域）
    const communicationElements = detailDialog.querySelectorAll('[class*="communication"], [class*="operate"], [class*="action"]');
    if (communicationElements.length > 0) {
      Utils.log(`  🔧 找到 ${communicationElements.length} 个可能的操作区域元素:`, 'success');
      communicationElements.forEach((elem, idx) => {
        const children = elem.querySelectorAll('*');
        Utils.log(`    操作区[${idx+1}]: tag="${elem.tagName}" class="${elem.className}" 子元素数=${children.length}`, 'info');
        // 列出子元素
        for (let i = 0; i < Math.min(10, children.length); i++) {
          const child = children[i];
          Utils.log(`      子[${i+1}]: tag="${child.tagName}" class="${child.className}" text="${child.textContent.trim().substring(0, 20)}"`, 'info');
        }
      });
    }
    
    // 特别查找包含"收藏"相关的元素
    const collectElements = detailDialog.querySelectorAll('[class*="collect"], [class*="star"], [class*="favor"], [title*="收藏"], [aria-label*="收藏"]');
    if (collectElements.length > 0) {
      Utils.log(`  ⭐ 找到 ${collectElements.length} 个可能的收藏相关元素:`, 'success');
      collectElements.forEach((elem, idx) => {
        Utils.log(`    收藏[${idx+1}]: tag="${elem.tagName}" class="${elem.className}" title="${elem.getAttribute('title')}"`, 'info');
      });
    }
    
    // 特别查找包含"转发"或"分享"相关的元素
    const forwardElements = detailDialog.querySelectorAll('[class*="forward"], [class*="share"], [title*="转发"], [title*="分享"], [aria-label*="转发"]');
    if (forwardElements.length > 0) {
      Utils.log(`  📧 找到 ${forwardElements.length} 个可能的转发相关元素:`, 'success');
      forwardElements.forEach((elem, idx) => {
        Utils.log(`    转发[${idx+1}]: tag="${elem.tagName}" class="${elem.className}" title="${elem.getAttribute('title')}"`, 'info');
      });
    }
  }
  
  // 自动收藏候选人
  async autoFavorite(candidate) {
    try {
      Utils.log(`⭐ 开始收藏: ${candidate.name}`, 'info');
      
      // 等待详情弹层完全加载
      await Utils.sleep(2000);
      
      // 尝试多个可能的收藏按钮选择器
      const selectors = [
        // Boss 直聘实际使用的选择器（从日志中找到）
        'div.like-icon-and-text',
        'div.icon-like',
        'div.like-icon',
        '.like-icon-and-text',
        '.icon-like',
        '.like-icon',
        // 可能的 div/i 标签（类似转发按钮）
        'div.icon-coop-collect',
        'div.btn-coop-collect',
        'div.communication[class*="collect"]',
        'i.icon-collect',
        'i.icon-star',
        'i[class*="collect"]',
        'i[class*="star"]',
        'i[class*="favor"]',
        // 传统按钮选择器
        'button.btn-collect',
        '.collect-btn',
        'button[class*="collect"]',
        'button[class*="favorite"]',
        'button[class*="star"]',
        '.icon-collect',
        'button:has(.icon-collect)',
        '[data-action="collect"]',
        '.geek-detail-dialog button[class*="collect"]',
        '.resume-detail-wrap button[class*="collect"]',
        // 更广泛的查找
        'div[class*="collect"]',
        'span[class*="collect"]',
        'a[class*="collect"]'
      ];
      
      let btn = null;
      let foundSelector = '';
      
      // 先在详情弹层中查找
      const detailDialog = document.querySelector('.resume-detail-wrap, .geek-detail-dialog, .dialog-wrap');
      
      if (detailDialog) {
        Utils.log(`在详情弹层中查找收藏按钮...`, 'info');
        for (const sel of selectors) {
          try {
            btn = detailDialog.querySelector(sel);
            if (btn && btn.offsetParent !== null) {
              foundSelector = sel;
              break;
            }
          } catch (e) {
            continue;
          }
        }
      }
      
      // 如果弹层中没找到，在主页面查找
      if (!btn) {
        Utils.log(`在主页面中查找收藏按钮...`, 'info');
        for (const sel of selectors) {
          try {
            btn = document.querySelector(sel);
            if (btn && btn.offsetParent !== null) {
              foundSelector = sel;
              break;
            }
          } catch (e) {
            continue;
          }
        }
      }
      
      if (btn) {
        Utils.log(`✅ 找到收藏按钮: ${foundSelector}`, 'success');
        
        // 检查是否已收藏
        const isCollected = btn.classList.contains('collected') || 
                           btn.classList.contains('active') ||
                           btn.classList.contains('selected');
        
        if (isCollected) {
          Utils.log(`⭐ ${candidate.name} 已收藏`, 'warning');
          return { success: true, alreadyCollected: true };
        }
        
        btn.click();
        await Utils.sleep(500);
        Utils.log(`✅ ${candidate.name} 收藏成功`, 'success');
        return { success: true };
      } else {
        // 调试信息：列出所有可见的按钮和链接
        const allButtons = document.querySelectorAll('button');
        const allLinks = document.querySelectorAll('a');
        
        Utils.log(`❌ 未找到收藏按钮。页面共有 ${allButtons.length} 个按钮，${allLinks.length} 个链接`, 'error');
        
        // 列出包含"收藏"文本的元素
        let foundCollectText = false;
        for (const btn of allButtons) {
          if (btn.textContent.includes('收藏')) {
            Utils.log(`  找到文本包含"收藏"的按钮: "${btn.textContent.trim()}" class="${btn.className}"`, 'info');
            foundCollectText = true;
          }
        }
        
        for (const link of allLinks) {
          if (link.textContent.includes('收藏')) {
            Utils.log(`  找到文本包含"收藏"的链接: "${link.textContent.trim()}" class="${link.className}"`, 'info');
            foundCollectText = true;
          }
        }
        
        // 如果详情弹层存在，列出弹层中的所有可点击元素
        if (detailDialog) {
          this.listClickableElements(detailDialog);
        }
        
        if (!foundCollectText) {
          Utils.log(`  未找到包含"收藏"文本的元素`, 'warning');
        }
        
        return { success: false, error: '未找到收藏按钮' };
      }
    } catch (error) {
      Utils.log(`❌ 收藏失败: ${error.message}`, 'error');
      return { success: false, error: error.message };
    }
  }
  
  // 自动转发候选人到邮箱
  async autoForward(candidate, email = 'liao412@gmail.com') {
    try {
      Utils.log(`📧 开始转发: ${candidate.name} → ${email}`, 'info');
      await Utils.sleep(1500);
      
      // 统一的备选选择器，供弹层与主页面两处复用，避免未定义错误
      const forwardSelectors = [
        'div.btn-coop-forward',                 // 含文本的按钮容器
        'div.communication.icon-coop-forward',  // 完整通信按钮
        '.btn-coop-forward',
        '.icon-coop-forward',
        '.forward-btn',
        'button.btn-forward',
        'button[class*="forward"]',
        'button[class*="share"]',
        'a[href*="forward"]'
      ];
      
      // 1. 查找"转发牛人"按钮
      let forwardBtn = null;
      let foundSelector = '';
      
      // 先在详情弹层中查找
      const detailDialog = document.querySelector('.resume-detail-wrap, .geek-detail-dialog, .dialog-wrap, .dialog-footer');
      
      if (detailDialog) {
        Utils.log(`在详情弹层中查找转发按钮...`, 'info');
        
        // 方法1：优先查找包含"转发牛人"文本的元素（精确匹配）
        const allElements = detailDialog.querySelectorAll('div, button, a, span');
        for (const elem of allElements) {
          const text = elem.textContent.trim();
          // 精确匹配"转发牛人"，且元素可见，且不是父容器（文本长度不超过10）
          if (text === '转发牛人' && elem.offsetParent !== null && text.length <= 10) {
            forwardBtn = elem;
            foundSelector = `text="转发牛人" tag="${elem.tagName}" class="${elem.className}"`;
            Utils.log(`✅ 通过文本找到转发按钮: ${elem.tagName}.${elem.className}`, 'success');
            break;
          }
        }
        
        // 方法2：如果方法1失败，尝试使用CSS选择器（但优先级降低）
        if (!forwardBtn) {
          const forwardSelectors = [
            'div.btn-coop-forward',  // 包含文本的按钮容器
            'div.communication.icon-coop-forward',  // 完整的通信按钮
            '.btn-coop-forward',
            'button.btn-forward',
            '.forward-btn',
            'button[class*="forward"]',
            'div.icon-coop-forward',  // 内部图标（最后尝试）
            '.icon-coop-forward'
          ];
          
          for (const sel of forwardSelectors) {
            try {
              forwardBtn = detailDialog.querySelector(sel);
              if (forwardBtn && forwardBtn.offsetParent !== null) {
                foundSelector = sel;
                break;
              }
            } catch (e) {
              continue;
            }
          }
        }
      }
      
      // 如果弹层中没找到，在主页面查找
      if (!forwardBtn) {
        Utils.log(`在主页面中查找转发按钮...`, 'info');
        for (const sel of forwardSelectors) {
          try {
            forwardBtn = document.querySelector(sel);
            if (forwardBtn && forwardBtn.offsetParent !== null) {
              foundSelector = sel;
              break;
            }
          } catch (e) {
            continue;
          }
        }
        
        // 尝试通过文本内容查找
        if (!forwardBtn) {
          const buttons = document.querySelectorAll('button');
          for (const btn of buttons) {
            if (btn.textContent.includes('转发') || btn.textContent.includes('分享')) {
              forwardBtn = btn;
              foundSelector = '通过文本"转发"找到';
              break;
            }
          }
        }
      }
      
      if (!forwardBtn) {
        // 调试信息：列出所有可见的按钮和链接
        const allButtons = document.querySelectorAll('button');
        const allLinks = document.querySelectorAll('a');
        
        Utils.log(`❌ 未找到转发按钮。页面共有 ${allButtons.length} 个按钮，${allLinks.length} 个链接`, 'error');
        
        // 列出包含"转发"或"分享"文本的按钮
        let foundForwardText = false;
        for (const btn of allButtons) {
          if (btn.textContent.includes('转发') || btn.textContent.includes('分享')) {
            Utils.log(`  找到文本包含"转发/分享"的按钮: "${btn.textContent.trim()}" class="${btn.className}"`, 'info');
            foundForwardText = true;
          }
        }
        
        // 列出包含"转发"或"分享"文本的链接
        for (const link of allLinks) {
          if (link.textContent.includes('转发') || link.textContent.includes('分享')) {
            Utils.log(`  找到文本包含"转发/分享"的链接: "${link.textContent.trim()}" class="${link.className}" href="${link.href}"`, 'info');
            foundForwardText = true;
          }
        }
        
        // 如果详情弹层存在，列出弹层中的所有可点击元素
        if (detailDialog) {
          this.listClickableElements(detailDialog);
        }
        
        if (!foundForwardText) {
          Utils.log(`  未找到包含"转发"或"分享"文本的元素`, 'warning');
        }
        
        return { success: false, error: '未找到转发按钮' };
      }
      
      Utils.log(`✅ 找到转发按钮: ${foundSelector}`, 'success');
      
      // 2. 点击转发按钮
      forwardBtn.click();
      Utils.log(`已点击转发按钮，等待转发选项对话框打开...`, 'info');
      
      // 3. 等待并查找"邮件转发"选项（循环等待，最多10秒）
      let emailOption = null;
      const maxWaitTime = 10000;  // 最多等待10秒
      const checkInterval = 500;  // 每500ms检查一次
      let waitedTime = 0;
      
      while (waitedTime < maxWaitTime && !emailOption) {
        await Utils.sleep(checkInterval);
        waitedTime += checkInterval;
        
        // 查找所有包含"邮件"或"转发"文本的元素
        const allElements = document.querySelectorAll('div, button, a, span');
        
        for (const elem of allElements) {
          const text = elem.textContent.trim();
          // 只匹配"邮件转发"（严格匹配，避免误选"转发至其他"）
          if (text === '邮件转发' && elem.offsetParent !== null) {
            emailOption = elem;
            Utils.log(`✅ 找到邮件转发选项（等待${waitedTime}ms）: tag="${elem.tagName}" class="${elem.className}"`, 'success');
            break;
          }
        }
        
        if (emailOption) {
          break;
        }
        
        // 每2秒输出一次等待日志
        if (waitedTime % 2000 === 0) {
          Utils.log(`  仍在等待邮件转发选项出现... (${waitedTime/1000}秒)`, 'info');
        }
      }
      
      if (emailOption) {
        Utils.log(`点击邮件转发选项...`, 'info');
        emailOption.click();
        await Utils.sleep(2000);  // 等待邮箱输入对话框出现
      } else {
        Utils.log(`⚠️ 未找到"邮件转发"选项（等待了${waitedTime}ms），跳过邮件转发`, 'warning');
        return { success: false, error: '未找到邮件转发选项，已跳过' };
      }
      
      // 4. 查找邮箱输入对话框
      Utils.log(`查找邮箱输入对话框...`, 'info');
      await Utils.sleep(500);  // 额外等待
      
      // 查找最新的对话框（邮箱输入对话框）
      const allDialogs = document.querySelectorAll('[class*="dialog"], [role="dialog"]');
      let emailDialog = null;
      
      // 找到最后一个可见的对话框
      for (let i = allDialogs.length - 1; i >= 0; i--) {
        if (allDialogs[i].offsetParent !== null) {
          emailDialog = allDialogs[i];
          Utils.log(`✅ 找到邮箱输入对话框: ${allDialogs[i].className}`, 'success');
          break;
        }
      }
      
      const emailSearchScope = emailDialog || document;
      
      // 5. 填写邮箱地址
      const emailInputSelectors = [
        'input[type="email"]',
        'input[type="text"]',  // 可能是 text 类型
        'input[placeholder*="邮箱"]',
        'input[placeholder*="收件人"]',
        'input[placeholder*="email"]',
        'input[placeholder*="输入"]',
        '.email-input input',
        'input[class*="email"]',
        'input[name*="email"]',
        'textarea[placeholder*="邮箱"]',
        'textarea[placeholder*="收件人"]',
        'input:not([type="hidden"]):not([type="submit"])'  // 任何可见的输入框
      ];
      
      let emailInput = null;
      for (const sel of emailInputSelectors) {
        const inputs = emailSearchScope.querySelectorAll(sel);
        for (const input of inputs) {
          if (input.offsetParent !== null && input.type !== 'hidden' && input.type !== 'submit') {
            emailInput = input;
            Utils.log(`✅ 找到邮箱输入框: ${sel} placeholder="${input.placeholder}"`, 'success');
            break;
          }
        }
        if (emailInput) break;
      }
      
      if (!emailInput) {
        Utils.log(`❌ 未找到邮箱输入框`, 'error');
        
        // 调试：列出邮箱输入对话框中的所有输入框
        const allInputs = emailSearchScope.querySelectorAll('input, textarea');
        Utils.log(`邮箱输入对话框中共有 ${allInputs.length} 个输入框:`, 'info');
        allInputs.forEach((input, idx) => {
          const isVisible = input.offsetParent !== null;
          Utils.log(`  输入框${idx+1}: type="${input.type}" placeholder="${input.placeholder}" visible=${isVisible} class="${input.className}"`, 'info');
        });
        
        // 调试：列出邮箱输入对话框中的所有按钮
        const allButtons = emailSearchScope.querySelectorAll('button');
        Utils.log(`邮箱输入对话框中共有 ${allButtons.length} 个按钮:`, 'info');
        allButtons.forEach((btn, idx) => {
          Utils.log(`  按钮${idx+1}: text="${btn.textContent.trim()}" class="${btn.className}"`, 'info');
        });
        
        return { success: false, error: '未找到邮箱输入框' };
      }
      
      // 填写邮箱
      emailInput.value = '';
      emailInput.focus();
      await Utils.sleep(200);
      emailInput.value = email;
      emailInput.dispatchEvent(new Event('input', { bubbles: true }));
      emailInput.dispatchEvent(new Event('change', { bubbles: true }));
      await Utils.sleep(500);
      
      // 6. 点击发送按钮（在邮箱输入对话框中）
      Utils.log(`查找发送按钮...`, 'info');
      await Utils.sleep(500);  // 额外等待，确保按钮渲染完成
      
      // 查找所有可能的可点击元素（button, div, a）
      const allClickableElements = emailSearchScope.querySelectorAll('button, div, a, span');
      let sendBtn = null;
      
      for (const elem of allClickableElements) {
        const text = elem.textContent.trim();
        // 精确匹配"转发"、"发送"或"确定"
        // 重要：确保元素的文本长度不超过10个字符，避免匹配到父容器
        if ((text === '转发' || text === '发送' || text === '确定') && text.length <= 10 && elem.offsetParent !== null) {
          // 检查是否被禁用
          const isDisabled = elem.disabled || elem.classList.contains('disabled') || elem.getAttribute('disabled');
          if (!isDisabled) {
            // 额外检查：确保不是按钮容器（如 class="btns"）
            const className = elem.className.toLowerCase();
            if (!className.includes('btns') || elem.tagName === 'BUTTON') {
              sendBtn = elem;
              Utils.log(`✅ 找到发送按钮: "${text}" tag="${elem.tagName}" class="${elem.className}"`, 'success');
              break;
            } else {
              Utils.log(`  跳过按钮容器: "${text}" class="${elem.className}"`, 'info');
            }
          }
        }
      }
      
      // 备用方案：如果没找到，尝试在按钮容器中查找子元素
      if (!sendBtn) {
        Utils.log(`  尝试在按钮容器中查找子元素...`, 'info');
        const buttonContainers = emailSearchScope.querySelectorAll('.btns, .dialog-footer, .footer-btns');
        for (const container of buttonContainers) {
          const children = container.querySelectorAll('button, div, a, span');
          for (const child of children) {
            const text = child.textContent.trim();
            if ((text === '转发' || text === '发送' || text === '确定') && text.length <= 10 && child.offsetParent !== null) {
              sendBtn = child;
              Utils.log(`✅ 在容器中找到发送按钮: "${text}" tag="${child.tagName}" class="${child.className}"`, 'success');
              break;
            }
          }
          if (sendBtn) break;
        }
      }
      
      if (!sendBtn) {
        Utils.log(`❌ 未找到发送按钮`, 'error');
        
        // 调试：列出所有包含"转发"、"发送"或"确定"的元素
        Utils.log(`调试：列出邮箱输入对话框中包含"转发/发送/确定"的元素:`, 'info');
        for (const elem of allClickableElements) {
          const text = elem.textContent.trim();
          if ((text.includes('转发') || text.includes('发送') || text.includes('确定')) && elem.offsetParent !== null) {
            Utils.log(`  元素: text="${text}" tag="${elem.tagName}" class="${elem.className}"`, 'info');
          }
        }
        
        // 调试：列出按钮容器中的所有子元素
        const buttonContainers = emailSearchScope.querySelectorAll('.btns, .dialog-footer');
        Utils.log(`调试：按钮容器中的子元素:`, 'info');
        buttonContainers.forEach((container, idx) => {
          Utils.log(`  容器${idx+1}: class="${container.className}"`, 'info');
          const children = container.querySelectorAll('*');
          for (let i = 0; i < Math.min(10, children.length); i++) {
            const child = children[i];
            Utils.log(`    子元素${i+1}: text="${child.textContent.trim().substring(0, 20)}" tag="${child.tagName}" class="${child.className}"`, 'info');
          }
        });
        
        return { success: false, error: '未找到发送按钮' };
      }
      
      sendBtn.click();
      Utils.log(`已点击发送按钮，等待邮件发送...`, 'info');
      await Utils.sleep(2000);  // 等待邮件发送
      
      // 关闭邮件发送对话框
      Utils.log(`关闭邮件发送对话框...`, 'info');
      await this.closeForwardDialog();
      
      Utils.log(`✅ ${candidate.name} 已转发到 ${email}`, 'success');
      return { success: true };
      
    } catch (error) {
      Utils.log(`❌ 转发失败: ${error.message}`, 'error');
      // 即使失败，也尝试关闭对话框
      try {
        await this.closeForwardDialog();
      } catch (e) {
        // 忽略关闭对话框的错误
      }
      return { success: false, error: error.message };
    }
  }
  
  // 关闭邮件发送对话框
  async closeForwardDialog() {
    Utils.log('关闭邮件发送对话框...', 'info');
    
    // 尝试多种关闭方式
    const closeSelectors = [
      '.boss-dialog .close',
      '.boss-dialog .icon-close',
      '.boss-dialog__close',
      '.el-dialog__close',
      '.dialog-close',
      '[aria-label="关闭"]',
      '.close-btn'
    ];
    
    // 查找并点击关闭按钮
    for (const selector of closeSelectors) {
      const closeBtn = document.querySelector(selector);
      if (closeBtn && closeBtn.offsetParent !== null) {
        Utils.log(`点击邮件对话框关闭按钮: ${selector}`, 'info');
        closeBtn.click();
        break;
      }
    }
    
    // 其次，尝试点击“取消”或“关闭”类按钮
    if (document.querySelector('.boss-dialog, .el-dialog')) {
      const altButtons = Array.from(document.querySelectorAll('.boss-dialog button, .el-dialog button, .boss-dialog .btn, .el-dialog .btn'));
      const candidate = altButtons.find(b => {
        const t = (b.textContent || '').trim();
        return ['取消', '关闭', '返回'].includes(t);
      });
      if (candidate && candidate.offsetParent !== null) {
        Utils.log(`点击邮件对话框辅助按钮: "${candidate.textContent.trim()}"`, 'info');
        candidate.click();
      }
    }
    
    // 等待并验证对话框是否关闭
    const maxWaitTime = 3000;  // 最多等待3秒
    const checkInterval = 200;
    let waitedTime = 0;
    
    while (waitedTime < maxWaitTime) {
      await Utils.sleep(checkInterval);
      waitedTime += checkInterval;
      
      // 检查邮件对话框是否还存在
      const forwardDialog = document.querySelector('.boss-dialog, .el-dialog, [class*="forward"][class*="dialog"]');
      if (!forwardDialog || forwardDialog.offsetParent === null) {
        Utils.log(`✅ 邮件对话框已关闭（等待了 ${waitedTime}ms）`, 'success');
        await Utils.sleep(300);  // 额外等待
        return;
      }
    }
    
    // 最后兜底：不再派发键盘事件（会触发 Untrusted event），仅记录告警
    Utils.log('⚠️ 邮件对话框可能仍未关闭，已跳过键盘事件以避免 CSP/Untrusted 限制', 'warning');
  }
  
  updateProgress(percent) {
    document.getElementById('progress').style.width = percent + '%';
  }
  
  updateUI(message) {
    const stats = `${message} | 推荐:${this.stats.recommend} 一般:${this.stats.normal} 不推荐:${this.stats.notRecommend} 失败:${this.stats.failed}`;
    document.getElementById('stats').textContent = stats;
  }
  
  exportCSV(resultsSubset = this.results, fileSuffix = '') {
    const data = Array.isArray(resultsSubset) ? resultsSubset : this.results;
    if (!data || data.length === 0) {
      if (resultsSubset === this.results) {
      alert('没有可导出的数据');
      } else {
        Utils.log('当前批次没有可导出的数据', 'warning');
      }
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
    const rows = data.map(r => {
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
    const suffix = fileSuffix ? `-${fileSuffix}` : '';
    link.download = `AI猎头助手-${new Date().toISOString().slice(0,10)}${suffix}.csv`;
    link.click();
    
    Utils.log(`CSV 已导出${fileSuffix ? `（${fileSuffix}）` : ''}`, 'success');
  }
  
  exportMarkdown(resultsSubset = this.results, fileSuffix = '', options = {}) {
    const { flushScreenshots = false } = options;
    const data = Array.isArray(resultsSubset) ? resultsSubset : this.results;
    if (!data || data.length === 0) {
      if (resultsSubset === this.results) {
      alert('没有可导出的数据');
      } else {
        Utils.log('当前批次没有可导出的 Markdown 数据', 'warning');
      }
      return;
    }
    
    const joinList = (list, fallback = '无') => (Array.isArray(list) && list.length ? list.join('、') : fallback);
    const bulletList = (list, fallback = '- 无') => (Array.isArray(list) && list.length ? list.map(item => `- ${item}`).join('\n') : fallback);
    
    const today = new Date().toISOString().slice(0, 10);
    const timestamp = new Date().getTime();
    const sections = [`# AI猎头助手候选人解析 ${today}`];
    
    // 用于存储需要单独导出的图片
    const screenshots = [];
    
    data.forEach((r, idx) => {
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
      const screenshotFilename = r.resume_screenshot_filename || `${info.name || `候选人${idx + 1}`}_简历_${timestamp}.png`;
      if (screenshot) {
        sections.push('');
        sections.push('### 简历截图');
        sections.push(`![${info.name}的简历](${screenshotFilename})`);
        sections.push('');
        sections.push('> 💡 提示：截图已单独保存为文件');
        
        screenshots.push({
          filename: screenshotFilename,
          dataUrl: screenshot,
          name: info.name || `候选人${idx + 1}`,
          resultRef: r
        });
      } else if (r.resume_screenshot_filename) {
        sections.push('');
        sections.push('### 简历截图');
        sections.push(`![${info.name}的简历](${r.resume_screenshot_filename})`);
        sections.push('');
        sections.push('> ✅ 此截图已在批次导出阶段保存');
      } else {
        sections.push('');
        sections.push('### 简历截图');
        sections.push('（本候选人的截图未保存）');
      }
    });
    
    // 1. 导出 Markdown 文件
    const markdown = sections.join('\n');
    const mdBlob = new Blob([markdown], { type: 'text/markdown;charset=utf-8;' });
    const mdLink = document.createElement('a');
    mdLink.href = URL.createObjectURL(mdBlob);
    const suffix = fileSuffix ? `-${fileSuffix}` : '';
    mdLink.download = `AI猎头助手-${today}${suffix}.md`;
    mdLink.click();
    
    Utils.log(`Markdown 已导出${fileSuffix ? `（${fileSuffix}）` : ''}`, 'success');
    
    // 2. 导出所有截图文件
    if (screenshots.length > 0) {
      Utils.log(`开始导出 ${screenshots.length} 个截图文件${fileSuffix ? `（${fileSuffix}）` : ''}...`, 'info');
      
      screenshots.forEach((item, index) => {
        setTimeout(() => {
          downloadDataUrlFile(item.dataUrl, item.filename, CONFIG.EXPORT.screenshot_format || 'image/png');
          item.resultRef.resume_screenshot_filename = item.filename;
          if (flushScreenshots) {
            item.resultRef.resume_screenshot = null;
          }
          Utils.log(`✅ 已导出截图: ${item.filename}`, 'success');
        }, index * 500); // 每个文件间隔 500ms，避免浏览器阻止多文件下载
      });
      
      Utils.log(`所有截图将在 ${screenshots.length * 0.5} 秒内完成下载`, 'success');
    } else if (flushScreenshots) {
      data.forEach(result => {
        if (result.resume_screenshot) {
          result.resume_screenshot = null;
        }
      });
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
      const format = CONFIG.EXPORT?.screenshot_format || 'image/png';
      const quality = format === 'image/jpeg' ? (CONFIG.EXPORT?.screenshot_quality ?? 0.9) : undefined;
      const dataUrl = quality ? canvas.toDataURL(format, quality) : canvas.toDataURL(format);
      const sizeKB = (dataUrl.length / 1024).toFixed(2);
      Utils.log(`✅ Canvas 截图完成（${format}，${sizeKB} KB）`, 'success');
      
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

function downloadDataUrlFile(dataUrl, filename, mimeOverride) {
  if (!dataUrl) return;
  try {
    const base64Data = dataUrl.split(',')[1];
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const mimeType = mimeOverride || dataUrl.substring(dataUrl.indexOf(':') + 1, dataUrl.indexOf(';')) || 'application/octet-stream';
    const blob = new Blob([byteArray], { type: mimeType });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  } catch (error) {
    Utils.log(`下载文件失败: ${error.message}`, 'error');
  }
}

async function closeDetail() {
  Utils.log('关闭弹层...', 'info');
  
  // 先关闭可能存在的转发对话框
  const shareDialogs = document.querySelectorAll('.c-share-box, [class*="share"]');
  for (const dialog of shareDialogs) {
    if (dialog.offsetParent !== null) {
      const closeBtn = dialog.querySelector('.close, .icon-close, [aria-label="关闭"]');
      if (closeBtn) {
        Utils.log('先关闭转发对话框...', 'info');
        closeBtn.click();
        await Utils.sleep(500);
      }
    }
  }
  
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
      break;  // 找到就退出循环
    }
  }
  
  // 如果没找到，在 iframe 内查找关闭按钮
  const iframe = document.querySelector('iframe[name="recommendFrame"]');
  if (iframe) {
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
      for (const selector of closeSelectors) {
        const closeBtn = iframeDoc.querySelector(selector);
        if (closeBtn) {
          Utils.log(`点击关闭按钮（iframe）: ${selector}`, 'info');
          closeBtn.click();
          break;  // 找到就退出循环
        }
      }
    } catch (e) {
      Utils.log('无法访问 iframe 内容', 'warning');
    }
  }
  
  // 等待并验证浮层是否关闭
  const maxWaitTime = 5000;  // 最多等待5秒
  const checkInterval = 200;  // 每200ms检查一次
  let waitedTime = 0;
  
  while (waitedTime < maxWaitTime) {
    await Utils.sleep(checkInterval);
    waitedTime += checkInterval;
    
    // 检查所有对话框是否都已关闭
    const allDialogs = document.querySelectorAll('.resume-detail-wrap, .geek-detail-dialog, .dialog-wrap, .boss-dialog, .c-share-box');
    const visibleDialogs = Array.from(allDialogs).filter(d => d.offsetParent !== null);
    
    if (visibleDialogs.length === 0) {
      Utils.log(`✅ 所有对话框已关闭（等待了 ${waitedTime}ms）`, 'success');
      await Utils.sleep(500);  // 额外等待500ms，确保完全关闭
      return;
    }
    
    // 每1秒输出一次等待日志
    if (waitedTime % 1000 === 0) {
      Utils.log(`  等待对话框关闭... (${waitedTime/1000}秒，剩余 ${visibleDialogs.length} 个)`, 'info');
    }
  }
  
  // 如果5秒后还没关闭，尝试按 ESC
  Utils.log('⚠️ 对话框未完全关闭，尝试按 ESC 键', 'warning');
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
  await Utils.sleep(1000);
  
  // 最后再检查一次
  const allDialogs = document.querySelectorAll('.resume-detail-wrap, .geek-detail-dialog, .dialog-wrap, .boss-dialog, .c-share-box');
  const visibleDialogs = Array.from(allDialogs).filter(d => d.offsetParent !== null);
  if (visibleDialogs.length > 0) {
    Utils.log(`❌ 仍有 ${visibleDialogs.length} 个对话框未关闭！`, 'error');
  } else {
    Utils.log('✅ 所有对话框已关闭', 'success');
  }
}

// ========== 初始化 ==========
console.log('🤖 AI猎头助手完整版加载中...');

// 防止重复注入：检查是否已经存在控制面板
if (document.getElementById('ai-headhunter-panel')) {
  console.log('⚠️ 控制面板已存在，跳过重复注入');
} else {
  new AIHeadhunterExtension();
}

