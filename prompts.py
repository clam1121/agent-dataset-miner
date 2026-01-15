"""
提示词模板
用于LLM提取论文中的数据集信息
"""

# 提取论文元信息
EXTRACT_PAPER_META_PROMPT = """
请从以下论文文本中提取论文的元信息。

论文文本：
{text}

请提取以下信息：
1. 论文标题 (title)
2. 作者列表 (authors)，格式为字符串数组，例如 ["作者1", "作者2", "作者3"]
3. 机构列表 (institutions)，格式为字符串数组，例如 ["机构1", "机构2", "机构3"]
4. 会议或期刊名称 (venue)
5. 发表年份 (year)
6. 论文URL (url)，如果文本中没有明确的论文URL，可以留空
7. is_fellow: 固定填写 "false"

请以JSON格式返回，格式如下：
```json
{{
  "title": "论文标题",
  "authors": ["作者1", "作者2", "作者3"],
  "institutions": ["机构1", "机构2", "机构3"],
  "venue": "会议或期刊名称",
  "year": "年份",
  "url": "论文URL（如果有）",
  "is_fellow": "false"
}}
```

注意：
- authors 和 institutions 是独立的数组，不需要一一对应
- 如果无法提取某个字段，可以使用空数组 []

只返回JSON，不要其他说明文字。
"""

# 提取数据集名称
EXTRACT_DATASET_NAMES_PROMPT = """
请从以下论文文本中识别所有提到的数据集名称。

论文文本：
{text}

请注意：
1. 只提取数据集名称，不要包含模型名称
2. 数据集通常出现在实验部分、数据集描述部分
3. 常见的数据集名称格式：ImageNet, COCO, SQuAD, GLUE等
4. 如果论文提出了新数据集，也要提取出来

请以JSON格式返回数据集名称列表：
```json
{{
  "datasets": ["数据集名称1", "数据集名称2", "数据集名称3"]
}}
```

只返回JSON，不要其他说明文字。
"""

# 提取数据集详细信息
EXTRACT_DATASET_DETAILS_PROMPT = """
请从以下论文文本中提取关于数据集 "{dataset_name}" 的详细信息。

论文文本：
{text}

URL链接：
{urls}

请提取以下信息：
1. name: 数据集名称（必填，就是 "{dataset_name}"）
2. content: 数据集的详细描述（用途、规模、特点等）
3. type: 数据集类型，例如 ["multiple-choice questions", "image classification", "text generation"]
4. domain: 数据集涉及的领域，例如 ["natural language processing", "computer vision", "audio"]
5. fields: 应用方向，例如 ["large language models evaluation", "object detection"]
6. dataset_link: 数据集的下载链接（从提供的URL中选择最相关的，或根据上下文推断）
7. platform: 平台名称，例如 "GitHub", "HuggingFace", "Kaggle", "官方网站"等

请以JSON格式返回：
```json
{{
  "name": "{dataset_name}",
  "content": "数据集的详细描述",
  "type": ["类型1", "类型2"],
  "domain": ["领域1", "领域2"],
  "fields": ["应用1", "应用2"],
  "dataset_link": "数据集链接",
  "platform": "平台名称"
}}
```

注意：
- name 字段必须填写数据集名称 "{dataset_name}"
- 如果某个字段无法从文本中获取，请尽量推断或使用 "unspecified"
- dataset_link 优先从提供的URL列表中选择，如果都不相关则留空
- platform 要根据 dataset_link 判断（github.com -> GitHub, huggingface.co -> HuggingFace等）

只返回JSON，不要其他说明文字。
"""

# 提取所有URL链接
EXTRACT_URLS_PROMPT = """
请从以下论文文本中提取所有的URL链接。

论文文本：
{text}

请提取所有HTTP/HTTPS链接，并以JSON格式返回：
```json
{{
  "urls": ["https://example.com/1", "https://github.com/user/repo", "https://huggingface.co/dataset"]
}}
```

只返回JSON，不要其他说明文字。
"""

