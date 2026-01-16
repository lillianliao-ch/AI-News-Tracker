// 最简单的测试 - 验证能否注入
console.log('===========================================');
console.log('✅✅✅ AI猎头助手测试版已成功注入！');
console.log('当前页面:', window.location.href);
console.log('===========================================');

// 在页面添加一个超级明显的红色提示
const testBox = document.createElement('div');
testBox.innerHTML = '🎉 插件成功注入！';
testBox.style.cssText = `
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: red;
  color: white;
  padding: 40px;
  font-size: 24px;
  font-weight: bold;
  border-radius: 12px;
  z-index: 999999;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
`;

document.body.appendChild(testBox);

// 3秒后自动消失
setTimeout(() => {
  testBox.style.opacity = '0';
  testBox.style.transition = 'opacity 1s';
  setTimeout(() => testBox.remove(), 1000);
}, 3000);

