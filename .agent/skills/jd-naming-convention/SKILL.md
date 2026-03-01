---
name: JD Job Code Naming Convention
description: 职位编号(job_code)命名规范。导入、新建、更新JD时必须首先查阅此规范，确保编号格式统一。
---

# 职位编号 (Job Code) 命名规范

> **⚠️ 强制规则：** 任何涉及 JD 导入、新建、更新的操作，都必须先查阅此规范，确保 job_code 命名正确。

## 1. 编号格式

```
{公司前缀}{4位数字}
```

- **前缀**：大写英文字母，代表公司
- **数字**：4位，从 0001 开始顺序递增，不跳号
- **示例**：`MMX0001`, `ALI0222`, `BT0029`, `XHS0001`

## 2. 公司前缀映射表

前缀映射定义在 `data/company_prefix_map.json`，以下是当前完整映射：

| 公司 | 前缀 | 备注 |
|:---|:---:|:---|
| **阿里系** (集团/云/高德/钉钉/淘天/健康/平头哥/优酷) | `ALI` | |
| **阿里云** (云智能集团独立) | `AY` | |
| **蚂蚁集团** | `ANT` | |
| **字节跳动** / ByteDance | `BT` | |
| **小红书** | `XHS` | 历史遗留有 `xhs_` 前缀，新增请用 `XHS` |
| **MiniMax** | `MMX` | ⚠️ 不要用 `M` 前缀 |
| **腾讯** | `TX` | |
| **百度** | `BD` | |
| **美团** | `MT` | |
| **京东** | `JD` | |
| **快手** | `KS` | |
| **滴滴** | `DD` | |
| **拼多多** | `PDD` | |
| **网易** | `WY` | |
| **华为** | `HW` | |
| **小米** | `MI` | |
| **OPPO** | `OP` | |
| **vivo** | `VI` | |
| **月之暗面** / Moonshot | `KIMI` | |
| **智谱** | `ZP` | |
| **阶跃星辰** | `JY` | |
| **深度求索** / DeepSeek | `DS` | |
| **零一万物** | `01` | |
| **商汤** | `ST` | |
| **旷视** | `KS` | 注意与快手重复，需区分 |
| **依图** | `YT` | |
| **云从** | `YC` | |
| **科大讯飞** | `KDXF` | |
| **蔚来** | `NIO` | |
| **理想** | `LI` | |
| **小鹏** | `XP` | |
| **比亚迪** | `BYD` | |
| **大疆** | `DJI` | |
| **微软** / Microsoft | `MS` | |
| **谷歌** / Google | `GG` | |
| **亚马逊** / Amazon | `AMZ` | |
| **苹果** / Apple | `APP` | |
| **Meta** / Facebook | `META` | |
| **OpenAI** | `OAI` | |
| **Anthropic** | `ANT` | |
| **铁柱** | `TIE` | |
| **智能创作** | `ZHI` | |
| 未收录公司 | `OTH` | 默认兜底前缀 |

## 3. 编号生成逻辑

### 3.1 查询当前最大编号

导入前必须查询数据库获取当前最大编号：

```sql
-- 查询某公司前缀的最大编号
SELECT MAX(CAST(SUBSTR(job_code, LENGTH('MMX')+1) AS INTEGER))
FROM jobs
WHERE job_code LIKE 'MMX%';
```

### 3.2 Python 代码参考

```python
from sqlalchemy import text

def generate_job_code(db, company_name, prefix_map):
    """生成下一个可用的 job_code"""
    prefix = prefix_map.get(company_name, "OTH")
    
    # 查询当前最大编号
    result = db.execute(text(
        f"SELECT MAX(CAST(SUBSTR(job_code, {len(prefix)+1}) AS INTEGER)) "
        f"FROM jobs WHERE job_code LIKE '{prefix}%'"
    )).fetchone()
    
    max_num = result[0] if result[0] else 0
    return f"{prefix}{max_num + 1:04d}"
```

## 4. 常见错误 ❌

| 错误示例 | 问题 | 正确格式 |
|:---|:---|:---|
| `M1`, `M2` | 前缀不规范，MiniMax 应用 `MMX` | `MMX0001`, `MMX0002` |
| `MMX1` | 缺少零填充 | `MMX0001` |
| `minimax001` | 前缀应大写 | `MMX0001` |
| `xhs_020` | 历史格式，新增应统一大写 | `XHS0020` |
| `A04889` | 不明前缀 | 应使用 `BT` 前缀 |

## 5. 操作检查清单

在导入/新建 JD 时，按以下顺序执行：

1. **确认公司名称** → 查表获取对应前缀
2. **查询最大编号** → `SELECT MAX(...) FROM jobs WHERE job_code LIKE '{prefix}%'`
3. **生成新编号** → 前缀 + (最大值+1) 零填充4位
4. **验证唯一性** → 确保数据库中不存在相同 job_code
5. **写入数据库** → 保存记录

## 6. 新公司前缀申请

如果遇到映射表中没有的公司：
1. 优先使用 2-4 个大写字母的缩写
2. 更新 `data/company_prefix_map.json`
3. 在本文档的映射表中同步添加
