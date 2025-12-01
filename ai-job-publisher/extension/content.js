/**
 * Boss 职位自动发布 - Content Script
 */

// ========== 配置 ==========
const CONFIG = {
  DELAYS: {
    field_fill: 500,
    dialog_wait: 1500,
    publish_interval_min: 20000,
    publish_interval_max: 30000
  },
  DEFAULTS: {
    recruitmentType: '社招全职',
    salaryMonths: '12薪',
    headcount: '1',
    departmentFallback: 'AI事业部'
  },
  MAPPINGS: {
    workYears: {
      '不限': '不限',
      '应届生': '1年以内',
      '一年以上': '1-3年',
      '三年以上': '3-5年',
      '五年以上': '5-10年',
      '八年以上': '5-10年',
      '十年以上': '5-10年'
    },
    education: {
      '不限': '不限',
      '初中及以下': '初中及以下',
      '中专/中技': '中专/中技',
      '高中': '高中',
      '大专': '大专',
      '本科': '本科',
      '硕士': '硕士',
      '博士': '博士'
    },
    jobType: {
      '大模型算法': ['互联网/AI', '人工智能', '大模型算法'],
      '图像算法': ['互联网/AI', '人工智能', '图像算法'],
      '自然语言处理算法': ['互联网/AI', '人工智能', '自然语言处理算法'],
      '语音算法': ['互联网/AI', '人工智能', '语音算法'],
      '推荐算法': ['互联网/AI', '人工智能', '推荐算法'],
      '搜索算法': ['互联网/AI', '人工智能', '搜索算法'],
      '算法工程师': ['互联网/AI', '人工智能', '算法工程师'],
      '数据挖掘': ['互联网/AI', '数据', '数据挖掘'],
      '数据开发': ['互联网/AI', '数据', '数据开发'],
      '数据分析师': ['互联网/AI', '数据', '数据分析师'],
      '后端开发': ['互联网/AI', '后端开发'],
      '前端开发': ['互联网/AI', '前端/移动开发', '前端开发工程师'],
      'Android': ['互联网/AI', '前端/移动开发', 'Android'],
      'iOS': ['互联网/AI', '前端/移动开发', 'iOS'],
      '测试工程师': ['互联网/AI', '测试'],
      '运维工程师': ['互联网/AI', '运维/技术支持', '运维工程师'],
      '技术项目管理': ['互联网/AI', '技术项目管理'],
      '产品经理': ['产品', '产品经理'],
      '高端技术职位': ['互联网/AI', '高端技术职位'],
      '其他技术职位': ['互联网/AI', '其他技术职位']
    }
  }
};

