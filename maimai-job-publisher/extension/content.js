/**
 * 脉脉职位自动发布 - Content Script
 */

const Utils = {
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
  log(msg) {
    console.log(`[脉脉发布助手] ${msg}`);
  }
};

class MaimaiPublisher {
  constructor() {
    this.init();
  }

  init() {
    Utils.log("插件已加载");
    // 监听来自 Popup 的消息
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'startPublish') {
        this.handleBatchPublish(request.jobs);
        sendResponse({ success: true });
      }
    });
  }

  async handleBatchPublish(jobs) {
    Utils.log(`收到 ${jobs.length} 个职位任务`);
    
    if (jobs.length > 0) {
      // 演示版：只处理第一个职位
      const job = jobs[0];
      await this.fillJobForm(job);
      
      // 提示用户
      // 实际生产中，这里应该把剩余 jobs 存回 storage，
      // 并在页面刷新/跳转后继续执行
      alert(`✅ 职位 "${job.job_name || job.name}" 已填写！\n\n请检查内容并手动点击【发布职位】。\n\n(目前仅支持单次填充，更多自动化需进一步开发)`);
    }
  }

  async fillJobForm(job) {
    const name = job.job_name || job.name;
    const desc = job.description;
    
    Utils.log(`开始填写职位: ${name}`);

    // 1. 职位名称
    // 脉脉 placeholder: "请输入职位名称"
    await this.fillInputByPlaceholder("请输入职位名称", name);

    // 2. 职位描述
    // 脉脉 placeholder: "请输入岗位职责、任职要求等..."
    // 使用部分匹配
    await this.fillInputByPlaceholder("岗位职责", desc, true);

    // 3. 邮箱
    if (job.email) {
      const emailInput = document.querySelector('input[value*="@"]');
      if (emailInput) {
        this.setNativeValue(emailInput, job.email);
      }
    }
    
    // 4. 简单处理下拉框 (如果能匹配到文本)
    // 比如 "经验要求"
    if (job.experience) {
        // 这是一个占位符逻辑，实际脉脉的下拉框比较复杂（通常是 div 模拟的）
        // 需要点击 -> 等待 DOM 变化 -> 点击选项
        // await this.clickSelectorText('.select-placeholder', job.experience);
    }

    Utils.log("基础信息填写完成");
  }

  async fillInputByPlaceholder(placeholderText, value, partial = false) {
    if (!value) return;
    
    // 查找所有可见的 input 和 textarea
    const inputs = Array.from(document.querySelectorAll('input, textarea'));
    let target = null;
    
    for (const input of inputs) {
      const ph = input.placeholder || "";
      if (partial) {
        if (ph.includes(placeholderText)) {
          target = input;
          break;
        }
      } else {
        if (ph === placeholderText) {
          target = input;
          break;
        }
      }
    }

    if (target) {
      target.scrollIntoView({ block: "center" });
      await Utils.sleep(300);
      this.setNativeValue(target, value);
      Utils.log(`已填写 [${placeholderText}]: ${value.substring(0, 10)}...`);
    } else {
      Utils.log(`❌ 未找到输入框: ${placeholderText}`);
    }
  }

  // 模拟 React/Vue 的输入事件
  setNativeValue(element, value) {
    const lastValue = element.value;
    element.value = value;
    const event = new Event("input", { bubbles: true });
    // React 16+ value tracker hack
    const tracker = element._valueTracker;
    if (tracker) {
      tracker.setValue(lastValue);
    }
    element.dispatchEvent(event);
  }
}

new MaimaiPublisher();

