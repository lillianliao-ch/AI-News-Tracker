// 脉脉招聘助手 - Popup Script

document.addEventListener('DOMContentLoaded', function() {
    
    // 检查插件状态
    checkPluginStatus();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 更新统计信息
    updateStatistics();
});

// 检查插件状态
function checkPluginStatus() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const currentTab = tabs[0];
        const statusElement = document.getElementById('plugin-status');
        
        if (currentTab.url && currentTab.url.includes('maimai.cn')) {
            statusElement.innerHTML = `
                <div class="status-dot status-online"></div>
                <span>插件已激活</span>
            `;
        } else {
            statusElement.innerHTML = `
                <div class="status-dot status-offline"></div>
                <span>未在脉脉网站</span>
            `;
        }
    });
}

// 绑定事件监听器
function bindEventListeners() {
    // 访问脉脉招聘按钮
    document.getElementById('open-maimai').addEventListener('click', function() {
        chrome.tabs.create({
            url: 'https://maimai.cn/ent/v41/recruit/talents'
        });
        window.close();
    });
    
    // 查看帮助按钮
    document.getElementById('view-help').addEventListener('click', function() {
        showHelp();
    });
    
    // 关于插件链接
    document.getElementById('about-link').addEventListener('click', function(e) {
        e.preventDefault();
        showAbout();
    });
}

// 更新统计信息
function updateStatistics() {
    chrome.storage.local.get(['talentData'], function(result) {
        const data = result.talentData || [];
        const count = data.length;
        
        // 可以在这里添加统计信息显示
        console.log(`已保存 ${count} 条人才数据`);
    });
}

// 显示帮助信息
function showHelp() {
    const helpWindow = window.open('', '_blank', 'width=600,height=400');
    helpWindow.document.write(`
        <html>
        <head>
            <title>脉脉招聘助手 - 使用帮助</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 20px; 
                    line-height: 1.6;
                }
                h1 { color: #1890ff; }
                .step { 
                    background: #f8f9fa; 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <h1>脉脉招聘助手 - 使用帮助</h1>
            
            <h3>安装说明：</h3>
            <div class="step">
                1. 下载插件文件<br>
                2. 打开Chrome扩展管理页面<br>
                3. 开启"开发者模式"<br>
                4. 点击"加载已解压的扩展程序"<br>
                5. 选择插件文件夹
            </div>
            
            <h3>使用步骤：</h3>
            <div class="step">
                1. 访问脉脉招聘页面 (maimai.cn)<br>
                2. 在人才详情页面查看左下角蓝色控制面板<br>
                3. 点击"提取当前人才"按钮<br>
                4. 查看提取的信息预览<br>
                5. 添加备注信息<br>
                6. 点击"保存数据"<br>
                7. 可随时点击"导出Excel"导出所有数据
            </div>
            
            <h3>注意事项：</h3>
            <div class="step">
                • 请确保网络连接正常<br>
                • 插件仅在脉脉网站有效<br>
                • 数据保存在本地浏览器中<br>
                • 请合理使用，遵守网站服务条款
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                <button onclick="window.close()" style="padding: 10px 20px; background: #1890ff; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    关闭
                </button>
            </p>
        </body>
        </html>
    `);
}

// 显示关于信息
function showAbout() {
    const aboutWindow = window.open('', '_blank', 'width=500,height=350');
    aboutWindow.document.write(`
        <html>
        <head>
            <title>关于脉脉招聘助手</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 30px; 
                    text-align: center;
                    line-height: 1.6;
                }
                h1 { color: #1890ff; margin-bottom: 30px; }
                .info { 
                    background: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1>脉脉招聘助手</h1>
            
            <div class="info">
                <h3>版本信息</h3>
                <p>版本号：v1.0.0<br>
                发布日期：2024-12-21<br>
                适用浏览器：Chrome 88+</p>
            </div>
            
            <div class="info">
                <h3>功能特性</h3>
                <p>• 自动提取脉脉人才信息<br>
                • 支持批量数据处理<br>
                • Excel格式导出<br>
                • 本地数据存储</p>
            </div>
            
            <div class="info">
                <h3>免责声明</h3>
                <p style="font-size: 12px; color: #666;">
                    本工具仅供学习和研究使用。<br>
                    请遵守相关法律法规和网站服务条款。<br>
                    开发者不对使用后果承担责任。
                </p>
            </div>
            
            <p>
                <button onclick="window.close()" style="padding: 10px 20px; background: #1890ff; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    关闭
                </button>
            </p>
        </body>
        </html>
    `);
}