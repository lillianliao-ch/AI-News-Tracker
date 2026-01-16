# 飞书 API 集成指南 - 快速参考

> **适用场景**：需要快速集成飞书多维表格、文件上传等功能时查阅

---

## 🚀 快速开始（5分钟）

### 1. 获取凭证（飞书开放平台）

1. 访问 https://open.feishu.cn/
2. 创建企业自建应用
3. 获取凭证：
   ```
   App ID: cli_xxx
   App Secret: xxx
   ```

### 2. 配置权限

**必需权限**：
- ✅ `bitable:app` - 获取多维表格元数据
- ✅ `bitable:record:write` - 写入记录
- ✅ `drive:file:upload` - 上传文件

### 3. 添加协作者

1. 打开目标多维表格
2. 右上角「协作」→ 搜索 App ID
3. 授予「可编辑」权限

💡 **如果搜索不到**：开放平台 → 版本管理 → 可用范围 → 改为「所有员工」

### 4. 提取 URL 参数

```
URL: https://xxx.feishu.cn/base/QTRib6A1Ba6HmFs5lnhcMcp9nqr?table=tblFyH3r55WxzwVw

app_token = QTRib6A1Ba6HmFs5lnhcMcp9nqr  # base/ 后面
table_id = tblFyH3r55WxzwVw              # table= 参数
```

---

## 🔧 常见错误速查表

| 错误码/信息 | 原因 | 解决方案 |
|------------|------|----------|
| `403 Forbidden` | 权限不足 | 1. 检查应用权限<br>2. 添加为协作者 |
| `400 NOTEXIST` | app_token/table_id 错误 | 从 URL 重新提取参数 |
| `1061044 parent node not exist` | 文件上传 parent_node 错误 | 使用 `app_token` 作为 `parent_node` |
| `1254045 FieldNameNotFound` | 字段名不匹配 | 使用 `get_table_fields.py` 获取实际字段名 |
| `1254068 URLFieldConvFail` | Link 字段格式错误 | 使用 `{"link": "...", "text": "..."}` |

---

## 📝 字段类型对照表

| 飞书字段类型 | Python 值格式 | 示例 |
|-------------|--------------|------|
| 文本 | `str` | `"张三"` |
| 数字 | `int` / `float` | `42`, `3.14` |
| **百分比** | `float` (0-1) | `0.75` → 显示 75% |
| 日期时间 | `str` | `"2025-11-14 20:00:00"` |
| **Link** | `dict` | `{"link": "https://...", "text": "文本"}` |
| **附件** | `list[dict]` | `[{"file_token": "xxx", "type": "image"}]` |

⚠️ **易错点**：
- 百分比字段传整数会导致显示异常（75 → 7500%）
- Link 字段传字符串会报错 `URLFieldConvFail`
- 附件必须先上传获取 `file_token`

---

## 💻 核心代码模板

### Token 获取
```python
from lark_oapi import Client
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

request = InternalTenantAccessTokenRequest.builder() \
    .request_body(InternalTenantAccessTokenRequestBody.builder()
        .app_id(app_id)
        .app_secret(app_secret)
        .build()) \
    .build()

response = client.auth.v3.tenant_access_token.internal(request)
token = response.data.tenant_access_token
```

---

### 图片上传（多维表格）
```python
from lark_oapi.api.drive.v1 import UploadAllMediaRequest, UploadAllMediaRequestBody
from io import BytesIO
import base64

# 解码 Base64
image_data = base64.b64decode(image_base64)

# 包装为文件对象
file_obj = BytesIO(image_data)
file_obj.name = filename

# ✅ 关键：parent_node 必须是 app_token
request = UploadAllMediaRequest.builder() \
    .request_body(UploadAllMediaRequestBody.builder()
        .file_name(filename)
        .parent_type("bitable_image")
        .parent_node(app_token)  # ⚠️ 不能为空！
        .size(len(image_data))
        .file(file_obj)
        .build()) \
    .build()

response = client.drive.v1.media.upload_all(request)
file_token = response.data.file_token
```

---

### 创建记录
```python
from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

fields = {
    "姓名": "张三",
    "年龄": 30,
    "匹配度": 0.75,  # ✅ 百分比字段
    "数据来源": {     # ✅ Link 字段
        "link": "https://example.com",
        "text": "来源"
    },
    "简历截图": [{    # ✅ 附件字段
        "file_token": file_token,
        "type": "image",
        "name": "resume.png"
    }]
}

request = CreateAppTableRecordRequest.builder() \
    .app_token(app_token) \
    .table_id(table_id) \
    .request_body(AppTableRecord.builder()
        .fields(fields)
        .build()) \
    .build()

response = client.bitable.v1.app_table_record.create(request)
record_id = response.data.record.record_id
```

---

## 🐛 调试技巧

### 1. 开启 DEBUG 日志
```python
import lark_oapi as lark

client = lark.Client.builder() \
    .log_level(lark.LogLevel.DEBUG) \  # ✅ 查看完整请求
    .build()
```

### 2. 错误处理模板
```python
if not response.success():
    logger.error(
        f"操作失败: code={response.code}, "
        f"msg={response.msg}, "
        f"log_id={response.get_log_id()}"  # ⚠️ 联系技术支持时需要
    )
    return None
```

### 3. 获取字段信息（调试用）
```python
from lark_oapi.api.bitable.v1 import ListAppTableFieldRequest

request = ListAppTableFieldRequest.builder() \
    .app_token(app_token) \
    .table_id(table_id) \
    .build()

response = client.bitable.v1.app_table_field.list(request)

for field in response.data.items:
    print(f"字段: {field.field_name} ({field.type})")
```

---

## 📚 最佳实践

### ✅ DO

1. **分步验证**
   ```
   Token 获取 → 字段查询 → 简单写入 → 完整流程
   ```

2. **详细日志**
   ```python
   logger.info(f"📸 收到数据: {len(data)} 字符")
   logger.info(f"✅ 成功: {result}")
   logger.error(f"❌ 失败: {error}")
   ```

3. **错误重试**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential())
   async def upload_with_retry():
       ...
   ```

### ❌ DON'T

1. ❌ 硬编码字段名（使用 API 查询实际字段）
2. ❌ 忽略 SDK 错误信息（`response.msg` 很重要）
3. ❌ 直接传递字节数据给文件上传（使用 `BytesIO`）
4. ❌ 百分比字段传整数（75 → 7500%）

---

## 🔗 快速链接

- **开放平台**: https://open.feishu.cn/
- **API 文档**: https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-record
- **SDK 仓库**: https://github.com/larksuite/oapi-sdk-python
- **错误码**: https://open.feishu.cn/document/server-docs/api-call-guide/error-code

---

## ⚡ 常用命令

```bash
# 安装 SDK
pip install lark-oapi>=1.2.0

# 测试连接
python3 test_feishu.py

# 查看字段
python3 get_table_fields.py

# 测试写入
python3 test_simple_write.py
```

---

**最后更新**: 2025-11-14  
**项目**: AI Headhunter Assistant


