# ICML 数据集挖掘工具

从ICML会议获取Oral和Spotlight论文，自动提取数据集信息。

## 🎯 功能说明

### 支持的论文类型
- **Oral**: 口头报告论文（最顶尖论文）
- **Spotlight**: 重要论文
- **Best Paper**: 最佳论文获奖作品

### 数据来源

1. **PMLR (Proceedings of Machine Learning Research)**
   - 官方主页：https://proceedings.mlr.press/
   - ICML论文的正式出版平台
   - Volume编号：ICML 2024是v235, 2023是v202

2. **OpenReview**
   - ICML近年来也使用OpenReview管理投稿
   - Venue: ICML.cc/2025/Conference

## 🚀 使用方法

### 快速开始

```bash
cd dataset_miner

# 1. 先测试能否获取论文列表
python3 test_icml.py

# 2. 如果测试成功，运行完整程序
python3 main_icml.py
```

### 输出位置
- **结果文件**: `outputs/dataset_icml_results.jsonl`
- **日志文件**: `dataset_miner_icml.log`

## 📊 输出格式

与ICLR、ACL、NeurIPS版本相同的JSONL格式：

```json
{
  "dataset id": "001",
  "name": "CIFAR-10",
  "dataset describe": {
    "content": "数据集详细描述",
    "type": ["image classification"],
    "domain": ["computer vision"],
    "fields": ["machine learning"]
  },
  "paper_refs": {
    "title": "论文标题",
    "authors": [
      {"name": "作者名", "institution": "机构"}
    ],
    "venue": "ICML oral",
    "year": "2024",
    "url": "https://proceedings.mlr.press/v235/...",
    "is_fellow": "false"
  },
  "dataset link": "https://github.com/...",
  "platform": "GitHub"
}
```

## 🔧 工作流程

### 1. 获取论文列表（双重方法）

#### 方法1: PMLR Proceedings
```python
# 访问 https://proceedings.mlr.press/v235 (2024)
# 解析HTML获取论文列表
# 筛选Oral和Spotlight论文
```

#### 方法2: OpenReview API
```python
# Venue: ICML.cc/2024/Conference
# 通过OpenReview API获取论文
# 根据decision筛选
```

### 2. 论文下载
从PMLR或OpenReview下载PDF

### 3. 信息提取
- 解析PDF文本
- 提取URL链接  
- 调用GPT-4o提取结构化信息

### 4. 即时保存
每处理完一篇论文立即保存到文件

## 📝 关键文件

```
dataset_miner/
├── main_icml.py             # ICML主程序
├── icml_downloader.py       # ICML下载器
├── test_icml.py             # 测试脚本
├── pdf_parser.py            # PDF解析（共用）
├── llm_client.py            # LLM调用（共用）
├── prompts.py               # 提示词模板（共用）
├── outputs/
│   └── dataset_icml_results.jsonl  # 输出结果
├── temp/                    # 临时PDF存储
└── dataset_miner_icml.log   # 日志文件
```

## ⚙️ 配置说明

### 修改年份
编辑 `main_icml.py`:
```python
def main():
    miner = ICMLDatasetMiner(output_file="outputs/dataset_icml_results.jsonl")
    miner.run(year=2024)  # 修改年份
```

### Volume编号映射
如需修改或添加年份，编辑 `icml_downloader.py`:
```python
self.volume_map = {
    2024: 'v235',
    2023: 'v202',
    2022: 'v162',
    # 添加更多年份...
}
```

## 🔍 ICML URL结构

### PMLR Proceedings
- Volume主页: `https://proceedings.mlr.press/v{number}`
- 论文页面: `https://proceedings.mlr.press/v{number}/{author}{year}.html`
- PDF下载: `https://proceedings.mlr.press/v{number}/{author}{year}.pdf`

### OpenReview
- Venue: `ICML.cc/{year}/Conference`
- 论文URL: `https://openreview.net/forum?id={submission_id}`
- PDF: `https://openreview.net/pdf?id={submission_id}`

### Volume编号历史
| 年份 | Volume | 说明 |
|------|--------|------|
| 2024 | v235 | ICML 2024 |
| 2023 | v202 | ICML 2023 |
| 2022 | v162 | ICML 2022 |
| 2021 | v139 | ICML 2021 |
| 2020 | v119 | ICML 2020 |

## ⚠️ 注意事项

### 1. 会议时间
ICML通常在每年**7-8月**举行。

ICML 2024:
- **日期**: 2024年7月21-27日
- **地点**: 维也纳，奥地利

### 2. 数据可用性

