# 猎头联盟网站

一个专为猎头企业设计的联盟平台，让联盟企业可以发布职位，其他成员单位可以浏览和搜索这些职位。

## 功能特点

### 🏢 企业功能
- **企业注册与登录**：安全的企业账户管理系统
- **职位发布**：完整的职位信息发布功能
- **职位管理**：查看、编辑、删除已发布的职位
- **企业信息管理**：维护企业基本信息和描述

### 🔍 职位搜索
- **多维度搜索**：按职位名称、企业名称、工作地点、工作类型筛选
- **分页浏览**：支持大量职位数据的分页显示
- **职位详情**：完整的职位信息展示页面
- **响应式设计**：支持桌面端和移动端访问

### 🎨 用户界面
- **现代化设计**：使用Bootstrap 5构建的现代化界面
- **响应式布局**：完美适配各种设备屏幕
- **直观导航**：清晰的导航结构和用户引导
- **美观动画**：流畅的页面过渡和交互效果

## 技术栈

- **后端框架**：Flask (Python)
- **数据库**：SQLite (可扩展至MySQL/PostgreSQL)
- **前端框架**：Bootstrap 5
- **图标库**：Font Awesome 6
- **认证系统**：Flask-Login
- **表单处理**：Flask-WTF

## 安装和运行

### 1. 环境要求
- Python 3.7+
- pip

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python app.py
```

### 4. 访问网站
打开浏览器访问：http://localhost:5000

## 数据库结构

### 用户表 (User)
- `id`: 主键
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `password_hash`: 密码哈希
- `company_name`: 企业名称
- `company_description`: 企业描述
- `is_admin`: 是否为管理员
- `created_at`: 创建时间

### 职位表 (Job)
- `id`: 主键
- `title`: 职位名称
- `company_name`: 企业名称
- `location`: 工作地点
- `salary_range`: 薪资范围
- `job_type`: 工作类型（全职/兼职/实习）
- `experience_level`: 经验要求
- `description`: 职位描述
- `requirements`: 职位要求
- `benefits`: 福利待遇
- `contact_email`: 联系邮箱
- `contact_phone`: 联系电话
- `posted_by`: 发布者ID
- `posted_at`: 发布时间
- `is_active`: 是否活跃

## 主要页面

### 1. 首页 (/)
- 英雄区域展示平台介绍
- 快速搜索功能
- 最新职位展示
- 联盟企业展示

### 2. 职位搜索页 (/jobs)
- 多维度筛选功能
- 分页浏览
- 网格/列表视图切换

### 3. 职位详情页 (/job/<id>)
- 完整职位信息
- 联系方式
- 快速操作按钮
- 相似职位推荐

### 4. 企业注册页 (/register)
- 企业信息注册
- 表单验证
- 用户友好的界面

### 5. 企业登录页 (/login)
- 安全的登录系统
- 记住登录状态

### 6. 管理面板 (/dashboard)
- 企业统计信息
- 职位管理
- 快速操作

### 7. 发布职位页 (/post-job)
- 完整的职位发布表单
- 实时验证
- 用户友好的界面

## API接口

### 职位搜索API
- **URL**: `/api/jobs`
- **方法**: GET
- **参数**: 
  - `company`: 企业名称筛选
  - `title`: 职位名称筛选
- **返回**: JSON格式的职位列表

## 部署建议

### 开发环境
- 使用SQLite数据库
- 开启调试模式
- 本地运行

### 生产环境
1. **数据库**: 使用MySQL或PostgreSQL
2. **Web服务器**: 使用Gunicorn + Nginx
3. **环境变量**: 设置SECRET_KEY等敏感信息
4. **HTTPS**: 配置SSL证书
5. **备份**: 定期备份数据库

### 环境变量配置
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## 安全考虑

1. **密码安全**: 使用Werkzeug进行密码哈希
2. **SQL注入防护**: 使用SQLAlchemy ORM
3. **XSS防护**: 模板自动转义
4. **CSRF防护**: 使用Flask-WTF
5. **会话安全**: 安全的会话配置

## 扩展功能建议

### 短期扩展
- [ ] 职位编辑功能
- [ ] 职位删除功能
- [ ] 企业信息编辑
- [ ] 密码重置功能
- [ ] 邮件通知系统

### 中期扩展
- [ ] 简历上传功能
- [ ] 职位申请系统
- [ ] 企业认证系统
- [ ] 数据统计报表
- [ ] 移动端APP

### 长期扩展
- [ ] 智能推荐系统
- [ ] 视频面试功能
- [ ] 在线聊天系统
- [ ] 多语言支持
- [ ] 第三方登录

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系开发团队。

---

**猎头联盟平台** - 连接优秀企业与顶尖人才的专业平台 