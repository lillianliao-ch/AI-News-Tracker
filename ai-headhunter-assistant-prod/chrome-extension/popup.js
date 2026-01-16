/**
 * 弹窗页面脚本
 */

function openBoss() {
  chrome.tabs.create({ url: 'https://www.zhipin.com/web/geek/recommend' });
}

function openDocs() {
  alert('文档功能开发中...');
}

function openGithub() {
  chrome.tabs.create({ url: 'https://github.com' });
}

// 等待 DOM 加载完成后绑定事件
document.addEventListener('DOMContentLoaded', () => {
  // 绑定按钮点击事件
  const btnBoss = document.getElementById('btn-open-boss');
  const btnDocs = document.getElementById('btn-open-docs');
  const linkGithub = document.querySelector('.footer .link');
  
  if (btnBoss) {
    btnBoss.addEventListener('click', openBoss);
  }
  
  if (btnDocs) {
    btnDocs.addEventListener('click', openDocs);
  }
  
  if (linkGithub) {
    linkGithub.addEventListener('click', (e) => {
      e.preventDefault();
      openGithub();
    });
  }
});

