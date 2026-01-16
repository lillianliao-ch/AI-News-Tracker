# 全局配置

## 配置文件

- `tsconfig.base.json` - TypeScript 基础配置
- `eslint.config.js` - ESLint 配置（待添加）

## 使用

各个包和应用继承这些基础配置。

```json
// apps/web/tsconfig.json
{
  "extends": "../../config/tsconfig.base.json",
  "compilerOptions": {
    // 应用特定配置
  }
}
```

