/**
 * Chrome 插件主逻辑 - Boss直聘候选人采集与评估
 */

class AIHeadhunterExtension {
  constructor() {
    this.api = new API();
    this.isRunning = false;
    this.isPaused = false;
    this.processedCount = 0;
    this.successCount = 0;
    this.failedCount = 0;
    this.recommendCount = 0;
    this.normalCount = 0;
    this.notRecommendCount = 0;
    this.results = [];
    
    // JD 配置
    this.jdConfig = CONFIG.DEFAULT_JD;
    
    // 初始化
    this.init();
  }
  
  /**
   * 初始化插件
   */
  async init() {
    Utils.log('插件加载中...');
    
    // 测试后台连接
    const result = await this.api.testConnection();
    if (result.success) {
      Utils.log('后台服务连接成功', 'success');
      this.createControlPanel();
    } else {
      Utils.log(`后台服务连接失败: ${result.error}`, 'error');
      this.createControlPanel(false);
    }
  }
  
  /**
   * 创建控制面板
   */
  createControlPanel(connected = true) {
    // 检查是否已存在
    if (document.getElementById('ai-headhunter-panel')) {
      return;
    }
    
    const panel = document.createElement('div');
    panel.id = 'ai-headhunter-panel';
    panel.className = 'ai-headhunter-panel';
    
    panel.innerHTML = `
      <div class="panel-header">
        <h3>🤖 AI猎头助手</h3>
        <button class="btn-minimize" title="最小化">−</button>
      </div>
      <div class="panel-body">
        <div class="status-row">
          <span class="status-label">后台服务:</span>
          <span class="status-value ${connected ? 'connected' : 'disconnected'}">
            ${connected ? '●已连接' : '●未连接'}
          </span>
        </div>
        
        <div class="config-row">
          <label>处理数量:</label>
          <input type="number" id="process-count" value="10" min="1" max="100">
        </div>
        
        <div class="button-row">
          <button id="btn-start" class="btn-primary" ${connected ? '' : 'disabled'}>
            🚀 开始处理
          </button>
          <button id="btn-pause" class="btn-secondary" disabled>⏸ 暂停</button>
          <button id="btn-stop" class="btn-danger" disabled>⏹ 停止</button>
        </div>
        
        <div class="progress-section">
          <div class="progress-bar-container">
            <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
          </div>
          <div class="progress-text" id="progress-text">0 / 0 (0%)</div>
        </div>
        
        <div class="status-section">
          <div class="status-item">
            <span class="status-emoji">🔄</span>
            <span id="current-status">等待开始...</span>
          </div>
        </div>
        
        <div class="stats-section">
          <div class="stat-item">
            <span class="stat-label">已处理:</span>
            <span class="stat-value" id="stat-processed">0</span>
          </div>
          <div class="stat-item stat-success">
            <span class="stat-label">✅ 推荐:</span>
            <span class="stat-value" id="stat-recommend">0</span>
          </div>
          <div class="stat-item stat-warning">
            <span class="stat-label">⚠️ 一般:</span>
            <span class="stat-value" id="stat-normal">0</span>
          </div>
          <div class="stat-item stat-error">
            <span class="stat-label">❌ 不推荐:</span>
            <span class="stat-value" id="stat-not-recommend">0</span>
          </div>
          <div class="stat-item stat-failed">
            <span class="stat-label">失败:</span>
            <span class="stat-value" id="stat-failed">0</span>
          </div>
        </div>
        
        <div class="export-section">
          <button id="btn-export" class="btn-export" disabled>
            📊 导出结果 (CSV)
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    // 绑定事件
    this.bindEvents();
  }
  
  /**
   * 绑定事件
   */
  bindEvents() {
    // 开始按钮
    document.getElementById('btn-start').addEventListener('click', () => {
      this.start();
    });
    
    // 暂停按钮
    document.getElementById('btn-pause').addEventListener('click', () => {
      this.togglePause();
    });
    
    // 停止按钮
    document.getElementById('btn-stop').addEventListener('click', () => {
      this.stop();
    });
    
    // 导出按钮
    document.getElementById('btn-export').addEventListener('click', () => {
      this.exportResults();
    });
    
    // 最小化按钮
    document.querySelector('.btn-minimize').addEventListener('click', () => {
      const panel = document.getElementById('ai-headhunter-panel');
      panel.classList.toggle('minimized');
    });
  }
  
  /**
   * 开始处理
   */
  async start() {
    if (this.isRunning) {
      Utils.log('已经在运行中', 'warning');
      return;
    }
    
    this.isRunning = true;
    this.isPaused = false;
    this.processedCount = 0;
    this.successCount = 0;
    this.failedCount = 0;
    this.recommendCount = 0;
    this.normalCount = 0;
    this.notRecommendCount = 0;
    this.results = [];
    
    // 更新按钮状态
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-pause').disabled = false;
    document.getElementById('btn-stop').disabled = false;
    document.getElementById('btn-export').disabled = true;
    
    // 获取处理数量
    const count = parseInt(document.getElementById('process-count').value) || 10;
    
    Utils.log(`开始处理 ${count} 个候选人`, 'success');
    this.updateStatus('正在获取候选人列表...');
    
    try {
      // 检查是否在正确的页面
      if (!window.location.href.includes('zhipin.com')) {
        throw new Error('请在 Boss 直聘页面使用');
      }
      
      // 获取候选人列表
      const candidates = await this.getCandidateList(count);
      Utils.log(`找到 ${candidates.length} 个候选人`);
      
      // 逐个处理
      for (let i = 0; i < candidates.length; i++) {
        // 检查是否暂停
        while (this.isPaused && this.isRunning) {
          await Utils.sleep(500);
        }
        
        // 检查是否停止
        if (!this.isRunning) {
          Utils.log('任务已停止', 'warning');
          break;
        }
        
        const candidate = candidates[i];
        this.updateProgress(i + 1, candidates.length);
        this.updateStatus(`正在处理: ${candidate.name}...`);
        
        try {
          const result = await this.processCandidate(candidate);
          this.successCount++;
          
          // 统计推荐等级
          if (result.evaluation.推荐等级 === '推荐') {
            this.recommendCount++;
          } else if (result.evaluation.推荐等级 === '一般') {
            this.normalCount++;
          } else {
            this.notRecommendCount++;
          }
          
          this.results.push(result);
          Utils.log(`✅ ${candidate.name} - 匹配度${result.evaluation.综合匹配度}% - ${result.evaluation.推荐等级}`, 'success');
        } catch (error) {
          this.failedCount++;
          Utils.log(`❌ ${candidate.name} 处理失败: ${error.message}`, 'error');
        }
        
        this.processedCount++;
        this.updateStats();
        
        // 随机延迟
        if (i < candidates.length - 1) {
          await Utils.randomDelay();
        }
      }
      
      // 完成
      this.finish();
      
    } catch (error) {
      Utils.log(`任务失败: ${error.message}`, 'error');
      this.updateStatus(`错误: ${error.message}`);
      this.reset();
    }
  }
  
  /**
   * 获取候选人列表
   */
  async getCandidateList(count) {
    const candidates = [];
    const candidateElements = document.querySelectorAll(CONFIG.SELECTORS.candidate_list);
    
    if (candidateElements.length === 0) {
      throw new Error('未找到候选人列表，请确保在正确的页面');
    }
    
    for (let i = 0; i < Math.min(count, candidateElements.length); i++) {
      const element = candidateElements[i];
      
      const candidate = {
        element,
        name: Utils.extractText(element, CONFIG.SELECTORS.candidate_name) || '未知',
        title: Utils.extractText(element, CONFIG.SELECTORS.candidate_title) || '未知',
        company: Utils.extractText(element, CONFIG.SELECTORS.candidate_company) || '未知',
        salary: Utils.extractText(element, CONFIG.SELECTORS.candidate_salary) || '未知',
        link: Utils.getAttribute(element, CONFIG.SELECTORS.candidate_link, 'href') || ''
      };
      
      candidates.push(candidate);
    }
    
    return candidates;
  }
  
  /**
   * 处理单个候选人
   */
  async processCandidate(candidate) {
    Utils.log(`开始处理候选人: ${candidate.name}`);
    
    // 模拟简历数据（MVP 阶段）
    // TODO: 实际应该打开简历页面并下载 PDF
    const mockResumeBase64 = 'mock_base64_data';
    
    // 构造候选人信息
    const candidateInfo = {
      name: candidate.name,
      source_platform: 'Boss直聘',
      source_url: candidate.link,
      current_company: candidate.company,
      current_position: candidate.title,
      work_years: null,
      expected_salary: candidate.salary,
      education: null,
      active_status: '本周活跃'
    };
    
    // 调用后台 API
    const result = await this.api.processCandidate(
      candidateInfo,
      mockResumeBase64,
      this.jdConfig
    );
    
    if (!result.success) {
      throw new Error(result.error);
    }
    
    return result.data;
  }
  
  /**
   * 暂停/恢复
   */
  togglePause() {
    this.isPaused = !this.isPaused;
    const btn = document.getElementById('btn-pause');
    
    if (this.isPaused) {
      btn.textContent = '▶️ 继续';
      this.updateStatus('已暂停');
      Utils.log('任务已暂停', 'warning');
    } else {
      btn.textContent = '⏸ 暂停';
      this.updateStatus('继续处理...');
      Utils.log('任务继续', 'success');
    }
  }
  
  /**
   * 停止
   */
  stop() {
    this.isRunning = false;
    this.isPaused = false;
    Utils.log('任务已停止', 'warning');
    this.reset();
  }
  
  /**
   * 完成
   */
  finish() {
    this.isRunning = false;
    this.isPaused = false;
    
    Utils.log(`任务完成！成功: ${this.successCount}, 失败: ${this.failedCount}`, 'success');
    this.updateStatus('✅ 任务完成！');
    
    // 启用导出按钮
    document.getElementById('btn-export').disabled = false;
    
    this.reset();
  }
  
  /**
   * 重置按钮状态
   */
  reset() {
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-pause').disabled = true;
    document.getElementById('btn-stop').disabled = true;
    document.getElementById('btn-pause').textContent = '⏸ 暂停';
  }
  
  /**
   * 更新进度
   */
  updateProgress(current, total) {
    const percentage = Math.round((current / total) * 100);
    document.getElementById('progress-bar').style.width = `${percentage}%`;
    document.getElementById('progress-text').textContent = `${current} / ${total} (${percentage}%)`;
  }
  
  /**
   * 更新状态
   */
  updateStatus(message) {
    document.getElementById('current-status').textContent = message;
  }
  
  /**
   * 更新统计
   */
  updateStats() {
    document.getElementById('stat-processed').textContent = this.processedCount;
    document.getElementById('stat-recommend').textContent = this.recommendCount;
    document.getElementById('stat-normal').textContent = this.normalCount;
    document.getElementById('stat-not-recommend').textContent = this.notRecommendCount;
    document.getElementById('stat-failed').textContent = this.failedCount;
  }
  
  /**
   * 导出结果为 CSV
   */
  exportResults() {
    if (this.results.length === 0) {
      Utils.log('没有可导出的结果', 'warning');
      return;
    }
    
    // 生成 CSV
    const headers = ['姓名', '当前公司', '当前职位', '期望薪资', '匹配度', '推荐等级', '核心优势', '潜在风险', '来源链接'];
    const rows = this.results.map(result => {
      const info = result.candidate_info;
      const evaluation = result.evaluation;
      return [
        info.name,
        info.current_company || '',
        info.current_position || '',
        info.expected_salary || '',
        evaluation.综合匹配度,
        evaluation.推荐等级,
        evaluation.核心优势.join('; '),
        evaluation.潜在风险.join('; '),
        info.source_url || ''
      ];
    });
    
    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    // 下载
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `AI猎头助手-候选人评估-${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    
    Utils.log('结果已导出', 'success');
  }
}

// 初始化插件
console.log('🤖 AI猎头助手插件加载中...');
console.log('当前页面:', window.location.href);

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 DOM 加载完成，初始化插件...');
    new AIHeadhunterExtension();
  });
} else {
  console.log('🤖 立即初始化插件...');
  new AIHeadhunterExtension();
}

