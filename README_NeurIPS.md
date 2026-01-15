# NeurIPS 数据集挖掘工具

从NeurIPS会议获取Spotlight和Best论文，自动提取数据集信息。

## 🎯 功能说明

### 支持的论文类型
- **Spotlight**: 重要论文（spotlight presentation）
- **Oral**: 口头报告论文
- **Best Paper**: 最佳论文获奖作品

### 数据来源
根据[NeurIPS官网](https://neurips.cc)，程序使用三种方法获取论文：

1. **OpenReview API** - NeurIPS使用OpenReview管理论文
2. **NeurIPS Proceedings** - https://papers.nips.cc/
3. **neurips.cc Awards** - 官网获奖论文信息

## 🚀 使用方法

### 快速开始

```bash
cd dataset_miner

# 1. 先测试能否获取论文列表
python3 test_neurips.py

# 2. 如果测试成功，运行完整程序
python3 main_neurips.py
```

### 输出位置
- **结果文件**: `outputs/dataset_neurips_results.jsonl`
- **日志文件**: `dataset_miner_neurips.log`

## 📊 输出格式

与ICLR、ACL版本相同的JSONL格式：

```json
{
  "dataset id": "001",
  "name": "ImageNet",
  "dataset describe": {
    "content": "数据集详细描述",
    "type": ["image classification"],
    "domain": ["computer vision"],
    "fields": ["deep learning"]
  },
  "paper_refs": {
    "title": "论文标题",
    "authors": [
      {"name": "作者名", "institution": "机构"}
    ],
    "venue": "NeurIPS spotlight",
    "year": "2025",
    "url": "https://openreview.net/forum?id=xxx",
    "is_fellow": "true"  // Best Paper时为true
  },
  "dataset link": "https://github.com/...",
  "platform": "GitHub"
}
```

## 🔧 工作流程

### 1. 获取论文列表（三种方法）

#### 方法1: OpenReview API
```python
# NeurIPS使用OpenReview管理投稿
# Venue ID: NeurIPS.cc/2025/Conference
```

#### 方法2: NeurIPS Proceedings
```python
# 访问 https://papers.nips.cc/paper_files/paper/2025
# 解析HTML获取论文列表
```

#### 方法3: neurips.cc Awards页面
```python
# 访问 https://neurips.cc/Conferences/2025/Awards
# 获取获奖论文信息
```

### 2. 论文下载
根据获取到的PDF链接下载

### 3. 信息提取
- 解析PDF文本
- 提取URL链接
- 调用GPT-4o提取结构化信息

### 4. 即时保存
每处理完一篇论文立即保存到文件

## 📝 关键文件

```
dataset_miner/
├── main_neurips.py          # NeurIPS主程序
├── neurips_downloader.py    # NeurIPS下载器
├── test_neurips.py          # 测试脚本
├── pdf_parser.py            # PDF解析（共用）
├── llm_client.py            # LLM调用（共用）
├── prompts.py               # 提示词模板（共用）
├── outputs/
│   └── dataset_neurips_results.jsonl  # 输出结果
├── temp/                    # 临时PDF存储
└── dataset_miner_neurips.log  # 日志文件
```

## ⚙️ 配置说明

### 修改年份
编辑 `main_neurips.py`:
```python
def main():
    miner = NeurIPSDatasetMiner(output_file="outputs/dataset_neurips_results.jsonl")
    miner.run(year=2024)  # 修改年份
```

### 修改论文类型
编辑 `neurips_downloader.py` 中的 `categories`:
```python
self.categories = ['spotlight', 'oral']  # 添加或删除类型
```

## 🔍 NeurIPS URL结构

### OpenReview
- Venue: `NeurIPS.cc/2025/Conference`
- 论文URL: `https://openreview.net/forum?id={submission_id}`
- PDF: `https://openreview.net/pdf?id={submission_id}`

### Proceedings
- 主页: `https://papers.nips.cc/paper_files/paper/{year}`
- 论文页: `https://papers.nips.cc/paper/{year}/hash/{hash}`
- PDF: `https://papers.nips.cc/paper/{year}/file/{hash}.pdf`

### 官网
- 会议主页: `https://neurips.cc/Conferences/{year}`
- 获奖信息: `https://neurips.cc/Conferences/{year}/Awards`

## ⚠️ 注意事项

### 1. 会议时间
NeurIPS 2025:
- **论文通知**: 2025年9月18日
- **会议日期**: 2025年12月2-7日
- **地点**: 圣地亚哥 + 墨西哥城

如果当前日期早于9月18日，论文列表可能还未公布。

### 2. 数据可用性

2025年的论文可能还未完全发布。如果没有找到论文，可以：
- 尝试2024年: `miner.run(year=2024)`
- 查看官网确认论文是否已发布

### 3. 多数据源策略

程序会尝试三种方法获取论文，并自动合并去重：
- OpenReview（最全面）
- Proceedings（发布后可用）
- neurips.cc Awards（获奖论文）

### 4. 网络连接
需要稳定的网络连接访问：
- openreview.net
- papers.nips.cc
- neurips.cc

## 📈 运行示例

```bash
$ python3 test_neurips.py

============================================================
测试NeurIPS下载器
============================================================

尝试获取 2024 年论文...

--- 方法1: OpenReview ---
✓ OpenReview找到 156 篇论文

前3篇示例:

1. [SPOTLIGHT] Neural Network Verification with Branch-and-Bound
   URL: https://openreview.net/forum?id=xxx

2. [ORAL] Best of Both Worlds: Learning Safe Data-Driven Systems
   URL: https://openreview.net/forum?id=yyy

3. [BEST] Outstanding Paper Award Winner
   URL: https://openreview.net/forum?id=zzz

--- 方法2: Proceedings ---
✓ Proceedings找到 142 篇论文

--- 方法3: neurips.cc Awards ---
✓ 找到 5 篇获奖论文

✅ 2024 年共找到 303 篇论文（合并前）

============================================================
测试完成
============================================================
```

## 🎓 NeurIPS会议说明

### 关于NeurIPS
NeurIPS（Conference on Neural Information Processing Systems）是机器学习和人工智能领域的顶级会议之一。

### 论文类型
- **Oral** (~1-2%): 最顶尖论文，口头报告
- **Spotlight** (~3-5%): 重要论文，简短展示
- **Poster** (~20-25%): 接收论文，海报展示

本工具专注于**Oral和Spotlight**论文。

### 会议规模
NeurIPS 2024统计：
- 投稿数: ~15,000+
- 接收率: ~25%
- Oral + Spotlight: ~300-400篇

## 🔧 故障排除

### 问题1: 未找到论文
**原因**: 2025年论文可能未发布（9月18日后才会公布）
**解决**: 使用已发布的年份，如 `miner.run(year=2024)`

### 问题2: OpenReview连接失败
**原因**: 网络问题或API变化
**解决**: 程序会自动尝试其他方法（Proceedings、Awards）

### 问题3: PDF下载失败
**原因**: PDF链接失效或格式变化
**解决**: 查看日志中的具体错误，程序会跳过失败的论文继续处理

## 📧 对比说明

### ICLR vs ACL vs NeurIPS

| 特性 | ICLR | ACL | NeurIPS |
|------|------|-----|---------|
| 数据源 | OpenReview | ACL Anthology | OpenReview + Proceedings |
| 论文类型 | Oral/Spotlight/Poster | Main/Findings | Oral/Spotlight/Best |
| 获取方式 | API | 网页爬取+BibTeX | 多源合并 |
| 年份 | 2025 | 2024 | 2025 |
| 输出文件 | dataset_iclr_results.jsonl | dataset_acl_results.jsonl | dataset_neurips_results.jsonl |
| 日志文件 | dataset_miner.log | dataset_miner_acl.log | dataset_miner_neurips.log |

三者共用相同的PDF解析和LLM提取逻辑！

## 🌟 特色功能

### 1. 多源合并
自动从三个数据源获取论文并去重

### 2. Best Paper标记
获奖论文在 `is_fellow` 字段标记为 `"true"`

### 3. 完整元数据
包含论文在OpenReview、Proceedings等多个平台的链接

### 4. 容错能力
单个数据源失败不影响其他源的数据获取

