/**
 * Popup 脚本 - Excel 上传与解析
 */

let jobsData = [];

document.addEventListener('DOMContentLoaded', () => {
  const uploadArea = document.getElementById('uploadArea');
  const fileInput = document.getElementById('fileInput');
  const fileInfo = document.getElementById('fileInfo');
  const jobPreview = document.getElementById('jobPreview');
  const jobList = document.getElementById('jobList');
  const startBtn = document.getElementById('startBtn');
  const status = document.getElementById('status');
  
  // 点击上传区域触发文件选择
  uploadArea.addEventListener('click', () => {
    fileInput.click();
  });
  
  // 文件选择后解析
  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
      status.textContent = '正在解析 Excel...';
      status.className = 'status';
      
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(firstSheet);
      
      jobsData = rows.map((row, index) => ({
        index: index + 1,
        name: row['职位名称'] || '',
        city: row['工作城市'] || '',
        education: row['学历'] || '',
        workYears: row['工作年限'] || '',
        salaryMin: row['月薪下限'] || 0,
        salaryMax: row['月薪上限'] || 0,
        description: row['职位描述'] || '',
        requirements: row['岗位要求'] || '',
        keywords: row['Boss关键词'] || '[]',
        jobType: row['职位类型（子类）'] || '',
        salaryMonths: row['发薪月数'] || row['发薪月份'] || row['薪资发放'] || '',
        department: row['业务线-部门'] || row['业务线'] || row['部门'] || '',
        recruitmentType: row['招聘类型'] || row['招聘方式'] || '',
        headcount: row['招聘人数'] || row['需求人数'] || '',
        highlights: row['职位亮点'] || row['职位诱惑'] || row['职位优势'] || ''
      }));
      
      // 显示文件信息
      fileInfo.textContent = `✅ 已加载 ${jobsData.length} 个职位`;
      uploadArea.classList.add('has-file');
      
      // 显示职位预览
      jobPreview.style.display = 'block';
      jobList.innerHTML = jobsData.map(job => `
        <div class="job-item">
          <span>${job.index}. ${job.name}</span>
          <span style="color: #6b7280; font-size: 12px;">${job.city.split(',')[0]?.split('-').pop() || job.city}</span>
        </div>
      `).join('');
      
      // 启用开始按钮
      startBtn.disabled = false;
      status.textContent = `已加载 ${jobsData.length} 个职位，可以开始发布`;
      status.className = 'status success';
      
    } catch (error) {
      status.textContent = `解析失败: ${error.message}`;
      status.className = 'status error';
      console.error('Excel 解析错误:', error);
    }
  });
  
  // 开始发布
  startBtn.addEventListener('click', async () => {
    if (jobsData.length === 0) {
      alert('请先上传 Excel 文件');
      return;
    }
    
    // 发送数据到 content script
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('zhipin.com/web/chat/job/edit')) {
      alert('请先打开 Boss 直聘的职位发布页面！');
      return;
    }
    
    chrome.tabs.sendMessage(tab.id, {
      action: 'startPublish',
      jobs: jobsData
    }, (response) => {
      if (chrome.runtime.lastError) {
        status.textContent = '发送失败，请刷新页面后重试';
        status.className = 'status error';
      } else {
        status.textContent = '正在发布中，请查看页面日志...';
        status.className = 'status';
        startBtn.disabled = true;
      }
    });
  });
});

