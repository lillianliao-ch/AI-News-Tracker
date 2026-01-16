/**
 * Background Script - 处理截屏请求
 */

// 监听来自 content script 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'captureScreenshot') {
    console.log('收到截屏请求，sender tab:', sender.tab?.id);
    
    // 获取发送消息的标签页所在的窗口 ID
    const tabId = sender.tab?.id;
    if (!tabId) {
      console.error('无法获取标签页 ID');
      sendResponse({ success: false, error: '无法获取标签页 ID' });
      return false; // 同步响应，直接返回
    }
    
    // 先获取标签页信息，得到 windowId
    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError) {
        console.error('获取标签页信息失败:', chrome.runtime.lastError.message);
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
        return;
      }
      
      // 使用 chrome.tabs.captureVisibleTab 截取当前窗口的可见标签页
      chrome.tabs.captureVisibleTab(
        tab.windowId,
        { format: 'png' },
        (dataUrl) => {
          if (chrome.runtime.lastError) {
            console.error('截屏失败:', chrome.runtime.lastError.message);
            sendResponse({ success: false, error: chrome.runtime.lastError.message });
          } else {
            console.log('截屏成功，大小:', (dataUrl.length / 1024).toFixed(2), 'KB');
            sendResponse({ success: true, dataUrl: dataUrl });
          }
        }
      );
    });
    
    // 返回 true 表示异步响应（会等待 sendResponse 调用）
    return true;
  }
});

console.log('🤖 AI猎头助手 Background Script 已加载');