- **PMLR**: 会议结束后发布完整proceedings
- **OpenReview**: 论文接收后逐步开放

如果当前年份的论文未发布：
```python
# 使用上一年的数据
miner.run(year=2023)
```

### 3. 双数据源策略

程序会尝试两种方法并自动合并去重：
1. PMLR（完整、官方）
2. OpenReview（及时、详细）

### 4. 网络连接
需要稳定的网络连接访问：
- proceedings.mlr.press
- openreview.net

## 📈 运行示例

```bash
$ python3 test_icml.py

============================================================
测试ICML下载器
============================================================

尝试获取 2024 年论文...

--- 方法1: PMLR ---
✓ PMLR找到 89 篇论文

前3篇示例:

1. [ORAL] Deep Reinforcement Learning with Plasticity Injection
   PDF: https://proceedings.mlr.press/v235/...

2. [SPOTLIGHT] Neural Architecture Search for Transformers
   PDF: https://proceedings.mlr.press/v235/...

3. [ORAL] Provably Efficient Exploration in Reinforcement Learning
   PDF: https://proceedings.mlr.press/v235/...

--- 方法2: OpenReview ---
✓ OpenReview找到 156 篇论文

✅ 2024 年共找到 245 篇论文（合并前）

============================================================
测试完成
============================================================
```

## 🎓 ICML会议说明

### 关于ICML
ICML（International Conference on Machine Learning）创立于1980年，是机器学习领域历史最悠久、影响力最大的国际会议之一。

### 论文类型
- **Oral** (~2-3%): 最顶尖论文，口头报告
- **Spotlight** (~5-8%): 重要论文，简短展示
- **Poster** (~20-25%): 接收论文，海报展示

本工具专注于**Oral和Spotlight**论文。

### 会议规模
ICML 2024统计：
- 投稿数: ~9,000+
- 接收率: ~27%
- Oral + Spotlight: ~400-500篇

### 论文出版
ICML论文正式出版在**PMLR (Proceedings of Machine Learning Research)**，这是JMLR旗下的开放获取会议论文系列。

## 🔧 故障排除

### 问题1: 未找到论文
**原因**: 当年论文可能未发布
**解决**: 使用已发布的年份
```python
miner.run(year=2024)  # 或更早的年份
```

### 问题2: PMLR解析失败
**原因**: HTML结构变化
**解决**: 程序会自动尝试OpenReview方法

### 问题3: Volume编号不正确
**原因**: 新年份的Volume编号未更新
**解决**: 
1. 访问 https://proceedings.mlr.press/ 查找正确编号
2. 更新 `icml_downloader.py` 中的 `volume_map`

### 问题4: PDF下载失败
**原因**: 网络问题或链接格式变化
**解决**: 查看日志，程序会跳过失败的论文继续处理

## 📧 四大会议对比

### ICLR vs ACL vs NeurIPS vs ICML

| 特性 | ICLR | ACL | NeurIPS | ICML |
|------|------|-----|---------|------|
| 领域 | 深度学习 | NLP | AI/ML | 机器学习 |
| 数据源 | OpenReview | ACL Anthology | OpenReview+Proceedings | PMLR+OpenReview |
| 论文类型 | Oral/Spotlight/Poster | Main/Findings | Oral/Spotlight/Best | Oral/Spotlight |
| 年度 | 2025 | 2024 | 2025 | 2024 |
| 会议时间 | 5月 | 7-8月 | 12月 | 7-8月 |
| 输出文件 | dataset_iclr_results.jsonl | dataset_acl_results.jsonl | dataset_neurips_results.jsonl | dataset_icml_results.jsonl |

四者共用相同的PDF解析和LLM提取逻辑！

## 🌟 特色功能

### 1. 双源合并
自动从PMLR和OpenReview获取论文并去重

### 2. Volume自动匹配
根据年份自动选择对应的PMLR Volume编号

### 3. 完整元数据
包含论文在PMLR、OpenReview等平台的链接

### 4. 容错能力
单个数据源失败不影响其他源的数据获取

## 💡 最佳实践

1. **优先使用2024年数据**: PMLR已完整发布
2. **检查Volume编号**: 新年份需要更新映射表
3. **查看官网**: https://icml.cc/ 确认会议日期和状态
4. **测试先行**: 运行 `test_icml.py` 确认数据可用性

## 🔗 相关链接

- **ICML官网**: https://icml.cc/
- **PMLR主页**: https://proceedings.mlr.press/
- **OpenReview**: https://openreview.net/
- **历年Proceedings**: https://proceedings.mlr.press/



