# Shared Package

跨应用共享的工具和类型定义

## 包含内容

### Types
- 候选人类型
- 职位类型
- 评估结果类型
- API 响应类型

### Utils
- 日期处理
- 字符串处理
- 验证函数
- 格式化函数

### Constants
- 配置常量
- 枚举定义
- 错误代码

### Config
- 环境配置
- API 配置
- 功能开关

## 使用示例

```typescript
import { CandidateInfo, formatDate } from '@ai-headhunter/shared';

const candidate: CandidateInfo = {
  name: '张三',
  age: 30,
  // ...
};
```

## 开发计划

待从各应用中提取通用代码。

