# 教授门派定向挖猎 (Dimension 2: Professor-Student Sourcing) 设计方案

**日期**: 2026-03-11  
**状态**: 设计阶段

---

## 核心思考
原有的 `/professor-student-sourcing` 工作流高度依赖人工通过 Google Search 查找实验室主页 (Step 1)、Google Scholar 分析第一作者 (Step 2)、知网/ProQuest 查论文 (Step 3)、以及去领英脉脉查去向 (Step 4)。
如果要将其**转化为每天能自动运行的 pipeline（像现在的顶会挖掘一样）**，我们需要将高度不规则的网页搜索，降维为**结构化的 API 调用**，辅以少量的大模型智能提取。

---

## 自动化落地方案 (`lab_miner.py`)

我们将开发一个自动化的 `lab_miner.py` 脚本，它接受一个**教授名单**作为输入（如 `Andrew Ng, Jitendra Malik, 何恺明`），然后顺藤摸瓜把他们的核心学生全部挖出来存到库里。

### Phase 1: 寻找种子学生 (Student Discovery)

由于“实验室主页”千奇百怪极难自动化解析，而知网/ProQuest 没有好用的免费 API。**最坚实可用、且含金量最高的学生发现渠道是：Semantic Scholar 合著者图谱分析**。因为好教授最得意的门生，一定和教授共同发表过多篇顶会。

这种挖掘可以支持两种模式：

#### 模式 A: 自上而下 (Top-Down)
1. **输入**: 知名教授名单 (如 `Andrew Ng`, `Jitendra Malik`)
2. **通过 API 锁定教授的 Author ID** 请求 Semantic Scholar API 查找对应教授。

#### 模式 B: 自下而上 (Bottom-Up, 强力推荐 🌟)
1. **输入**: 借助我们已经拥有的 `academic_miner.py`，我们已经抓到了大批活跃发论文的学者 (S/A/B 级人才)。
2. **反向寻找 Boss**: 取出他们的高引论文，找出一直挂在通讯作者（最后一位）的**核心导师 (The Boss)**。
3. **扩展网络**: 把找出的这些导师作为新的图谱中心，立刻就能把原本不在我们视野里的其他学生全部挖出来！

#### 锁定核心嫡系 (The Proteges)
无论走哪种模式，只要拿到了教授的 Author ID：
1. **拉取教授近 10 年的高引论文** (请求 `/graph/v1/author/{authorId}/papers`)。
2. **核心学生特征过滤**: 寻找在这些高引论文中**担任第一作者或第二作者**的学者。如果某个人和该教授在 3 年内共同发表了 ≥2 篇论文，极大可能不仅是合作者，而是**其麾下的博士生或博士后**。

### Phase 2: 质量评级与过滤 (Quality Filtering)

1. **复用 `academic_miner.py` 的过滤逻辑**
   - 国籍过滤：只要通过 `detect_nationality` 判定为华人的（或者姓名为拼音的）。
   - 质量打分：再次用拿到的学生 Author ID 去查他的总 h-index、总引用数。
   - 给学生打上 S/A+/A/B/C 的标签。

### Phase 3: 自动化背景审查 (Background Tracing)

原工作流中的 Step 4 是去领英/脉脉搜寻去向。我们可以利用大语言模型（LLM）+ 搜索工具自动化这部分：
1. **组装智能搜索词**：`"{student_name} {professor_name} lab AI LinkedIn site:linkedin.com"` 或 `"{student_name} homepage"`。
2. **通过已有的 `run_phase4_5_llm_enrichment.py` 管道**
   - 我们刚刚已经确认过，提取出来的人无论是去向还是邮箱，都会流入现有的系统库。如果发现他有了 GitHub 链接，会自动走到 phase3、phase3.5 去查库、打标签。

### Phase 4: 增强联系方式提取 (Contact Extraction)

1. 复用今天刚写的强大的 `extract_paper_email.py`。
2. 利用大语言模型让它自己根据论文里的通讯信息（如果 Semantic Scholar 能顺便返回摘要或者原文链接的话）抽取邮箱。

---

## 数据流对接

1. `lab_miner.py` 根据 `professors_seed.csv` 挖掘出所有高潜力的第一作者/关联学生。
2. 输出的候选人同样打平为两条标准的 JSON 路径：
   - `[prefix]_lab_direct_import.json`
   - `[prefix]_lab_github_pipeline.json`
3. 毫无缝隙地融入现有的 `import_github_candidates.py` 和 `batch_runner.py`！

---

## 新脚本的设计规范 (`lab_miner.py`)

```python
import argparse
# ... imports ...

def find_professor_id(name: str, institution: str) -> str:
    """利用 Semantic Scholar 找到真正的该教授 ID"""
    pass

def extract_proteges_from_coauthors(author_id: str, years=10) -> List[Dict]:
    """
    逻辑:
    1. 拿近十年论文
    2. 找出并非通讯作者（一般为First Author）的作者
    3. 按照共同发表次数排序，>=2 次的锁定为嫡系部队
    """
    pass

def enrich_protege_details(proteges: List[Dict]) -> List[Dict]:
    """复用 academic_miner.py 里的 h-index 查询和邮箱抓取方案"""
    pass

def main():
    # 类似 academic_miner
    pass
```
