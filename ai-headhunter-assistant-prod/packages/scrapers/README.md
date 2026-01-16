# Scrapers Package

多平台爬虫模块

## 支持平台

- ✅ Boss 直聘
- ⏳ 猎聘
- ⏳ LinkedIn
- ⏳ 脉脉

## 使用示例

```typescript
import { BossScraper } from '@ai-headhunter/scrapers';

const scraper = new BossScraper();
const candidates = await scraper.getCandidates({
  count: 10,
  position: 'AI工程师'
});
```

## 架构

- `base/`: 基础爬虫类
- `boss/`: Boss 直聘实现
- `liepin/`: 猎聘实现
- `linkedin/`: LinkedIn 实现

## 开发计划

待从 `chrome-extension-v2/content-full.js` 提取和重构。

