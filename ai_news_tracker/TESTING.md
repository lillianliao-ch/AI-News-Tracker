# 测试指南 - AI News Tracker

本文档提供 AI News Tracker 系统的完整测试指南，包括单元测试、集成测试、API 测试和手动测试。

## 📋 目录

- [测试环境准备](#测试环境准备)
- [后端测试](#后端测试)
- [前端测试](#前端测试)
- [API 测试](#api-测试)
- [集成测试](#集成测试)
- [性能测试](#性能测试)

---

## 测试环境准备

### 1. 安装测试依赖

**后端测试依赖:**

```bash
cd backend

# 安装测试框架
pip install pytest pytest-asyncio pytest-cov httpx

# 安装覆盖率工具
pip install coverage
```

**前端测试依赖:**

```bash
cd frontend

# 安装测试框架
npm install --save-dev vitest @vitest/ui jsdom
```

### 2. 配置测试环境

创建 `backend/tests/__init__.py`:

```python
# 测试配置
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试数据库
os.environ['DATABASE_URL'] = 'sqlite:///./test_data/test.db'
os.environ['LOG_LEVEL'] = 'DEBUG'
```

---

## 后端测试

### 1. 单元测试

#### 测试 AI 服务

创建 `backend/tests/test_ai_service.py`:

```python
"""
AI 服务单元测试
"""
import pytest
from services.ai_service import AIService
from config.base_config import settings

@pytest.fixture
def ai_service():
    """创建 AI 服务实例"""
    # 使用测试环境变量
    return AIService()

@pytest.mark.asyncio
async def test_classify_news(ai_service):
    """测试资讯分类"""
    news = {
        'title': 'OpenAI 发布 GPT-5 模型',
        'summary': 'OpenAI 宣布推出新一代大语言模型 GPT-5'
    }

    result = await ai_service.classify_news(news)

    assert 'category' in result
    assert result['category'] in ['product', 'model', 'investment', 'view', 'research', 'application']
    assert 'confidence' in result
    assert 0 <= result['confidence'] <= 1

@pytest.mark.asyncio
async def test_generate_summary(ai_service):
    """测试摘要生成"""
    news = {
        'title': 'AI 技术突破',
        'summary': '这是一个很长的摘要内容，超过200字...' * 10
    }

    summary = await ai_service.generate_summary(news)

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) <= 300  # 摘要长度限制

@pytest.mark.asyncio
async def test_generate_xiaohongshu_content(ai_service):
    """测试小红书内容生成"""
    news = {
        'title': '测试新闻标题',
        'summary': '这是一个测试新闻的摘要内容',
        'content': '这是详细的新闻内容',
        'url': 'https://example.com/news/123'
    }

    # 测试版本 A
    result_a = await ai_service.generate_xiaohongshu_content(news, 'A')
    assert 'title' in result_a
    assert 'content' in result_a
    assert 'hashtags' in result_a
    assert len(result_a['hashtags']) > 0

    # 测试版本 B
    result_b = await ai_service.generate_xiaohongshu_content(news, 'B')
    assert result_b['version'] == 'B'

    # 测试版本 C
    result_c = await ai_service.generate_xiaohongshu_content(news, 'C')
    assert result_c['version'] == 'C'
```

#### 测试数据源

创建 `backend/tests/test_sources.py`:

```python
"""
数据源单元测试
"""
import pytest
from sources.base import SourceFactory, RSSSource
from config.base_config import SOURCES_CONFIG

@pytest.mark.asyncio
async def test_source_factory():
    """测试数据源工厂"""
    sources = SourceFactory.create_all_sources(SOURCES_CONFIG)

    assert len(sources) > 0
    assert all(hasattr(s, 'get_data') for s in sources)
    assert all(hasattr(s, 'normalize') for s in sources)

@pytest.mark.asyncio
async def test_rss_source():
    """测试 RSS 数据源"""
    # 使用 36氪作为测试
    config = {
        'id': '36kr',
        'name': '36氪',
        'enabled': True,
        'type': 'rss',
        'url': 'https://36kr.com/feed',
        'icon': ''
    }

    source = RSSSource(config)
    items = await source.get_data()

    assert len(items) > 0
    assert all('id' in item for item in items)
    assert all('title' in item for item in items)
    assert all('url' in item for item in items)

@pytest.mark.asyncio
async def test_normalize():
    """测试数据标准化"""
    config = {
        'id': 'test',
        'name': '测试',
        'enabled': True,
        'type': 'rss',
        'url': 'https://example.com/feed'
    }

    source = RSSSource(config)
    raw_data = {
        'id': '123',
        'title': '测试标题',
        'link': 'https://example.com/123',
        'summary': '测试摘要',
        'published': 'Mon, 13 Jan 2025 10:00:00 GMT'
    }

    normalized = source.normalize(raw_data)

    assert normalized['id'] == 'test_123'
    assert normalized['title'] == '测试标题'
    assert normalized['url'] == 'https://example.com/123'
    assert 'publish_time' in normalized
```

#### 测试数据库模型

创建 `backend/tests/test_models.py`:

```python
"""
数据库模型单元测试
"""
import pytest
from datetime import datetime
from models.database import News, CrawlerLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine('sqlite:///:memory:')
    from models.database import Base
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()

def test_create_news(db_session):
    """测试创建新闻记录"""
    news = News(
        news_id='test_123',
        title='测试新闻',
        url='https://example.com/123',
        summary='测试摘要',
        content='测试内容',
        source='测试来源',
        category='model',
        tags='AI,GPT',
        publish_time=datetime.now(),
        crawl_time=datetime.now()
    )

    db_session.add(news)
    db_session.commit()

    # 查询
    retrieved = db_session.query(News).filter(News.news_id == 'test_123').first()
    assert retrieved is not None
    assert retrieved.title == '测试新闻'
    assert retrieved.category == 'model'

def test_crawler_log(db_session):
    """测试爬虫日志"""
    log = CrawlerLog(
        platform='36氪',
        start_time=datetime.now(),
        end_time=datetime.now(),
        status='success',
        items_crawled=50
    )

    db_session.add(log)
    db_session.commit()

    # 查询
    retrieved = db_session.query(CrawlerLog).first()
    assert retrieved.platform == '36氪'
    assert retrieved.items_crawled == 50
```

### 2. 运行后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_ai_service.py

# 运行特定测试函数
pytest tests/test_ai_service.py::test_classify_news

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s

# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行异步测试
pytest -v tests/
```

---

## 前端测试

### 1. 组件测试

创建 `frontend/src/components/__tests__/NewsCard.test.ts`:

```typescript
/**
 * NewsCard 组件测试
 */
import { describe, it, expect } from 'vitest'

describe('NewsCard', () => {
  it('should render news card with correct data', () => {
    const news = {
      id: '1',
      title: '测试新闻标题',
      summary: '这是测试摘要',
      source: '36氪',
      category: 'model',
      publish_time: '2025-01-13T10:00:00',
      url: 'https://example.com/123'
    }

    expect(news.title).toBe('测试新闻标题')
    expect(news.category).toBe('model')
  })

  it('should format category name correctly', () => {
    const getCategoryName = (category: string) => {
      const map: Record<string, string> = {
        model: '模型',
        product: '产品',
        investment: '融资',
        view: '观点'
      }
      return map[category] || category
    }

    expect(getCategoryName('model')).toBe('模型')
    expect(getCategoryName('product')).toBe('产品')
  })
})
```

### 2. 运行前端测试

在 `frontend/package.json` 中添加测试脚本:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

运行测试:

```bash
cd frontend

# 运行所有测试
npm test

# 运行 UI 模式
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

---

## API 测试

### 1. 使用 pytest + httpx

创建 `backend/tests/test_api.py`:

```python
"""
API 端点测试
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "AI News Tracker API" in response.json()["message"]

def test_get_news():
    """测试获取资讯列表"""
    response = client.get("/api/news?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_news_with_filters():
    """测试带筛选的资讯获取"""
    response = client.get("/api/news?category=model&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_news_detail():
    """测试获取资讯详情"""
    # 先获取列表
    list_response = client.get("/api/news?limit=1")
    news_list = list_response.json()

    if news_list:
        news_id = news_list[0]['news_id']
        response = client.get(f"/api/news/{news_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['news_id'] == news_id

def test_get_stats():
    """测试获取统计信息"""
    response = client.get("/api/stats")

    assert response.status_code == 200
    data = response.json()
    assert 'total_news' in data
    assert 'category_stats' in data

def test_trigger_crawl():
    """测试触发爬虫"""
    response = client.post("/api/crawl")

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'running'

def test_generate_content():
    """测试内容生成"""
    # 先获取一条新闻
    list_response = client.get("/api/news?limit=1")
    news_list = list_response.json()

    if news_list:
        news_id = news_list[0]['news_id']
        response = client.post(
            "/api/generate",
            json={
                "news_id": news_id,
                "versions": ["A", "B"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all('version' in item for item in data)
```

### 2. 使用 cURL 测试

```bash
# 测试根路径
curl http://localhost:8000/

# 测试获取资讯
curl http://localhost:8000/api/news?limit=5

# 测试带筛选
curl http://localhost:8000/api/news?category=model&source=36氪

# 测试获取统计
curl http://localhost:8000/api/stats

# 测试触发爬虫
curl -X POST http://localhost:8000/api/crawl

# 测试生成内容
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"news_id":"36kr_123","versions":["A","B","C"]}'
```

### 3. 使用 Postman 测试

导入以下集合到 Postman:

```json
{
  "info": {
    "name": "AI News Tracker API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get News",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/news?limit=10",
          "host": ["{{base_url}}"],
          "path": ["api", "news"],
          "query": [{"key": "limit", "value": "10"}]
        }
      }
    },
    {
      "name": "Trigger Crawl",
      "request": {
        "method": "POST",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/crawl",
          "host": ["{{base_url}}"],
          "path": ["api", "crawl"]
        }
      }
    },
    {
      "name": "Generate Content",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"news_id\": \"36kr_123\",\n  \"versions\": [\"A\", \"B\", \"C\"]\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/generate",
          "host": ["{{base_url}}"],
          "path": ["api", "generate"]
        }
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000"}
  ]
}
```

---

## 集成测试

### 1. 端到端测试流程

创建 `backend/tests/test_integration.py`:

```python
"""
集成测试 - 完整流程测试
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app
from models.database import SessionLocal, News
from tasks.crawler import crawl_all_sources

client = TestClient(app)

@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流程"""

    # 1. 触发爬虫
    crawl_response = client.post("/api/crawl")
    assert crawl_response.status_code == 200

    # 等待爬虫完成
    await asyncio.sleep(10)

    # 2. 检查数据
    news_response = client.get("/api/news?limit=10")
    assert news_response.status_code == 200
    news_list = news_response.json()

    # 3. 生成内容
    if news_list:
        news_id = news_list[0]['news_id']
        gen_response = client.post(
            "/api/generate",
            json={
                "news_id": news_id,
                "versions": ["A"]
            }
        )

        assert gen_response.status_code == 200
        generated = gen_response.json()
        assert len(generated) == 1
        assert 'title' in generated[0]
        assert 'content' in generated[0]

    # 4. 检查统计
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats['total_news'] >= 0
```

### 2. 手动集成测试清单

**测试前准备:**
- [ ] 后端服务运行正常 (http://localhost:8000)
- [ ] 前端服务运行正常 (http://localhost:4321)
- [ ] 数据库已初始化
- [ ] API Keys 已配置

**功能测试清单:**

**爬虫功能:**
- [ ] 手动触发爬虫成功
- [ ] 爬虫能获取数据
- [ ] 数据正确保存到数据库
- [ ] 爬虫日志正确记录
- [ ] 失败重试机制正常工作

**AI 处理:**
- [ ] 资讯自动分类准确
- [ ] 摘要生成质量良好
- [ ] 3种版本内容风格差异明显
- [ ] 标签生成合理
- [ ] 后备方案可用（API 失败时）

**API 接口:**
- [ ] GET /api/news 返回数据
- [ ] 筛选参数工作正常
- [ ] 分页功能正常
- [ ] POST /api/generate 生成内容
- [ ] GET /api/stats 统计正确
- [ ] 错误处理正确（404, 500 等）

**前端界面:**
- [ ] 页面加载正常
- [ ] 资讯卡片显示正确
- [ ] 分类筛选工作
- [ ] 刷新按钮功能正常
- [ ] 生成按钮显示生成结果
- [ ] 响应式设计适配移动端

---

## 性能测试

### 1. API 响应时间测试

创建 `backend/tests/test_performance.py`:

```python
"""
性能测试
"""
import pytest
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_response_time():
    """测试 API 响应时间"""
    start_time = time.time()

    response = client.get("/api/news?limit=50")

    end_time = time.time()
    response_time = end_time - start_time

    assert response.status_code == 200
    assert response_time < 2.0  # 响应时间应小于 2 秒

    print(f"API 响应时间: {response_time:.2f} 秒")

def test_concurrent_requests():
    """测试并发请求"""
    import concurrent.futures

    def make_request():
        response = client.get("/api/news?limit=10")
        return response.status_code

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    end_time = time.time()
    total_time = end_time - start_time

    assert all(r == 200 for r in results)
    print(f"50 个并发请求耗时: {total_time:.2f} 秒")
    print(f"平均每个请求: {total_time/50:.3f} 秒")
```

### 2. 使用 Apache Bench (ab)

```bash
# 安装 ab
# macOS: 已预装
# Ubuntu: sudo apt-get install apache2-utils

# 测试获取资讯接口（100 个请求，10 个并发）
ab -n 100 -c 10 http://localhost:8000/api/news?limit=10

# 测试 POST 请求
ab -n 50 -c 5 -p data.json -T application/json http://localhost:8000/api/generate
```

### 3. 使用 Locust

创建 `locustfile.py`:

```python
"""
Locust 性能测试配置
"""
from locust import HttpUser, task, between

class NewsTrackerUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_news(self):
        self.client.get("/api/news?limit=20")

    @task(3)
    def get_home(self):
        self.client.get("/")
```

运行 Locust:

```bash
# 安装 Locust
pip install locust

# 运行测试
locust -f locustfile.py --host=http://localhost:8000

# 访问 Web UI
open http://localhost:8089
```

---

## 测试报告

### 生成测试报告

```bash
# 后端覆盖率报告
cd backend
pytest --cov=. --cov-report=html --cov-report=term

# 查看报告
open htmlcov/index.html

# 前端覆盖率报告
cd frontend
npm run test:coverage

# 查看报告
open coverage/index.html
```

### 持续集成 (CI)

创建 `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        cd backend
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd frontend
        npm install

    - name: Run tests
      run: |
        cd frontend
        npm test
```

---

## 测试最佳实践

### 1. 测试命名规范

```python
# ✅ 好的命名
def test_classify_news_returns_model_category()
def test_generate_content_with_valid_news_id()

# ❌ 不好的命名
def test1()
def test_classification()
```

### 2. 测试隔离

```python
# ✅ 每个测试独立
@pytest.fixture
def clean_db():
    # 每次测试前清理数据库
    db.query(News).delete()
    db.commit()

def test_create_news(clean_db):
    # 测试代码

# ❌ 测试互相依赖
def test_create_news():
    # 创建数据

def test_delete_news():
    # 依赖上面的数据
```

### 3. 使用 Mock

```python
from unittest.mock import patch, AsyncMock

@patch('services.ai_service.OpenAI')
async def test_classify_with_mock(mock_openai):
    # Mock API 调用
    mock_client = AsyncMock()
    mock_openai.return_value = mock_client

    # 测试代码，不会真正调用 API
```

---

## 下一步

完成测试后：

1. **确保所有测试通过**
2. **覆盖率目标**: 后端 > 80%，前端 > 70%
3. **性能基准**: API 响应 < 2s
4. **设置 CI/CD**: 自动运行测试
5. **定期运行**: 每次代码变更前

测试是保证代码质量的关键，请确保在生产环境部署前完成所有测试！
