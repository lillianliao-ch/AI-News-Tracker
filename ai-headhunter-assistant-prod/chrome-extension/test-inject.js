// 简单的测试脚本 - 验证插件是否注入
console.log('================================');
console.log('🚀🚀🚀 插件测试脚本已加载！');
console.log('当前URL:', window.location.href);
console.log('================================');

// 在页面上添加一个明显的标记
setTimeout(() => {
  const testDiv = document.createElement('div');
  testDiv.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: red;
    color: white;
    padding: 20px;
    border-radius: 8px;
    z-index: 999999;
    font-size: 16px;
    font-weight: bold;
  `;
  testDiv.textContent = '🚀 插件已成功注入！';
  document.body.appendChild(testDiv);
  
  console.log('✅ 测试标记已添加到页面');
}, 1000);

