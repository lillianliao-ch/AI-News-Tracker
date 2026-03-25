---
name: browser-agent
description: 用 Playwright 挂载 Lilian 已有的 Chrome Profile，控制已登录的脉脉/小红书/LinkedIn 等平台。所有浏览器操作的基础层。
---

# Browser Agent Skill

## 核心原则

所有浏览器操作基于 **用户已有的 Chrome Profile**，不是无状态的新浏览器。
这意味着：账号已登录、插件已安装、Cookie 有效。

## 启动方式

```python
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = "/Users/lillianliao/Library/Application Support/Google/Chrome"

def get_browser():
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        executable_path=CHROME_PATH,
        headless=False,
        slow_mo=500,  # 模拟人类速度
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
        ]
    )
    return p, browser
```

## 反检测要点

- `slow_mo=500`：操作间加延迟，模拟人类
- 不用 `headless=True`（有头模式不容易被检测）
- user-agent 保持 Chrome 默认，不修改
- 操作前随机 sleep 1-3 秒

## 关闭方式

```python
browser.close()
p.stop()
```

## 注意事项

- 用此方式打开 Chrome 时，正常的 Chrome 窗口可能需要关闭（同一 Profile 不能多进程）
- 如果任务完成，立即关闭，不要长时间占用
- 截图留存：每个关键操作前后截图，方便调试
