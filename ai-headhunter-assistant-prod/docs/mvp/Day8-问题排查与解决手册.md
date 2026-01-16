# Day 8 - 飞书集成问题排查与解决手册

> **目标**：记录飞书集成过程中遇到的所有问题、排查思路和解决方案，为后续类似项目提供参考。

---

## 📋 目录

1. [简历截图缺失问题](#1-简历截图缺失问题)
2. [数据来源字段缺失](#2-数据来源字段缺失)
3. [匹配度超过100%显示异常](#3-匹配度超过100显示异常)
4. [飞书API常见错误速查](#4-飞书api常见错误速查)

---

## 1. 简历截图缺失问题

### 问题现象
- 飞书多维表格中「简历截图」字段为空
- 其他字段（姓名、匹配度等）正常显示
- 前端插件已成功截图并导出为 PNG 文件

### 排查过程

#### 第一步：确认数据流向
```bash
# 查看后端日志，检查是否收到截图数据
cd /Users/lillianliao/notion_rag/ai-headhunter-assistant/apps/backend
tail -50 backend.log | grep -E "截图|screenshot"
```

**发现问题 1**：日志显示 `⚠️ 未收到截图数据`

#### 第二步：检查前端传递逻辑
```javascript
// apps/extension/content-full.js

// ❌ 错误代码
async processCandidate(candidateInfo, resumeText, jdConfig, resumeBase64 = 'mock_data') {
  const response = await fetch(`${this.baseURL}/api/candidates/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      candidate_info: candidateInfo,
      resume_file: resumeBase64,
      resume_text: resumeText,
      jd_config: jdConfig
      // ❌ 缺少 resume_screenshot 字段！
    })
  });
}
```

**根本原因**：前端 API 调用未传递 `resume_screenshot` 参数。

#### 第三步：修复前端传递
```javascript
// ✅ 正确代码
async processCandidate(candidateInfo, resumeText, jdConfig, resumeBase64 = 'mock_data', resumeScreenshot = null) {
  const requestBody = {
    candidate_info: candidateInfo,
    resume_file: resumeBase64,
    resume_text: resumeText,
    jd_config: jdConfig
  };
  
  // ✅ 添加截图（如果有）
  if (resumeScreenshot) {
    requestBody.resume_screenshot = resumeScreenshot;
  }
  
  const response = await fetch(`${this.baseURL}/api/candidates/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  });
}

// ✅ 调用时传递截图
const reParseResult = await this.api.processCandidate(
  candidateInfo,
  resumeText,
  CONFIG.DEFAULT_JD,
  'mock_data',      // resume_file
  screenshot        // resume_screenshot - 传递截图！
);
```

#### 第四步：确认后端接收
```bash
# 重新测试后查看日志
tail -50 backend.log | grep -E "截图|screenshot|📸"
```

**结果**：`📸 收到截图数据: 1154398 字符` ✅ 数据传递成功！

---

#### 第五步：飞书图片上传失败

**发现问题 2**：日志显示 `❌ 截图上传失败，但继续添加记录`

```bash
# 查看详细错误
tail -100 backend.log | grep -A 3 "上传图片"
```

**错误信息**：
```
上传图片失败: code=1061044, msg=parent node not exist., log_id=None
```

**原因分析**：飞书 API 的 `parent_node` 参数配置错误。

#### 第六步：修复 parent_node 参数

```python
# apps/backend/app/services/feishu_client.py

# ❌ 错误代码
request = UploadAllMediaRequest.builder() \
    .request_body(UploadAllMediaRequestBody.builder()
        .file_name(filename)
        .parent_type("bitable_image")
        .parent_node("")  # ❌ 空字符串导致 "parent node not exist"
        .size(len(image_data))
        .file(image_data)
        .build()) \
    .build()
```

```python
# ✅ 正确代码
# 获取 app_token（多维表格的 parent_node）
app_token = self.config["app_token"]

request = UploadAllMediaRequest.builder() \
    .request_body(UploadAllMediaRequestBody.builder()
        .file_name(filename)
        .parent_type("bitable_image")
        .parent_node(app_token)  # ✅ 使用 app_token 作为 parent_node
        .size(len(image_data))
        .file(BytesIO(image_data))  # ✅ 使用 BytesIO 包装
        .build()) \
    .build()
```

### 解决方案总结

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 后端未收到截图 | 前端未传递 `resume_screenshot` 参数 | 在 `processCandidate` 函数添加 `resumeScreenshot` 参数并传递 |
| 飞书上传失败 `1061044` | `parent_node` 为空字符串 | 使用 `app_token` 作为 `parent_node` |
| 文件对象格式 | 直接传递字节数据 | 使用 `BytesIO` 包装为文件对象 |

### 关键代码位置

- **前端传递**：`apps/extension/content-full.js` 第 73-91 行
- **后端接收**：`apps/backend/app/main.py` 第 276-340 行
- **飞书上传**：`apps/backend/app/services/feishu_client.py` 第 137-189 行

---

## 2. 数据来源字段缺失

### 问题现象
- 飞书多维表格中「数据来源」字段为空
- 预期显示为指向 Boss 直聘的链接

### 排查过程

```bash
# 查看飞书上传的数据
tail -100 backend.log | grep "数据来源"
```

**发现**：`source_url` 为空字符串。

### 根本原因

```python
# apps/backend/app/main.py

# ❌ 错误代码
candidate_data = {
    # ...
    "source_url": "",  # ❌ 硬编码为空字符串
}
```

前端传递了 `candidate_info.source_url`，但后端未使用，而是硬编码为空字符串。

### 解决方案

```python
# ✅ 正确代码
candidate_data = {
    # ...
    "source_url": request.candidate_info.source_url or "https://www.zhipin.com/web/chat/recommend",
    # ✅ 使用前端传递的值，或使用默认 URL
}
```

### 飞书 Link 字段格式要求

飞书的 Link 类型字段需要特定格式：

```python
# ❌ 错误格式（纯字符串）
fields["数据来源"] = "https://www.zhipin.com/web/chat/recommend"
# 报错: 1254068 - URLFieldConvFail

# ✅ 正确格式（Link 对象）
fields["数据来源"] = {
    "link": "https://www.zhipin.com/web/chat/recommend",
    "text": "Boss直聘"
}
```

### 关键代码位置

- **前端传递**：`apps/extension/content-full.js` 第 628 行（`source_url: window.location.href`）
- **后端使用**：`apps/backend/app/main.py` 第 313 行
- **飞书字段**：`apps/backend/app/services/feishu_client.py` 第 260-263 行

---

## 3. 匹配度超过100%显示异常

### 问题现象
- 飞书多维表格显示匹配度为 **7700%**
- 预期显示为 **77%**

### 排查过程

#### 第一步：确认后端数据
```python
# apps/backend/app/main.py

# 后端已经限制在 0-100
"match_score": min(parsed["evaluation"].get("综合匹配度", 0), 100)
```

后端传递的是 `75`（整数）。

#### 第二步：理解飞书字段类型

**根本原因**：飞书表格中的「匹配度」字段类型为**百分比**。

- 飞书百分比字段期望接收 **小数值**（0-1）
- 传入 `75` 时，飞书自动乘以 100 → 显示为 **7500%**
- 传入 `0.75` 时，飞书自动乘以 100 → 显示为 **75%** ✅

### 解决方案

```python
# apps/backend/app/services/feishu_client.py

# ❌ 错误代码
fields = {
    "匹配度": candidate_data.get("match_score", 0),  # 75 → 7500%
}

# ✅ 正确代码
fields = {
    "匹配度": candidate_data.get("match_score", 0) / 100,  # 75 / 100 = 0.75 → 75%
}
```

### 飞书字段类型处理规则

| 飞书字段类型 | 期望值格式 | 示例 |
|--------------|-----------|------|
| 文本 | 字符串 | `"张三"` |
| 数字 | 整数或小数 | `42`, `3.14` |
| 百分比 | 小数（0-1） | `0.75` → 显示为 75% |
| 日期时间 | 字符串 | `"2025-11-14 20:00:00"` |
| Link | 对象 | `{"link": "url", "text": "文本"}` |
| 附件 | 对象数组 | `[{"file_token": "xxx", "type": "image"}]` |

### 关键代码位置

- **匹配度计算**：`apps/backend/app/main.py` 第 221 行
- **飞书字段转换**：`apps/backend/app/services/feishu_client.py` 第 251 行

---

## 4. 飞书API常见错误速查

### 4.1 认证与权限错误

#### `403 Forbidden`
**原因**：应用权限不足或未添加为协作者。

**排查步骤**：
1. **应用级权限**：飞书开放平台 → 权限管理 → 确认已开通
   - `bitable:app` - 获取多维表格元数据
   - `bitable:record` - 读取多维表格记录
   - `bitable:record:write` - 写入多维表格记录
   - `drive:file:upload` - 上传文件到云盘

2. **资源级权限**：直接在飞书表格中添加应用为协作者
   - 打开多维表格 → 右上角「协作」
   - 搜索 App ID（如 `cli_a99c635ace69501c`）
   - 授予「可编辑」权限

**解决方案**：
```bash
# 如果搜索不到 App ID，需要修改应用可用范围
# 飞书开放平台 → 版本管理与发布 → 可用性状态 → 设为「所有员工」
```

---

#### `400 - NOTEXIST`
**原因**：`app_token` 或 `table_id` 错误。

**排查步骤**：
```python
# 从飞书表格 URL 提取正确的 app_token 和 table_id
# URL: https://qqvh73w8uz.feishu.cn/base/QTRib6A1Ba6HmFs5lnhcMcp9nqr?table=tblFyH3r55WxzwVw&view=vewzgGuZEI
#                                      ^^^^^^^^^^^^^^^^^^^^^^^^         ^^^^^^^^^^^^^^^^
#                                      app_token                        table_id

FEISHU_APP_TOKEN=QTRib6A1Ba6HmFs5lnhcMcp9nqr  # ✅ base/ 后面的部分
FEISHU_TABLE_ID=tblFyH3r55WxzwVw             # ✅ table= 参数的值
```

**注意**：Wiki 表格 URL 格式不同，需使用独立的多维表格。

---

#### `1254045 - FieldNameNotFound`
**原因**：字段名称不匹配。

**排查步骤**：
```python
# 使用工具脚本获取实际字段名
# apps/backend/get_table_fields.py

# 输出示例：
# 字段: 文本 (text)
# 字段: 姓名 (text)
# 字段: 匹配度 (number)
```

**解决方案**：使用实际字段名，而非假设的名称。

---

#### `1061044 - parent node not exist`
**原因**：文件上传时 `parent_node` 参数错误。

**解决方案**：
```python
# ✅ 对于多维表格图片上传
request = UploadAllMediaRequest.builder() \
    .request_body(UploadAllMediaRequestBody.builder()
        .parent_type("bitable_image")
        .parent_node(app_token)  # ✅ 必须使用 app_token
        .build())
```

---

#### `1254068 - URLFieldConvFail`
**原因**：Link 字段格式错误。

**解决方案**：
```python
# ❌ 错误
fields["数据来源"] = "https://example.com"

# ✅ 正确
fields["数据来源"] = {
    "link": "https://example.com",
    "text": "显示文本"
}
```

---

### 4.2 调试技巧

#### 开启详细日志
```python
# apps/backend/app/services/feishu_client.py

self.client = lark.Client.builder() \
    .app_id(self.config["app_id"]) \
    .app_secret(self.config["app_secret"]) \
    .log_level(lark.LogLevel.DEBUG) \  # ✅ 开启 DEBUG 日志
    .build()
```

#### 查看飞书 API 请求详情
```bash
# 查看完整的 HTTP 请求和响应
tail -200 backend.log | grep -E "\[Lark\]|POST|headers|body"
```

#### 手动测试 API
```python
# apps/backend/test_manual_request.py
# 直接发送 HTTP 请求，绕过 SDK，用于诊断问题
```

---

### 4.3 最佳实践

1. **分步验证**
   ```bash
   # 1. 验证 Token 获取
   python3 apps/backend/test_feishu.py
   
   # 2. 验证字段获取
   python3 apps/backend/get_table_fields.py
   
   # 3. 验证记录写入
   python3 apps/backend/test_simple_write.py
   
   # 4. 验证完整流程
   # 使用 Chrome 插件测试
   ```

2. **错误处理**
   ```python
   # 所有飞书 API 调用都应包含错误处理
   if not response.success():
       logger.error(
           f"操作失败: code={response.code}, msg={response.msg}, "
           f"log_id={response.get_log_id()}"  # ✅ log_id 用于联系技术支持
       )
   ```

3. **环境变量管理**
   ```bash
   # .env 文件（实际值）
   FEISHU_APP_ID=cli_xxx
   FEISHU_APP_SECRET=xxx
   FEISHU_APP_TOKEN=QTRib6A1Ba6HmFs5lnhcMcp9nqr
   FEISHU_TABLE_ID=tblFyH3r55WxzwVw
   FEISHU_ENABLED=true
   
   # env.example（模板）
   FEISHU_APP_ID=your_app_id_here
   FEISHU_APP_SECRET=your_app_secret_here
   ```

---

## 5. 完整问题解决时间线

| 时间 | 问题 | 解决方案 | 耗时 |
|------|------|----------|------|
| 20:00 | 数据写入飞书成功，但截图缺失 | 检查前端是否传递截图数据 | - |
| 20:10 | 发现后端未收到截图 | 修改前端 `processCandidate` 函数，添加 `resumeScreenshot` 参数 | 10min |
| 20:20 | 后端收到截图，但飞书上传失败 | 修改 `parent_node` 为 `app_token`，使用 `BytesIO` 包装 | 10min |
| 20:30 | 截图上传成功！但数据来源为空 | 修改后端使用 `request.candidate_info.source_url` | 5min |
| 20:35 | 数据来源仍为空（格式错误） | 修改为 Link 对象格式 `{"link": "...", "text": "..."}` | 5min |
| 20:40 | 匹配度显示为 7700% | 除以 100 转换为小数（飞书百分比字段） | 5min |
| 20:45 | ✅ 所有问题解决！ | - | **总计 35min** |

---

## 6. 核心 Know-How 总结

### 6.1 飞书 API 集成要点

1. **权限配置是双层的**
   - 应用级权限（开放平台配置）
   - 资源级权限（表格协作者）

2. **字段类型必须严格匹配**
   - 百分比 → 小数（0-1）
   - Link → 对象（`{"link": "...", "text": "..."}`）
   - 附件 → 对象数组（`[{"file_token": "...", "type": "image"}]`）

3. **文件上传参数**
   - `parent_type`: `"bitable_image"`
   - `parent_node`: 必须是 `app_token`
   - `file`: 使用 `BytesIO` 包装字节数据

4. **错误排查优先级**
   - Token 获取 → 字段名称 → 字段格式 → 权限检查

---

### 6.2 前后端数据传递要点

1. **前端 → 后端**
   ```javascript
   // ✅ 确保所有必需字段都传递
   const requestBody = {
       candidate_info: {...},  // 基本信息
       resume_text: "...",     // 简历文本
       resume_screenshot: "data:image/png;base64,..."  // Base64 截图
   };
   ```

2. **后端 → 飞书**
   ```python
   # ✅ 按照飞书字段类型转换
   fields = {
       "匹配度": score / 100,           # 百分比
       "数据来源": {"link": "...", "text": "..."},  # Link
       "简历截图": [{"file_token": "...", "type": "image"}]  # 附件
   }
   ```

---

### 6.3 调试技巧

1. **日志驱动排查**
   ```bash
   # 添加详细日志
   logger.info(f"📸 收到截图数据: {len(screenshot)} 字符")
   logger.info(f"✅ 上传成功: {file_token}")
   logger.error(f"❌ 失败: code={code}, msg={msg}")
   ```

2. **分段验证**
   - 前端 → 后端（检查 API 请求）
   - 后端 → 飞书（检查飞书 API 响应）
   - 逐步缩小问题范围

3. **使用测试脚本**
   - 绕过完整流程，单独测试问题模块
   - 快速迭代验证

---

## 7. 参考资源

- **飞书开放平台文档**: https://open.feishu.cn/document
- **多维表格 API**: https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-record
- **文件上传 API**: https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
- **错误码查询**: https://open.feishu.cn/document/server-docs/api-call-guide/error-code

---

## 8. 未来优化方向

1. **错误重试机制**
   - 飞书 API 调用失败时自动重试 3 次
   - 指数退避策略

2. **批量上传优化**
   - 多个候选人的截图批量上传
   - 减少 API 调用次数

3. **数据校验**
   - 在前端和后端都做数据完整性校验
   - 避免传递空值或格式错误的数据

4. **监控告警**
   - 集成日志监控（如 Sentry）
   - 关键错误自动告警

---

**文档创建时间**: 2025-11-14  
**最后更新**: 2025-11-14  
**作者**: AI Assistant + Lillian  
**项目**: AI Headhunter Assistant - MVP Phase


