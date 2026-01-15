# ACL Anthology 数据集挖掘工具

从ACL Anthology获取2025年Main和Findings论文，自动提取数据集信息。

## 🎯 功能说明

### 支持的会议
- **ACL** (Association for Computational Linguistics)
- **EMNLP** (Empirical Methods in Natural Language Processing)
- **NAACL** (North American Chapter of the ACL)
- **EACL** (European Chapter of the ACL)

### 支持的论文类型
- **Main** (Long Papers): 主会议的完整论文
- **Findings**: Findings论文集

## 🚀 使用方法

### 运行ACL挖掘程序

```bash
cd dataset_miner
python3 main_acl.py
```

程序会自动：
1. 从ACL Anthology获取2025年所有Main和Findings论文列表
2. 逐篇下载PDF文件
3. 提取论文信息和数据集信息
4. 保存到 `outputs/dataset_acl_results.jsonl`
5. 自动删除已处理的PDF文件

## 📊 输出格式

与ICLR版本相同的JSONL格式：

```json
{
  "dataset id": "001",
  "name": "SQuAD",
  "dataset describe": {
    "content": "数据集详细描述",
    "type": ["question answering"],
    "domain": ["natural language processing"],
    "fields": ["reading comprehension"]
  },
  "paper_refs": {
    "title": "论文标题",
    "authors": [
      {"name": "作者名", "institution": "机构"}
    ],
    "venue": "ACL main",
    "year": "2025",
    "url": "https://aclanthology.org/2025.acl-long.1",
    "is_fellow": "false"
  },
  "dataset link": "https://github.com/...",
  "platform": "GitHub"
}
```

## 🔧 工作流程

### 1. 获取论文列表
使用两种方法：
- **方法1**: 爬取ACL Anthology网页
- **方法2**: 下载并解析BibTeX文件（备用）

### 2. 论文下载
从ACL Anthology下载PDF：
```
https://aclanthology.org/{anthology_id}.pdf
```

### 3. 信息提取
- 解析PDF文本
- 提取URL链接
- 调用GPT-4o提取结构化信息

### 4. 即时保存
每处理完一篇论文立即保存到文件

## 📝 关键文件

```
dataset_miner/
├── main_acl.py              # ACL主程序
├── acl_downloader.py        # ACL下载器
├── pdf_parser.py            # PDF解析（共用）
├── llm_client.py            # LLM调用（共用）
├── prompts.py               # 提示词模板（共用）
├── outputs/
│   └── dataset_acl_results.jsonl  # ACL输出结果
├── temp/                    # 临时PDF存储
└── dataset_miner_acl.log    # ACL日志文件
```

## ⚙️ 配置说明

### 修改年份
编辑 `main_acl.py`:
```python
def main():
    miner = ACLDatasetMiner(output_file="outputs/dataset_acl_results.jsonl")
    miner.run(year=2024)  # 修改年份
```

### 修改会议范围
编辑 `acl_downloader.py` 中的 `venues`:
```python
self.venues = {
    'ACL': f'{year}.acl',
    'EMNLP': f'{year}.emnlp',
    # 添加或删除会议
}
```

### 修改论文类型
编辑 `acl_downloader.py` 中的 `categories`:
```python
self.categories = ['main', 'findings']  # 或添加其他类型
```

## 🔍 ACL Anthology URL结构

### Anthology ID格式
```
{year}.{venue}-{type}.{number}

示例:
- 2025.acl-long.1      (ACL 2025 Main Paper #1)
- 2025.acl-findings.1  (ACL 2025 Findings #1)
- 2025.emnlp-long.1    (EMNLP 2025 Main Paper #1)
```

### 主要URL
- 论文页面: `https://aclanthology.org/{anthology_id}`
- PDF下载: `https://aclanthology.org/{anthology_id}.pdf`
- BibTeX: `https://aclanthology.org/volumes/{volume_id}.bib`
- 会议页面: `https://aclanthology.org/events/{venue}-{year}/`

## ⚠️ 注意事项

### 1. 会议时间
- **ACL**: 通常7-8月
- **EMNLP**: 通常11-12月
- **NAACL**: 通常6月
- **EACL**: 通常4月

如果当前日期早于会议时间，可能还没有论文发布。

### 2. 数据可用性
2025年的论文可能还未发布。如果没有找到论文，可以：
- 尝试2024年: `miner.run(year=2024)`
- 查看ACL Anthology确认论文是否已发布

### 3. 网络连接
需要稳定的网络连接访问 aclanthology.org

### 4. API限制
为避免对服务器造成压力：
- 下载间隔：1秒
- 超时设置：60秒

## 📈 运行示例

```bash
$ python3 main_acl.py

2025-10-15 11:00:00 - __main__ - INFO - === 开始挖掘ACL 2025数据集信息 ===
2025-10-15 11:00:00 - acl_downloader - INFO - 正在获取 ACL main 论文...
2025-10-15 11:00:05 - acl_downloader - INFO - ✓ 成功获取 150 篇 ACL main 论文
2025-10-15 11:00:10 - acl_downloader - INFO - ✓ 成功获取 100 篇 ACL findings 论文
...
2025-10-15 11:00:15 - __main__ - INFO - 处理第 1 篇论文 [ACL_main]
2025-10-15 11:00:15 - __main__ - INFO - 标题: Neural Machine Translation...
...
2025-10-15 11:00:30 - __main__ - INFO - ✓ 已保存数据集: WMT14 (ID: 001)
2025-10-15 11:00:30 - __main__ - INFO - ✅ 成功保存 1 条记录
```

## 🔧 故障排除

### 问题1: 未找到论文
**原因**: 2025年论文可能未发布
**解决**: 使用已发布的年份，如 `miner.run(year=2024)`

### 问题2: 下载PDF失败
**原因**: 网络问题或PDF链接变化
**解决**: 检查网络连接，查看日志中的具体错误

### 问题3: BibTeX解析失败
**原因**: BibTeX格式变化
**解决**: 程序会自动尝试网页爬取方法

## 📧 对比说明

### ICLR vs ACL

| 特性 | ICLR (`main.py`) | ACL (`main_acl.py`) |
|------|------------------|---------------------|
| 数据源 | OpenReview API | ACL Anthology |
| 论文类型 | Oral/Spotlight/Poster | Main/Findings |
| 获取方式 | API调用 | 网页爬取+BibTeX |
| 年份 | 2025 | 2025（可配置） |
| 输出文件 | dataset_iclr_results.jsonl | dataset_acl_results.jsonl |
| 日志文件 | dataset_miner.log | dataset_miner_acl.log |

两者共用相同的PDF解析和LLM提取逻辑！



