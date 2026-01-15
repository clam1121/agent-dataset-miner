# ⚙️ 配置说明

## API Key 配置

本项目使用环境变量来管理 API Key，确保安全性。

### 方法1：使用 .env 文件（推荐）

1. 复制示例配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API Key：
```bash
AZURE_OPENAI_API_KEY=your_actual_api_key_here
```

3. 安装 python-dotenv（如果使用 .env 文件）：
```bash
pip install python-dotenv
```

4. 在代码开头加载环境变量（已在主程序中添加）：
```python
from dotenv import load_dotenv
load_dotenv()
```

### 方法2：直接设置环境变量

**macOS/Linux:**
```bash
export AZURE_OPENAI_API_KEY="your_api_key_here"
```

**Windows (PowerShell):**
```powershell
$env:AZURE_OPENAI_API_KEY="your_api_key_here"
```

**Windows (CMD):**
```cmd
set AZURE_OPENAI_API_KEY=your_api_key_here
```

### 方法3：在代码中临时设置（不推荐用于生产）

```python
import os
os.environ["AZURE_OPENAI_API_KEY"] = "your_api_key_here"
```

## 配置项说明

| 环境变量 | 说明 | 默认值 | 是否必需 |
|----------|------|--------|----------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API密钥 | 无 | **是** |
| `AZURE_OPENAI_ENDPOINT` | API端点URL | `https://search-va.byteintl.net/...` | 否 |
| `AZURE_OPENAI_API_VERSION` | API版本 | `2024-03-01-preview` | 否 |
| `AZURE_OPENAI_MODEL` | 模型名称 | `gpt-4o-2024-11-20` | 否 |
| `AZURE_OPENAI_MAX_TOKENS` | 最大Token数 | `4096` | 否 |

## 验证配置

运行以下命令验证配置是否正确：

```bash
python3 -c "
from llm_client import call_gpt4o_text
try:
    response = call_gpt4o_text('Hello, test!')
    print('✓ 配置成功！LLM 响应:', response[:50])
except ValueError as e:
    print('✗ 配置错误:', e)
except Exception as e:
    print('✗ API 调用失败:', e)
"
```

## 安全提醒

⚠️ **重要**：
- **永远不要**将 `.env` 文件或包含 API Key 的文件提交到 Git
- `.env` 已经添加到 `.gitignore` 中
- 如果不小心提交了 API Key，请立即：
  1. 撤销提交
  2. 重新生成新的 API Key
  3. 更新本地配置

## 团队协作

对于团队项目：
1. 每个成员创建自己的 `.env` 文件
2. 共享 `.env.example` 作为配置模板
3. 不要共享实际的 API Key
4. 使用统一的密钥管理系统（如 AWS Secrets Manager）

## 故障排查

### 问题1: "AZURE_OPENAI_API_KEY environment variable is not set"

**解决方法**：
```bash
# 检查环境变量是否设置
echo $AZURE_OPENAI_API_KEY  # macOS/Linux
echo %AZURE_OPENAI_API_KEY%  # Windows

# 如果为空，按照上述方法设置
```

### 问题2: API 调用失败

**可能原因**：
- API Key 无效或过期
- 网络连接问题
- API 配额用尽

**解决方法**：
1. 验证 API Key 是否正确
2. 检查网络连接
3. 查看 Azure 控制台的使用情况

### 问题3: .env 文件不生效

**解决方法**：
```bash
# 确保安装了 python-dotenv
pip install python-dotenv

# 确保在代码开头加载了 .env
# 已在 main_agent.py 等主程序中添加
```

---

**配置完成后，就可以安全地运行程序了！** 🎉
