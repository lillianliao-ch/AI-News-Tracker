# AI Pipeline

AI 处理流程的共享包

## 功能模块

### Parsers (解析器)
- PDF 解析
- 简历结构化
- 信息提取

### Evaluators (评估器)
- 匹配度评估
- 技能评分
- 推荐等级计算

### Generators (生成器)
- 招呼语生成
- 标签生成
- 摘要生成

## 使用示例

```typescript
import { ResumeParser, Evaluator } from '@ai-headhunter/ai-pipeline';

const parser = new ResumeParser();
const resume = await parser.parse(pdfBuffer);

const evaluator = new Evaluator();
const score = await evaluator.evaluate(resume, jobDescription);
```

## 开发计划

待从 `backend/app/services/` 提取和重构。

