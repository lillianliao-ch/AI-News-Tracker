// Maimai Assistant - 工具函数
class MaimaiUtils {

    // 延迟函数
    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 检测是否为脉脉域名
    static isMaimaiDomain() {
        return window.location.hostname === 'maimai.cn' ||
            window.location.hostname === 'www.maimai.cn';
    }

    // 检测页面类型
    static detectPageType() {
        if (!this.isMaimaiDomain()) return null;

        const url = window.location.href;
        if (url.includes('/ent/v41/recruit/talents')) {
            return MAIMAI_CONSTANTS.PAGE_TYPES.TALENTS;
        }
        return MAIMAI_CONSTANTS.PAGE_TYPES.OTHER;
    }

    // 清理文本内容
    static cleanText(text) {
        if (!text) return '';
        return text.trim().replace(/\s+/g, ' ').replace(/\n+/g, ' ');
    }

    // 使用选择器数组查找元素
    static findElement(selectors, parent = document) {
        if (typeof selectors === 'string') {
            selectors = [selectors];
        }
        for (const selector of selectors) {
            try {
                const element = parent.querySelector(selector);
                if (element) return element;
            } catch (e) {
                // 忽略无效选择器
            }
        }
        return null;
    }

    // 使用选择器数组查找所有元素
    static findAllElements(selectors, parent = document) {
        if (typeof selectors === 'string') {
            selectors = [selectors];
        }
        for (const selector of selectors) {
            try {
                const elements = parent.querySelectorAll(selector);
                if (elements.length > 0) return Array.from(elements);
            } catch (e) {
                // 忽略无效选择器
            }
        }
        return [];
    }

    // 安全获取元素文本
    static safeGetText(selectors, parent = document) {
        const element = this.findElement(selectors, parent);
        return element ? this.cleanText(element.textContent) : '';
    }

    // 等待元素出现
    static waitForElement(selectors, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const element = this.findElement(selectors);
            if (element) {
                resolve(element);
                return;
            }

            const observer = new MutationObserver(() => {
                const el = this.findElement(selectors);
                if (el) {
                    observer.disconnect();
                    resolve(el);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element not found within ${timeout}ms`));
            }, timeout);
        });
    }

    // 生成 UUID
    static generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // 格式化日期
    static formatDate(date) {
        if (!date) date = new Date();
        return date.toISOString().split('T')[0];
    }

    // 格式化时间戳
    static formatTimestamp(date) {
        if (!date) date = new Date();
        return date.toISOString();
    }

    // 发送消息到 background
    static async sendMessage(message) {
        try {
            const response = await chrome.runtime.sendMessage(message);
            return response;
        } catch (error) {
            console.error('Message sending failed:', error);
            throw error;
        }
    }

    // 显示通知
    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `maimai-notification maimai-notification-${type}`;
        notification.textContent = message;

        const colors = {
            info: '#1890ff',
            success: '#52c41a',
            error: '#ff4d4f',
            warning: '#faad14'
        };

        notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${colors[type] || colors.info};
      color: white;
      padding: 12px 20px;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 100000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      max-width: 300px;
      animation: slideInFromRight 0.3s ease-out;
    `;

        // 添加动画样式
        if (!document.getElementById('maimai-notification-styles')) {
            const styleSheet = document.createElement('style');
            styleSheet.id = 'maimai-notification-styles';
            styleSheet.textContent = `
        @keyframes slideInFromRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `;
            document.head.appendChild(styleSheet);
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            notification.style.transition = 'all 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // 下载数据为文件
    static downloadAsFile(data, filename, type = 'application/json') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 记录日志
    static log(action, data = {}) {
        console.log('[Maimai Assistant]', action, data);
    }
}

// 导出到全局
if (typeof window !== 'undefined') {
    window.MaimaiUtils = MaimaiUtils;
}
