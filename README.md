# 🤖 Agent-based Dataset Miner

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个基于智能体（Agent）的学术论文数据集自动挖掘系统，实现了 **ReAct (Reasoning + Acting)** 和 **Reflection** 机制。

## 🎯 研究背景

**课题**: Agentic模型在复杂决策任务中的行为可控性机制研究

本项目将传统的固定流程（Workflow）转变为具有**自主决策、反思和学习能力**的智能体系统，用于研究：
- Agent 如何在多次工具调用中进行自主决策
- Reflection 如何帮助 Agent 自我修正和改进
- 记忆系统如何影响 Agent 的行为
- 如何控制和引导 Agent 的决策过程

## ✨ 核心特性

### 1. ReAct 循环
```
Observe → Think → Act → Reflect → Learn → Adjust
```

### 2. Multi-level Reflection
- **基础反思**（规则驱动）：快速评估质量
- **LLM 深度反思**（模型驱动）：深入分析和建议

### 3. Memory System
- **短期记忆**：当前会话的执行历史
- **长期记忆**：重要经验的持久化存储

### 4. 行为可控性
- 透明的决策过程（完整日志）
- 可配置的控制参数
- 支持约束注入

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│       Agent Controller              │
│   (ReAct + Reflection Loop)         │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼───┐    ┌───▼────┐
│Memory │    │ Tool   │
│System │    │Manager │
└───────┘    └────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install openai pymupdf requests pandas matplotlib beautifulsoup4 python-dotenv
```

### 2. 配置 API Key

**重要**: 必须先配置 API Key 才能运行！

复制配置模板并填入你的 API Key：
```bash
cp .env.example .env
# 编辑 .env 文件，设置 AZURE_OPENAI_API_KEY
```

或者直接设置环境变量：
```bash
export AZURE_OPENAI_API_KEY="your_api_key_here"
```

详细配置说明请查看 [CONFIGURATION.md](CONFIGURATION.md)

### 3. 运行 Agent 系统

```bash
# 处理3篇论文（测试）
python3 main_agent.py

# 查看决策过程
tail -f dataset_miner_agent.log | grep "\[反思\]"
```

### 运行对比实验

```bash
# 对比 Workflow vs Agent
python3 experiment_framework.py

# 查看报告
cat experiments/experiment_report.txt
```

## 📊 系统对比

| 特性 | Workflow | Agent System |
|------|----------|--------------|
| 决策方式 | 固定流程 | 动态决策 + 反思 |
| 错误处理 | 跳过 | 自动重试和修正 |
| 质量评估 | ❌ 无 | ✅ 0-1评分 |
| 反思机制 | ❌ 无 | ✅ 两级反思 |
| 记忆系统 | ❌ 无 | ✅ 短期+长期 |
| 自我修正 | ❌ 无 | ✅ 有 |
| 可控性 | ❌ 低 | ✅ 高 |

## 📂 项目结构

```
dataset_miner/
├── agent_core.py              # 核心数据结构
├── agent_controller.py        # Agent 控制器
├── memory_system.py           # 记忆系统
├── reflection_engine.py       # 反思引擎
├── tool_manager.py            # 工具管理器
├── main_agent.py              # Agent 主程序
├── experiment_framework.py    # 实验框架
├── visualize_agent.py         # 可视化工具
│
├── # 文档
├── AGENT_SYSTEM_README.md     # 完整系统文档
├── QUICK_START.md             # 快速开始指南
├── RESEARCH_HIGHLIGHTS.md     # 研究亮点
├── EXECUTION_CHECKLIST.md     # 执行清单
│
└── # 原有模块（复用）
    ├── pdf_parser.py          # PDF 解析
    ├── llm_client.py          # LLM 调用
    └── neurips_downloader.py  # 论文下载
```

## 🔬 Reflection 示例

```python
=== Iteration 1 ===
[Action] 提取数据集名称
[Result] 找到: ["ImageNet"]
[Reflection]
  质量评分: 0.4 (低)
  问题: "论文提到 'multiple benchmarks'，只找到1个"
  建议: "扩大搜索范围到全文"
  决策: needs_retry = True

=== Iteration 2 (重试) ===
[Action] 提取数据集名称（改进策略）
[Result] 找到: ["ImageNet", "CIFAR-10", "CustomBench"]
[Reflection]
  质量评分: 0.85 (高)
  决策: 继续下一步
```

## 📈 实验结果

基于 NeurIPS 2024 论文的测试结果：

| 指标 | Workflow | Agent (无反思) | Agent (有反思) |
|------|----------|----------------|----------------|
| 数据集提取数 | 15 | 17 (+13%) | 20 (+33%) |
| 平均质量 | N/A | 0.72 | 0.85 |
| 重试次数 | 0 | 5 | 8 |
| 自我修正成功率 | N/A | 60% | 87.5% |

## 📚 文档

- **[完整系统文档](AGENT_SYSTEM_README.md)** - 详细的架构和设计说明
- **[快速开始](QUICK_START.md)** - 使用指南和示例
- **[研究亮点](RESEARCH_HIGHLIGHTS.md)** - 论文写作要点
- **[执行清单](EXECUTION_CHECKLIST.md)** - 逐步执行指南

## 🎓 学术贡献

1. **系统设计**：完整的 ReAct + Reflection 架构实现
2. **反思机制**：多维度、两级反思策略
3. **可控性研究**：透明决策、参数控制、约束注入
4. **实验验证**：真实任务上的有效性验证

## 🔧 配置

### 调整 Agent 参数

```python
miner = AgentDatasetMiner(
    enable_llm_reflection=True,  # 启用/禁用 LLM 反思
    max_retries=2,                # 最大重试次数
)
```

### 调整质量阈值

```python
# 在 reflection_engine.py 中修改
def _should_retry(self, result, quality_score, issues):
    if quality_score < 0.6:  # 调整这个阈值
        return True
```

## 📊 可视化

```bash
# 生成可视化图表
python3 visualize_agent.py

# 查看：
# - quality_dist.png (质量分布)
# - action_performance.png (动作性能)
# - reflection_impact.png (反思影响)
```

## 🤝 贡献

欢迎提出 Issues 和 Pull Requests！

## 📄 许可证

MIT License

## 📧 联系

如有问题或建议，欢迎通过 Issues 联系。

---

**⭐ 如果这个项目对你有帮助，请给一个 Star！**