const Utils = {
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
  
  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[职位发布 ${timestamp}]`;
    const colors = {
      success: 'color: green; font-weight: bold',
      error: 'color: red; font-weight: bold',
      warning: 'color: orange; font-weight: bold',
      info: 'color: blue'
    };
    console.log(`%c${prefix} ${message}`, colors[type] || colors.info);
  },
  
  async randomDelay() {
    const min = CONFIG.DELAYS.publish_interval_min;
    const max = CONFIG.DELAYS.publish_interval_max;
    const delay = Math.random() * (max - min) + min;
    await this.sleep(delay);
  }
};

// ========== 主应用 ==========
class JobPublisher {
  constructor() {
    this.jobs = [];
    this.currentIndex = 0;
    this.results = [];
    this.isRunning = false;
    this.targetDoc = document; // 默认是主文档
    this.iframe = null;
    
    this.init();
  }
  
  init() {
    Utils.log('Boss 职位发布助手已加载');
    
    // 监听来自 popup 的消息
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'startPublish') {
        this.jobs = request.jobs;
        this.startPublish();
        sendResponse({ success: true });
      }
      return true;
    });
  }
  
  async findTargetDocument() {
    // 查找包含表单的 iframe
    const iframes = document.querySelectorAll('iframe');
    Utils.log(`检测到 ${iframes.length} 个 iframe`, 'info');
    
    for (let i = 0; i < iframes.length; i++) {
      try {
        const iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
        if (iframeDoc) {
          const inputs = iframeDoc.querySelectorAll('input, textarea');
          Utils.log(`  iframe[${i+1}] 有 ${inputs.length} 个表单元素`, 'info');
          
          if (inputs.length > 5) {
            Utils.log(`✅ 使用 iframe[${i+1}] 作为操作目标`, 'success');
            this.targetDoc = iframeDoc;
            this.iframe = iframes[i];
            return;
          }
        }
      } catch (e) {
        Utils.log(`  iframe[${i+1}] 无法访问`, 'warning');
      }
    }
    
    Utils.log('未找到表单 iframe，使用主文档', 'warning');
  }
  
  async startPublish() {
    if (this.isRunning) {
      Utils.log('已有任务在运行中', 'warning');
      return;
    }
    
    this.isRunning = true;
    this.currentIndex = 0;
    this.results = [];
    
    // 先找到目标文档（可能在 iframe 中）
    await this.findTargetDocument();
    
    Utils.log(`开始批量发布 ${this.jobs.length} 个职位`, 'success');
    
    for (let i = 0; i < this.jobs.length; i++) {
      const job = this.jobs[i];
      Utils.log(`\n===== 发布职位 ${i + 1}/${this.jobs.length}: ${job.name} =====`, 'success');
      
      try {
        await this.publishOneJob(job);
        this.results.push({
          index: job.index,
          name: job.name,
          status: 'success',
          error: null
        });
        Utils.log(`✅ ${job.name} 发布成功`, 'success');
      } catch (error) {
        Utils.log(`❌ ${job.name} 发布失败: ${error.message}`, 'error');
        this.results.push({
          index: job.index,
          name: job.name,
          status: 'failed',
          error: error.message
        });
      }
      
      // 发布间隔（最后一个职位不需要等待）
      if (i < this.jobs.length - 1) {
        const waitTime = Math.round((CONFIG.DELAYS.publish_interval_min + CONFIG.DELAYS.publish_interval_max) / 2000);
        Utils.log(`等待 ${waitTime} 秒后发布下一个职位...`, 'info');
        await Utils.randomDelay();
        
        // 刷新页面，准备下一个职位
        Utils.log('刷新页面，准备发布下一个职位...', 'info');
        window.location.reload();
        await Utils.sleep(3000); // 等待页面加载
      }
    }
    
    Utils.log('\n所有职位发布完成！', 'success');
    this.exportReport();
    this.isRunning = false;
  }
  
  async publishOneJob(job) {
    Utils.log(`开始填写职位: ${job.name}`, 'info');
    
    // 等待页面完全加载（增加等待时间，确保动态内容渲染完成）
    Utils.log('等待页面加载完成...', 'info');
    await Utils.sleep(3000);
    await this.refreshTargetDocument();
    
    // 调试：列出目标文档中的表单元素
    const allInputs = this.targetDoc.querySelectorAll('input, textarea');
    Utils.log(`目标文档共有 ${allInputs.length} 个表单元素`, 'info');
    
    const visibleInputs = Array.from(allInputs).filter(inp => inp.offsetParent !== null);
    Utils.log(`  其中可见的有 ${visibleInputs.length} 个`, 'info');
    visibleInputs.forEach((inp, idx) => {
      Utils.log(`    [${idx+1}] type="${inp.type}" placeholder="${inp.placeholder}" class="${inp.className.substring(0, 40)}"`, 'info');
    });
    
    // 0. 填写客户公司（阿里巴巴）
    await this.fillClientCompany('阿里巴巴集团');
    
    // 1. 填写职位名称
    await this.fillJobName(job.name);
    
    // 2. 填写业务线/部门（若 Excel 未提供则从职位名称推断）
    const departmentName = job.department && job.department.trim()
      ? job.department.trim()
      : this.deriveDepartmentFromName(job.name);
    await this.fillJobDepartment(departmentName);
    
    // 3. 选择职位类型
    await this.selectJobType(job.jobType);
    
    // 4. 设置招聘类型
    const recruitmentType = job.recruitmentType && job.recruitmentType.trim()
      ? job.recruitmentType.trim()
      : CONFIG.DEFAULTS.recruitmentType;
    await this.selectRecruitmentType(recruitmentType);
    
    // 5. 填写职位描述
    await this.fillJobDescription(job.description, job.requirements);
    
    // 6. 选择经验和学历
    await this.selectExperience(job.workYears);
    await this.selectEducation(job.education);
    
    // 7. 填写薪资与招聘人数
    await this.fillSalary(job.salaryMin, job.salaryMax, job.salaryMonths);
    await this.fillHeadcount(job.headcount);
    
    // 8. 添加职位关键词与亮点
    await this.addKeywords(job.keywords);
    await this.fillJobHighlights(job);
    
    // 9. 选择工作地点
    await this.selectLocation(job.city);
    
    // 10. 点击发布
    await this.clickPublish();
    
    Utils.log(`${job.name} 所有字段填写完成`, 'success');
  }
  
  async fillClientCompany(company) {
    Utils.log(`填写客户公司: ${company}`, 'info');
    
    const input = this.targetDoc.querySelector('input[placeholder*="客户公司"]');
    if (!input) {
      Utils.log('⚠️ 未找到客户公司输入框，跳过', 'warning');
      return;
    }
    
    input.value = '';
    input.focus();
    await Utils.sleep(200);
    input.value = '阿里';  // 先输入部分文字触发搜索
    input.dispatchEvent(new Event('input', { bubbles: true }));
    await Utils.sleep(1200);  // 等待下拉建议加载
    
    // 等待下拉建议出现，可能需要滚动查找"阿里巴巴集团"
    const suggestions = document.querySelectorAll('[class*="suggest"], [class*="option"], [class*="item"], li, div[class*="company"]');
    Utils.log(`找到 ${suggestions.length} 个可能的建议项`, 'info');
    
    for (const sug of suggestions) {
      const text = sug.textContent.trim();
      Utils.log(`  检查建议项: "${text.substring(0, 30)}"`, 'info');
      
      if (text.includes('阿里巴巴集团') && sug.offsetParent !== null) {
        Utils.log(`找到匹配项: ${text.substring(0, 30)}`, 'success');
        sug.scrollIntoView({ block: 'center' });  // 滚动到可见
        await Utils.sleep(300);
        sug.click();
        await Utils.sleep(500);
        Utils.log(`✅ 已选择客户公司: 阿里巴巴集团`, 'success');
        return;
      }
    }
    
    const fallbackOption = await this.waitForElement(() => this.findElementByText('阿里巴巴集团', {
      selector: '[role="option"], .suggestion-item, .select-option, li, span, div',
      fuzzy: true,
      maxLength: 20
    }), 2500, 200);
    
    if (fallbackOption) {
      fallbackOption.click();
      await Utils.sleep(400);
      Utils.log('✅ 通过全局搜索选择客户公司: 阿里巴巴集团', 'success');
      return;
    }
    
    Utils.log(`⚠️ 未找到"阿里巴巴集团"建议项，保留已填写的文字`, 'warning');
  }
  
  async fillJobName(name) {
    Utils.log(`填写职位名称: ${name}`, 'info');
    
    // 在目标文档（可能是 iframe）中查找
    const input = this.targetDoc.querySelector('input[placeholder*="职位名称"]') ||
                  this.targetDoc.querySelector('input[placeholder*="请填写职位名称"]') ||
                  this.targetDoc.querySelector('input[type="text"]:not([type="hidden"])');
    
    if (!input) {
      // 调试：列出所有输入框
      const allInputs = this.targetDoc.querySelectorAll('input');
      Utils.log(`调试：目标文档中共有 ${allInputs.length} 个 input:`, 'info');
      for (let i = 0; i < Math.min(allInputs.length, 15); i++) {
        const inp = allInputs[i];
        const visible = inp.offsetParent !== null;
        Utils.log(`  [${i+1}] type="${inp.type}" placeholder="${inp.placeholder}" visible=${visible}`, 'info');
      }
      throw new Error('未找到职位名称输入框');
    }
    
    Utils.log(`找到职位名称输入框: placeholder="${input.placeholder}"`, 'success');
    input.value = '';
    input.focus();
    await Utils.sleep(200);
    input.value = name;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已填写职位名称: ${name}`, 'success');
  }
  
  async fillJobDepartment(department) {
    const targetValue = department && department.trim() ? department.trim() : CONFIG.DEFAULTS.departmentFallback;
    Utils.log(`填写业务线/部门: ${targetValue}`, 'info');
    
    const input = this.targetDoc.querySelector('input[placeholder*="业务线"], input[placeholder*="部门"]');
    if (!input) {
      Utils.log('⚠️ 未找到业务线/部门输入框，跳过', 'warning');
      return;
    }
    
    input.value = '';
    input.focus();
    await Utils.sleep(200);
    input.value = targetValue;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已填写业务线/部门: ${targetValue}`, 'success');
  }
  
  async selectJobType(jobType) {
    Utils.log(`选择职位类型: ${jobType}`, 'info');
    
    const mapping = CONFIG.MAPPINGS.jobType[jobType];
    if (!mapping) {
      Utils.log(`⚠️ 未找到职位类型映射: ${jobType}，将跳过`, 'warning');
      return;
    }
    
    // 查找职位类型输入框（placeholder="选择职位类型"）
    const typeInput = this.targetDoc.querySelector('input[placeholder*="职位类型"]') ||
                      this.targetDoc.querySelector('input.ipt.job-type-input') ||
                      this.targetDoc.querySelector('input[placeholder="选择职位类型"]');
    
    if (!typeInput) {
      throw new Error('未找到职位类型输入框');
    }
    
    Utils.log('找到职位类型输入框，点击打开选择器...', 'success');
    typeInput.click();
    await Utils.sleep(CONFIG.DELAYS.dialog_wait);
    
    // 在弹窗中按层级选择（弹窗通常在主文档）
    for (let i = 0; i < mapping.length; i++) {
      const category = mapping[i];
      Utils.log(`  选择第 ${i + 1} 级: ${category}`, 'info');
      
      // 查找所有可点击元素（只查找对话框内的）
      const dialogs = document.querySelectorAll('[class*="dialog"], [role="dialog"]');
      let found = false;
      
      for (const dialog of dialogs) {
        if (dialog.offsetParent === null) continue;
        
        // 在对话框内查找所有可能的选项元素
        const allElements = dialog.querySelectorAll('div, button, span, a, li');
        
        for (const elem of allElements) {
          // 精确匹配：元素的直接文本内容（不包括子元素）
          const directText = Array.from(elem.childNodes)
            .filter(node => node.nodeType === Node.TEXT_NODE)
            .map(node => node.textContent.trim())
            .join('')
            .replace(/\s+/g, '');
          
          const fullText = elem.textContent.trim().replace(/\s+/g, '');
          
          // 匹配条件：元素的文本内容等于目标（忽略空格）且元素可见
          if ((directText === category.replace(/\s+/g, '') || fullText === category.replace(/\s+/g, '')) && 
              elem.offsetParent !== null) {
            
            // 额外检查：确保不是父容器（子元素数量少）
            const childCount = elem.querySelectorAll('*').length;
            if (childCount < 10) {
              Utils.log(`    找到选项: ${category} (tag=${elem.tagName}, class=${elem.className.substring(0,20)})`, 'success');
              elem.click();
              found = true;
              await Utils.sleep(800); // 等待下一级展开
              break;
            }
          }
        }
        
        if (found) break;
      }
      
      if (!found) {
        Utils.log(`  未找到 "${category}"，尝试调试...`, 'warning');
        // 列出对话框中文本长度<20的所有可见元素
        for (const dialog of dialogs) {
          if (dialog.offsetParent === null) continue;
          const shortElements = Array.from(dialog.querySelectorAll('div, span, button, a, li'))
            .filter(e => e.offsetParent !== null && e.textContent.trim().length < 30 && e.querySelectorAll('*').length < 5)
            .slice(0, 15);
          Utils.log(`  对话框中的短文本元素（可能是选项）:`, 'info');
          shortElements.forEach(e => {
            Utils.log(`    "${e.textContent.trim()}" (${e.tagName}.${e.className.substring(0,15)})`, 'info');
          });
        }
        throw new Error(`未找到职位类型选项: ${category}`);
      }
    }
    
    // 职位类型选择完成后，可能需要关闭对话框
    await Utils.sleep(500);
    
    // 尝试点击对话框的关闭或确定按钮
    const dialogs = document.querySelectorAll('[class*="dialog"], [role="dialog"]');
    for (const dialog of dialogs) {
      if (dialog.offsetParent !== null) {
        const closeBtn = dialog.querySelector('.close, .icon-close, [aria-label="关闭"]');
        if (closeBtn && closeBtn.offsetParent !== null) {
          closeBtn.click();
          await Utils.sleep(500);
          Utils.log(`已关闭职位类型对话框`, 'info');
          break;
        }
      }
    }
    
    const typeInputValue = (typeInput.value || '').trim();
    if (!typeInputValue) {
      typeInput.value = mapping[mapping.length - 1];
      typeInput.setAttribute('data-selected-path', mapping.join(' / '));
      typeInput.dispatchEvent(new Event('input', { bubbles: true }));
      typeInput.dispatchEvent(new Event('change', { bubbles: true }));
      Utils.log('职位类型输入框未显示结果，已写入最后一级值', 'warning');
    }
    
    Utils.log(`✅ 职位类型已选择: ${jobType}`, 'success');
  }
  
  async fillJobDescription(description, requirements) {
    Utils.log(`填写职位描述（${description.length} 字 + 岗位要求）`, 'info');
    
    const combined = `${description}\n\n【岗位要求】\n${requirements}`;
    const textarea = this.targetDoc.querySelector('textarea[placeholder*="职位描述"]') ||
                     this.targetDoc.querySelector('textarea');
    if (!textarea) throw new Error('未找到职位描述输入框');
    
    textarea.value = '';
    textarea.focus();
    await Utils.sleep(200);
    textarea.value = combined;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已填写职位描述`, 'success');
  }
  
  async selectRecruitmentType(type) {
    const targetType = type && type.trim() ? type.trim() : CONFIG.DEFAULTS.recruitmentType;
    Utils.log(`设置招聘类型: ${targetType}`, 'info');
    
    const normalizedTarget = this.normalizeText(targetType);
    let clicked = false;
    
    // 优先在“招聘类型”区域内查找
    const label = Array.from(this.targetDoc.querySelectorAll('div, span, label')).find(elem =>
      elem.offsetParent !== null && this.normalizeText(elem.textContent).includes('招聘类型')
    );
    
    if (label) {
      const container = label.closest('[class*="form"], [class*="item"], .job-form-item') || label.parentElement;
      if (container) {
        const directOptions = Array.from(container.querySelectorAll('span, div, button, label')).filter(elem => elem.offsetParent !== null);
        for (const option of directOptions) {
          if (this.normalizeText(option.textContent) === normalizedTarget) {
            option.click();
            clicked = true;
            break;
          }
        }
        
        if (!clicked) {
          const input = container.querySelector('input[placeholder*="招聘类型"]');
          if (input) {
            input.click();
            await Utils.sleep(CONFIG.DELAYS.dialog_wait);
          }
        }
      }
    }
    
    if (!clicked) {
      const optionElem = await this.waitForElement(() => this.findDropdownOption(targetType, {
        selectorGroups: [
          '[role="option"]',
          '.ui-select-dropdown [role="option"]',
          '.ui-select-dropdown li',
          '.boss-select-dropdown li',
          '.select-option',
          '.dropdown li',
          'li',
          'span'
        ],
        fuzzy: true,
        maxLength: 20
      }), 4000, 200);
      
      if (optionElem) {
        optionElem.click();
        clicked = true;
      }
    }
    
    if (clicked) {
      Utils.log(`✅ 已设置招聘类型: ${targetType}`, 'success');
    } else {
      Utils.log('⚠️ 未能设置招聘类型，保留默认值', 'warning');
    }
  }
  
  async selectExperience(workYears) {
    Utils.log(`选择工作年限: ${workYears}`, 'info');
    
    const mapped = CONFIG.MAPPINGS.workYears[workYears];
    if (!mapped) {
      Utils.log(`⚠️ 未找到工作年限映射: ${workYears}`, 'warning');
      return;
    }
    
    await this.refreshTargetDocument('经验和学历');
    await this.ensureFieldVisible('经验和学历', { forceDeepScroll: true });
    
    // 查找"选择经验"下拉框
    const experienceInputs = this.targetDoc.querySelectorAll('input[placeholder*="经验"], div[class*="select"]');
    Utils.log(`找到 ${experienceInputs.length} 个经验相关元素`, 'info');
    
    let experienceSelect = null;
    
    // 尝试通过 placeholder 查找
    for (const elem of experienceInputs) {
      if (elem.offsetParent !== null && elem.placeholder && elem.placeholder.includes('经验')) {
        experienceSelect = elem;
        Utils.log(`通过 placeholder 找到经验输入框`, 'success');
        break;
      }
    }
    
    // 如果没找到，尝试通过"经验和学历"标签定位
    if (!experienceSelect) {
      const labels = Array.from(this.targetDoc.querySelectorAll('div, label, span')).filter(elem => 
        elem.textContent.trim() === '经验和学历' && elem.offsetParent !== null
      );
      
      if (labels.length > 0) {
        const parent = labels[0].parentElement || labels[0].closest('div[class*="form-item"]');
        if (parent) {
          const selects = parent.querySelectorAll('div[class*="select"], input, button');
          if (selects.length >= 1) {
            experienceSelect = selects[0];
            Utils.log(`通过"经验和学历"标签找到第1个下拉框`, 'success');
          }
        }
      }
    }
    
    if (!experienceSelect) throw new Error('未找到经验下拉框');
    
    Utils.log(`点击经验下拉框: ${experienceSelect.tagName} class="${experienceSelect.className}"`, 'info');
    experienceSelect.click();
    
    // 循环等待下拉选项出现（最多等待3秒）
    let found = false;
    const maxWait = 6000;
    const checkInterval = 300;
    let waited = 0;
    let extraScrollDone = false;
    
    while (waited < maxWait && !found) {
      const optionElem = this.findDropdownOption(mapped, { fuzzy: true, maxLength: 20 });
      if (optionElem) {
        Utils.log(`找到经验选项: ${mapped} (等待${waited}ms)`, 'success');
        optionElem.click();
        found = true;
        break;
      }
      
      if (!extraScrollDone && waited >= 3000) {
        extraScrollDone = true;
        await this.forceDeepScroll();
        await this.refreshTargetDocument('经验');
      }
      
      await Utils.sleep(checkInterval);
      waited += checkInterval;
      
      if (waited % 1000 === 0 && !found) {
        Utils.log(`  等待经验选项出现... (${waited/1000}秒)`, 'info');
      }
    }
    
    if (!found) {
      // 最终调试：列出所有短文本的可见元素
      Utils.log(`未找到经验选项"${mapped}"（等待了${waited}ms），列出可见的短文本元素:`, 'warning');
      
      const allShort = Array.from(document.querySelectorAll('div, li, span'))
        .filter(e => e.offsetParent !== null && e.textContent.trim().length < 20 && e.textContent.trim().length > 0 && e.querySelectorAll('*').length < 2)
        .slice(0, 20);
      
      allShort.forEach(e => {
        Utils.log(`  - "${e.textContent.trim()}" (${e.tagName}.${e.className.substring(0,15)})`, 'info');
      });
      
      throw new Error(`未找到经验选项: ${mapped}`);
    }
    
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已选择经验: ${mapped}`, 'success');
  }
  
  async selectEducation(education) {
    Utils.log(`选择学历: ${education}`, 'info');
    
    const mapped = CONFIG.MAPPINGS.education[education] || education;
    
    await this.refreshTargetDocument('经验和学历');
    await this.ensureFieldVisible('经验和学历', { forceDeepScroll: true });
    
    // 查找学历下拉框（经验后面的第二个下拉框）
    const labels = Array.from(this.targetDoc.querySelectorAll('div, label, span')).filter(elem => 
      elem.textContent.includes('经验和学历') && elem.offsetParent !== null
    );
    
    if (labels.length === 0) throw new Error('未找到学历选择区域');
    
    const selects = labels[0].parentElement.querySelectorAll('div[class*="select"], button[class*="select"]');
    if (selects.length < 2) throw new Error('未找到学历下拉框');
    
    const educationSelect = selects[1];
    educationSelect.click();
    await Utils.sleep(500);
    
    const optionElem = await this.waitForElement(() => this.findDropdownOption(mapped, {
      fuzzy: true,
      maxLength: 20
    }), 3000, 200);
    
    if (!optionElem) {
      throw new Error(`未找到学历选项: ${mapped}`);
    }
    
    optionElem.click();
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已选择学历: ${mapped}`, 'success');
  }
  
  async fillSalary(salaryMin, salaryMax, salaryMonths = CONFIG.DEFAULTS.salaryMonths) {
    Utils.log(`填写薪资: ${salaryMin}-${salaryMax}`, 'info');
    
    if (!salaryMin || !salaryMax) {
      Utils.log('⚠️ 薪资区间缺失，跳过', 'warning');
      return;
    }
    
    // 转换为k（千元）
    const minK = Math.floor(Number(salaryMin) / 1000);
    const maxK = Math.floor(Number(salaryMax) / 1000);
    
    Utils.log(`薪资转换: ${salaryMin}-${salaryMax} → ${minK}k-${maxK}k`, 'info');
    
    await this.refreshTargetDocument('薪资范围');
    await this.ensureFieldVisible('薪资范围', { forceDeepScroll: true });
    
    // 查找"薪资范围"区域的下拉框（有3个：最低月薪、最高月薪、月数）
    const salaryLabels = Array.from(this.targetDoc.querySelectorAll('div, span')).filter(elem => 
      elem.textContent.trim() === '薪资范围' && elem.offsetParent !== null
    );
    
    if (salaryLabels.length === 0) {
      Utils.log('⚠️ 未找到薪资范围区域，跳过', 'warning');
      return;
    }
    
    const parent = salaryLabels[0].parentElement || salaryLabels[0].closest('div[class*="form-item"]');
    if (!parent) {
      Utils.log('⚠️ 未找到薪资范围父容器', 'warning');
      return;
    }
    
    const selects = parent.querySelectorAll('div[class*="select"], input[placeholder*="月薪"]');
    Utils.log(`薪资区域找到 ${selects.length} 个选择器`, 'info');
    
    if (selects.length < 2) {
      Utils.log('⚠️ 薪资下拉框数量不足，跳过', 'warning');
      return;
    }
    
    // 选择最低月薪
    Utils.log(`点击最低月薪下拉框...`, 'info');
    selects[0].click();
    await Utils.sleep(600);
    
    const minOption = await this.waitForElement(() => this.findDropdownOption(`${minK}k`, {
      fuzzy: false,
      maxLength: 10
    }), 3000, 200);
    
    if (minOption) {
      minOption.click();
      Utils.log(`✅ 已选择最低月薪: ${minK}k`, 'success');
    } else {
      Utils.log(`⚠️ 未找到最低月薪选项: ${minK}k`, 'warning');
    }
    
    await Utils.sleep(400);
    
    // 选择最高月薪
    Utils.log(`点击最高月薪下拉框...`, 'info');
    selects[1].click();
    await Utils.sleep(600);
    
    const maxOption = await this.waitForElement(() => this.findDropdownOption(`${maxK}k`, {
      fuzzy: false,
      maxLength: 10
    }), 3000, 200);
    
    if (maxOption) {
      maxOption.click();
      Utils.log(`✅ 已选择最高月薪: ${maxK}k`, 'success');
    } else {
      Utils.log(`⚠️ 未找到最高月薪选项: ${maxK}k`, 'warning');
    }
    
    // 选择发薪月份（若存在第三个下拉框）
    if (selects.length >= 3 && salaryMonths) {
      Utils.log(`点击发薪月份下拉框...`, 'info');
      selects[2].click();
      await Utils.sleep(400);
      
      const monthsOption = await this.waitForElement(() => this.findDropdownOption(salaryMonths, {
        fuzzy: true,
        maxLength: 10
      }), 3000, 200);
      
      if (monthsOption) {
        monthsOption.click();
        Utils.log(`✅ 已选择发薪月份: ${salaryMonths}`, 'success');
      } else {
        Utils.log(`⚠️ 未找到发薪月份选项: ${salaryMonths}`, 'warning');
      }
    }
    
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 薪资范围已设置`, 'success');
  }
  
  async fillHeadcount(headcountValue) {
    const value = headcountValue && String(headcountValue).trim()
      ? String(headcountValue).trim()
      : CONFIG.DEFAULTS.headcount;
    
    Utils.log(`填写招聘人数: ${value}`, 'info');
    
    await this.refreshTargetDocument('招聘人数');
    await this.ensureFieldVisible('招聘人数', { forceDeepScroll: true });
    
    const input = this.targetDoc.querySelector('input[placeholder*="招聘人数"], input[placeholder*="人数"], input[name*="headcount"]');
    if (!input) {
      Utils.log('⚠️ 未找到招聘人数输入框，跳过', 'warning');
      return;
    }
    
    input.value = '';
    input.focus();
    await Utils.sleep(150);
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log(`✅ 已填写招聘人数: ${value}`, 'success');
  }
  
  async addKeywords(keywordsStr) {
    Utils.log(`添加职位关键词`, 'info');
    
    await this.refreshTargetDocument('职位关键词');
    await this.ensureFieldVisible('职位关键词', { forceDeepScroll: true });
    
    const keywords = this.parseKeywordList(keywordsStr);
    if (keywords.length === 0) {
      Utils.log('无关键词需要添加', 'info');
      return;
    }
    
    // 点击"请选择职位关键词"（可能在 iframe 或主文档）
    const searchScopes = [this.targetDoc, document];
    let keywordBtn = null;
    
    for (const doc of searchScopes) {
      const btns = Array.from(doc.querySelectorAll('div, button, span')).filter(elem => 
        elem.textContent.includes('请选择职位关键词') && elem.offsetParent !== null
      );
      if (btns.length > 0) {
        keywordBtn = btns[0];
        break;
      }
    }
    
    if (!keywordBtn) {
      Utils.log('⚠️ 未找到关键词选择按钮，跳过', 'warning');
      return;
    }
    
    keywordBtn.click();
    Utils.log('已打开关键词对话框', 'info');
    await Utils.sleep(CONFIG.DELAYS.dialog_wait);
    
    // 逐个添加自定义关键词（最多8个）
    const maxKeywords = Math.min(keywords.length, 8);
    for (let i = 0; i < maxKeywords; i++) {
      const keyword = keywords[i];
      Utils.log(`  添加关键词 ${i + 1}/${maxKeywords}: ${keyword}`, 'info');
      
      // 点击"+ 自定义关键词"（对话框可能在主文档）
      const addBtns = Array.from(document.querySelectorAll('div, button, span, a')).filter(elem => 
        elem.textContent.includes('自定义关键词') && elem.offsetParent !== null
      );
      
      if (addBtns.length === 0) {
        Utils.log('  未找到"自定义关键词"按钮', 'warning');
        break;
      }
      
      addBtns[0].click();
      await Utils.sleep(800);
      
      // 填写关键词输入框（对话框在主文档）
      const keywordInput = document.querySelector('input[placeholder*="关键词"], input[placeholder*="职位关键词"]');
      if (!keywordInput) {
        Utils.log('  未找到关键词输入框', 'warning');
        break;
      }
      
      keywordInput.value = '';
      keywordInput.focus();
      await Utils.sleep(200);
      keywordInput.value = keyword;
      keywordInput.dispatchEvent(new Event('input', { bubbles: true }));
      await Utils.sleep(300);
      
      // 点击"确定"按钮
      const confirmBtns = Array.from(document.querySelectorAll('button, a, div')).filter(elem => 
        elem.textContent.trim() === '确定' && elem.offsetParent !== null
      );
      
      if (confirmBtns.length > 0) {
        confirmBtns[0].click();
        await Utils.sleep(500);
      }
    }
    
    // 关闭关键词对话框
    const closeBtns = document.querySelectorAll('.close, .icon-close, [aria-label="关闭"]');
    for (const btn of closeBtns) {
      if (btn.offsetParent !== null) {
        btn.click();
        break;
      }
    }
    
    await Utils.sleep(500);
    Utils.log(`✅ 已添加 ${maxKeywords} 个关键词`, 'success');
  }
  
  async fillJobHighlights(job) {
    const textarea = this.targetDoc.querySelector('textarea[placeholder*="职位诱惑"], textarea[placeholder*="亮点"], textarea[placeholder*="补充"]');
    const highlightText = job?.highlights && job.highlights.trim() ? job.highlights.trim() : this.buildDefaultHighlights(job);
    
    await this.refreshTargetDocument('职位诱惑');
    await this.ensureFieldVisible('职位诱惑', { forceDeepScroll: true });
    
    if (!textarea) {
      Utils.log('⚠️ 未找到职位亮点输入框，跳过', 'warning');
      return;
    }
    
    if (!highlightText) {
      Utils.log('⚠️ 无可用的职位亮点内容，跳过', 'warning');
      return;
    }
    
    Utils.log('填写职位亮点/诱惑', 'info');
    textarea.value = '';
    textarea.focus();
    await Utils.sleep(200);
    textarea.value = highlightText;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    await Utils.sleep(CONFIG.DELAYS.field_fill);
    Utils.log('✅ 已填写职位亮点', 'success');
  }
  
  async selectLocation(cityStr) {
    Utils.log(`选择工作地点: ${cityStr}`, 'info');
    
    // 提取城市名（如 "中国-北京-北京" → "北京"）
    const city = cityStr.split(',')[0]?.split('-').pop()?.trim() || cityStr;
    
    await this.refreshTargetDocument('工作地点');
    await this.ensureFieldVisible('工作地点', { forceDeepScroll: true });
    
    // 查找工作地点输入框
    const locationInputs = this.targetDoc.querySelectorAll('input[placeholder*="地点"], input[placeholder*="城市"]');
    if (locationInputs.length === 0) throw new Error('未找到工作地点输入框');
    
    const locationInput = locationInputs[0];
    locationInput.value = '';
    locationInput.focus();
    await Utils.sleep(200);
    locationInput.value = city;
    locationInput.dispatchEvent(new Event('input', { bubbles: true }));
    
    // 等待地点弹窗出现
    await Utils.sleep(CONFIG.DELAYS.dialog_wait);
    
    // 点击"使用该地址"按钮（弹窗可能在主文档）
    const useBtns = Array.from(document.querySelectorAll('button, a, div')).filter(elem => 
      elem.textContent.includes('使用该地址') && elem.offsetParent !== null
    );
    
    if (useBtns.length === 0) {
      Utils.log('⚠️ 未找到"使用该地址"按钮，尝试直接确认', 'warning');
      
      // 可能需要点击建议的第一个地址
      const suggestions = document.querySelectorAll('[class*="suggest"], [class*="address-item"]');
      if (suggestions.length > 0 && suggestions[0].offsetParent !== null) {
        suggestions[0].click();
        await Utils.sleep(500);
      }
    } else {
      useBtns[0].click();
      await Utils.sleep(500);
    }
    
    Utils.log(`✅ 已选择地点: ${city}`, 'success');
  }
  
  async clickPublish() {
    Utils.log('点击发布按钮...', 'info');
    
    // 查找发布按钮（可能在 iframe 或主文档）
    const searchScopes = [this.targetDoc, document];
    let publishBtn = null;
    
    for (const doc of searchScopes) {
      const btns = Array.from(doc.querySelectorAll('button, a')).filter(elem => 
        (elem.textContent.trim() === '发布' || elem.textContent.trim() === '提交') && 
        elem.offsetParent !== null &&
        !elem.disabled &&
        !elem.classList.contains('disabled')
      );
      if (btns.length > 0) {
        publishBtn = btns[0];
        break;
      }
    }
    
    if (!publishBtn) throw new Error('未找到发布按钮或按钮被禁用');
    
    publishBtn.click();
    await Utils.sleep(2000);
    
    Utils.log('✅ 已点击发布按钮', 'success');
  }
  
  exportReport() {
    Utils.log('导出发布报告...', 'info');
    
    const headers = ['序号', '职位名称', '状态', '错误信息'];
    const rows = this.results.map(r => [
      r.index,
      r.name,
      r.status === 'success' ? '成功' : '失败',
      r.error || ''
    ]);
    
    const csv = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Boss职位发布报告-${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    
    Utils.log('✅ 发布报告已导出', 'success');
  }
  
  normalizeText(text = '') {
    return (text || '').replace(/\s+/g, '').trim();
  }
  
  deriveDepartmentFromName(name = '') {
    const fallback = CONFIG.DEFAULTS.departmentFallback;
    if (!name) return fallback;
    
    const parts = name.split(/[-—]/).map(seg => seg.trim()).filter(Boolean);
    if (parts.length > 1) return `${parts[0]}团队`;
    
    const trimmed = name.trim();
    if (!trimmed) return fallback;
    
    const shortened = trimmed.length > 12 ? trimmed.slice(0, 12) : trimmed;
    return `${shortened}团队`;
  }
  
  parseKeywordList(value) {
    if (Array.isArray(value)) {
      return value.map(item => String(item).trim()).filter(Boolean);
    }
    
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) return [];
      try {
        const parsed = JSON.parse(trimmed.replace(/'/g, '"'));
        if (Array.isArray(parsed)) {
          return parsed.map(item => String(item).trim()).filter(Boolean);
        }
      } catch (e) {
        return trimmed
          .replace(/[\[\]]/g, '')
          .split(/[,，]/)
          .map(item => item.trim())
          .filter(Boolean);
      }
    }
    
    return [];
  }
  
  buildDefaultHighlights(job) {
    if (!job) return '';
    const keywords = this.parseKeywordList(job.keywords);
    if (keywords.length >= 2) {
      return `岗位亮点：${keywords.slice(0, 3).join('、')}`;
    }
    if (job.highlights && job.highlights.trim()) {
      return job.highlights.trim();
    }
    if (job.requirements && job.requirements.trim()) {
      return `岗位亮点：${job.requirements.trim().slice(0, 80)}...`;
    }
    if (job.description && job.description.trim()) {
      return `岗位亮点：${job.description.trim().slice(0, 80)}...`;
    }
    return '';
  }
  
  async refreshTargetDocument(labelText = '') {
    const normalizedLabel = this.normalizeText(labelText);
    const candidates = [];
    const visited = new Set();
    
    const collectDocs = (doc, frameEl, depth) => {
      if (!doc || visited.has(doc)) return;
      visited.add(doc);
      
      let formCount = 0;
      let labelMatches = false;
      try {
        formCount = doc.querySelectorAll('input, textarea, select').length;
      } catch (e) {
        formCount = 0;
      }
      
      if (normalizedLabel) {
        try {
          labelMatches = Array.from(doc.querySelectorAll('div, span, label, h2, h3')).some(elem => 
            elem.offsetParent !== null && this.normalizeText(elem.textContent).includes(normalizedLabel)
          );
        } catch (e) {
          labelMatches = false;
        }
      }
      
      candidates.push({ doc, frame: frameEl || null, depth, formCount, labelMatches });
      
      let frames = [];
      try {
        frames = Array.from(doc.querySelectorAll('iframe'));
      } catch (e) {
        frames = [];
      }
      
      for (const frame of frames) {
        try {
          const innerDoc = frame.contentDocument || frame.contentWindow?.document;
          if (innerDoc) {
            collectDocs(innerDoc, frame, depth + 1);
          }
        } catch (e) {
          // ignore cross-origin frames
        }
      }
    };
    
    if (document) {
      collectDocs(document, null, 0);
    }
    if (this.targetDoc && this.targetDoc !== document) {
      collectDocs(this.targetDoc, this.iframe || null, 0);
    }
    
    if (candidates.length === 0) {
      return;
    }
    
    let best = candidates.find(c => c.doc === this.targetDoc) || candidates[0];
    for (const candidate of candidates) {
      if (candidate.labelMatches && !best.labelMatches) {
        best = candidate;
        continue;
      }
      if (candidate.labelMatches === best.labelMatches) {
        if (candidate.formCount > best.formCount) {
          best = candidate;
          continue;
        }
        if (candidate.formCount === best.formCount && candidate.depth > best.depth) {
          best = candidate;
        }
      }
    }
    
    if (best.doc && best.doc !== this.targetDoc) {
      this.targetDoc = best.doc;
      this.iframe = best.frame || null;
      Utils.log(`已切换目标文档：深度 ${best.depth}，字段数 ${best.formCount}`, 'info');
    }
  }
  
  async forceDeepScroll() {
    if (!this.targetDoc) return;
    const scroller = this.iframe?.contentWindow || window;
    if (!scroller || typeof scroller.scrollTo !== 'function') return;
    
    const docEl = this.targetDoc.documentElement || document.documentElement;
    const body = this.targetDoc.body || document.body;
    const scrollHeight = Math.max(
      docEl?.scrollHeight || 0,
      body?.scrollHeight || 0
    );
    
    if (!scrollHeight) return;
    
    for (let i = 0; i < 2; i++) {
      scroller.scrollTo({ top: scrollHeight, behavior: 'auto' });
      await Utils.sleep(350);
    }
    
    scroller.scrollTo({ top: scrollHeight, behavior: 'auto' });
    await Utils.sleep(400);
  }
  
  async ensureFieldVisible(labelText, options = {}) {
    if (!labelText || !this.targetDoc) return null;
    
    const searchOptions = {
      selector: 'div, span, label, h2, h3',
      fuzzy: true,
      maxLength: 80,
      scopes: [this.targetDoc]
    };
    
    const updateScopes = () => {
      searchOptions.scopes = [this.targetDoc];
    };
    updateScopes();
    
    const findLabel = () => this.findElementByText(labelText, searchOptions);
    let labelElem = findLabel();
    
    if (!labelElem) {
      if (options.forceDeepScroll) {
        await this.forceDeepScroll();
      }
      await this.refreshTargetDocument(labelText);
      updateScopes();
      labelElem = findLabel();
    }
    
    if (!labelElem && !options.forceDeepScroll) {
    await this.forceDeepScroll();
      await this.refreshTargetDocument(labelText);
      updateScopes();
      labelElem = findLabel();
    }
    
    if (!labelElem) return null;
    
    const scrollContainer = this.iframe?.contentWindow || window;
    const viewportHeight = this.iframe?.clientHeight || window.innerHeight || 800;
    let attempts = 0;
    
    while (attempts < 6) {
      const rect = labelElem.getBoundingClientRect();
      if (rect.top >= 40 && rect.bottom <= viewportHeight - 40) {
        break;
      }
      
      const delta = rect.top - viewportHeight / 2;
      if (Math.abs(delta) < 10 || typeof scrollContainer.scrollBy !== 'function') {
        break;
      }
      
      scrollContainer.scrollBy(0, delta);
      await Utils.sleep(400);
      labelElem = findLabel() || labelElem;
      attempts += 1;
      
      if (attempts === 3 && options.forceDeepScroll) {
        await this.forceDeepScroll();
        await this.refreshTargetDocument(labelText);
        updateScopes();
      }
    }
    
    await Utils.sleep(250);
    return labelElem;
  }
  
  getSearchScopes() {
    const scopes = [];
    if (this.targetDoc && !scopes.includes(this.targetDoc)) scopes.push(this.targetDoc);
    if (document && !scopes.includes(document)) scopes.push(document);
    return scopes;
  }
  
  async waitForElement(predicateFn, timeout = 4000, interval = 200) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      try {
        const result = predicateFn();
        if (result) return result;
      } catch (e) {
        // 忽略临时错误
      }
      await Utils.sleep(interval);
    }
    return null;
  }
  
  findElementByText(targetText, options = {}) {
    const normalizedTarget = this.normalizeText(targetText);
    if (!normalizedTarget) return null;
    
    const {
      selector = 'div, li, span, a, button',
      scopes = this.getSearchScopes(),
      fuzzy = false,
      maxLength = 40
    } = options;
    
    for (const scope of scopes) {
      let elements = [];
      try {
        elements = Array.from(scope.querySelectorAll(selector));
      } catch (e) {
        continue;
      }
      
      for (const elem of elements) {
        if (!elem || !this.isElementVisible(elem)) continue;
        const text = this.normalizeText(elem.textContent);
        if (!text || text.length > maxLength) continue;
        if (text === normalizedTarget || (fuzzy && text.includes(normalizedTarget))) {
          return elem;
        }
      }
    }
    
    return null;
  }
  
  findDropdownOption(targetText, options = {}) {
    const selectorGroups = options.selectorGroups || [
      '.ui-select-dropdown [role="option"]',
      '.ui-select-dropdown li',
      '.boss-select-dropdown [role="option"]',
      '.boss-select-dropdown li',
      '.select-dropdown [role="option"]',
      '.select-dropdown li',
      '[role="option"]',
      '.select-option',
      '.dropdown li',
      'li',
      'span'
    ];
    
    const normalizedTarget = this.normalizeText(targetText);
    const fuzzy = options.fuzzy ?? false;
    const maxLength = options.maxLength ?? 40;
    const scopes = options.scopes || this.getSearchScopes();
    
    const dropdownContainers = this.getVisibleDropdownContainers(scopes);
    for (const container of dropdownContainers) {
      for (const selector of selectorGroups) {
        let candidates = [];
        try {
          candidates = Array.from(container.querySelectorAll(selector));
        } catch (e) {
          continue;
        }
        for (const elem of candidates) {
          if (!this.isElementVisible(elem)) continue;
          const text = this.normalizeText(elem.textContent);
          if (!text || text.length > maxLength) continue;
          if (text === normalizedTarget || (fuzzy && text.includes(normalizedTarget))) {
            return elem;
          }
        }
      }
    }
    
    for (const selector of selectorGroups) {
      const element = this.findElementByText(targetText, {
        selector,
        fuzzy,
        maxLength,
        scopes
      });
      if (element) return element;
    }
    
    return null;
  }
  
  isElementVisible(elem) {
    if (!elem) return false;
    if (elem.offsetParent !== null) return true;
    const rect = elem.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }
  
  getVisibleDropdownContainers(scopes = this.getSearchScopes()) {
    const selectors = [
      '.ui-select-dropdown',
      '.boss-select-dropdown',
      '.select-dropdown',
      '.dropdown-panel',
      '.dropdown',
      '.ui-select-panel'
    ];
    const containers = [];
    for (const scope of scopes) {
      let elems = [];
      try {
        elems = selectors.flatMap(sel => Array.from(scope.querySelectorAll(sel)));
      } catch (e) {
        continue;
      }
      for (const elem of elems) {
        if (this.isElementVisible(elem) && !containers.includes(elem)) {
          containers.push(elem);
        }
      }
    }
    return containers;
  }
}

// ========== 初始化 ==========
console.log('🤖 Boss职位自动发布助手加载中...');

if (window.location.href.includes('zhipin.com/web/chat/job/edit')) {
  new JobPublisher();
} else {
  console.log('⚠️ 当前不在职位发布页面，插件待命中');
}



