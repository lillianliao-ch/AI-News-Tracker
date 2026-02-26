// 为每个生成按钮添加点击事件
document.addEventListener('astro:page-load', () => {
    const generateButtons = document.querySelectorAll('.generate-btn');
    generateButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const newsId = e.target.dataset.newsId;
            if (!newsId) {
                alert('新闻 ID 不存在');
                return;
            }

            // 防止重复点击
            if (e.target.disabled) {
                return;
            }

            const resultDiv = document.getElementById(`result-${newsId}`);
            const resultContent = document.getElementById(`result-content-${newsId}`);

            // 显示加载状态
            const originalText = e.target.textContent;
            e.target.textContent = '⏳ 生成中...';
            e.target.disabled = true;
            e.target.style.cursor = 'not-allowed';
            e.target.style.opacity = '0.6';

            if (resultDiv) {
                resultDiv.style.display = 'block';
                if (resultContent) {
                    resultContent.innerHTML = `
            <div style="text-align: center; padding: 20px;">
              <div style="color: #667eea; font-size: 14px; margin-bottom: 8px;">
                ⏳ 正在调用 AI 生成文案...
              </div>
              <div style="color: #999; font-size: 12px;">
                这可能需要 10-30 秒，请耐心等待
              </div>
              <div style="margin-top: 12px;">
                <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
              </div>
            </div>
            <style>
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            </style>
          `;
                }
            }

            try {
                // Use implicit relative URL or configured base
                // In local dev it is localhost:8502. In prod it is same host or configured.
                // But NewsCard.astro uses absolute URL in fetch: http://localhost:8502/api/generate
                // We should use PUBLIC_API_URL here too.

                const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8502';

                const response = await fetch(`${API_URL}/api/generate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        news_id: newsId,
                        versions: ['A', 'B', 'C']
                    })
                });

                if (response.ok) {
                    const results = await response.json();
                    if (results && results.length > 0) {
                        // 显示所有版本
                        let html = '';
                        results.forEach((result, index) => {
                            const versionNames = { 'A': '硬核技术风', 'B': '轻松科普风', 'C': '热点观点风' };
                            html += `
                <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #ddd;">
                  <div class="title">版本 ${result.version} - ${versionNames[result.version]}</div>
                  <div class="content">${result.content}</div>
                  <div class="hashtags">${result.hashtags ? result.hashtags.join(' ') : ''}</div>
                </div>
              `;
                        });
                        if (resultContent) {
                            resultContent.innerHTML = html;
                        }

                        // 成功提示
                        e.target.textContent = '✅ 生成成功';
                        setTimeout(() => {
                            e.target.textContent = originalText;
                            e.target.disabled = false;
                            e.target.style.cursor = 'pointer';
                            e.target.style.opacity = '1';
                        }, 2000);
                    } else {
                        if (resultContent) {
                            resultContent.innerHTML = '<p style="color: #dc3545;">❌ 生成失败：未返回内容</p>';
                        }
                        e.target.textContent = originalText;
                        e.target.disabled = false;
                        e.target.style.cursor = 'pointer';
                        e.target.style.opacity = '1';
                    }
                } else {
                    const error = await response.json();
                    if (resultContent) {
                        resultContent.innerHTML = `<p style="color: #dc3545;">❌ 生成失败：${error.detail || '未知错误'}</p>`;
                    }
                    e.target.textContent = originalText;
                    e.target.disabled = false;
                    e.target.style.cursor = 'pointer';
                    e.target.style.opacity = '1';
                }
            } catch (error) {
                console.error('生成错误:', error);
                if (resultContent) {
                    resultContent.innerHTML = `<p style="color: #dc3545;">❌ 生成失败：${error.message}</p>`;
                }
                e.target.textContent = originalText;
                e.target.disabled = false;
                e.target.style.cursor = 'pointer';
                e.target.style.opacity = '1';
            }
        });
    });

    // 复制按钮事件
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = e.target.dataset.target;
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                const text = targetElement.innerText || targetElement.textContent;

                // 使用 Clipboard API
                navigator.clipboard.writeText(text).then(() => {
                    const originalText = e.target.textContent;
                    e.target.textContent = '✅ 已复制';
                    e.target.classList.add('copied');

                    setTimeout(() => {
                        e.target.textContent = originalText;
                        e.target.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('复制失败:', err);
                    alert('复制失败，请手动复制');
                });
            }
        });
    });
});
