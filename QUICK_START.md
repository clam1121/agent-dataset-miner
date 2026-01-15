# 🚀 快速开始指南

## 目录

1. [系统概述](#系统概述)
2. [文件结构](#文件结构)
3. [运行示例](#运行示例)
4. [关键概念](#关键概念)
5. [调试和监控](#调试和监控)

---

## 系统概述

你现在有两个版本的数据集挖掘器：

1. **原始 Workflow** (`main_neurips.py`) - 固定流程，无反思
2. **Agent 系统** (`main_agent.py`) - 智能决策，有反思和学习能力

---

## 文件结构

```
dataset_miner/
├── # 核心 Agent 组件
├── agent_core.py              # 数据结构定义
├── agent_controller.py        # Agent 控制器 (ReAct 循环)
├── memory_system.py           # 记忆系统
├── reflection_engine.py       # 反思引擎
├── tool_manager.py            # 工具管理器
│
├── # 主程序
├── main_neurips.py            # 原始 Workflow
├── main_agent.py              # Agent 系统
├── experiment_framework.py    # 对比实验框架
│
├── # 工具模块（共用）
├── pdf_parser.py              # PDF 解析
├── llm_client.py              # LLM 调用
├── prompts.py                 # 提示词模板
├── neurips_downloader.py      # 论文下载器
│
└── # 文档
    ├── AGENT_SYSTEM_README.md # 完整文档
    └── QUICK_START.md         # 本文件
```

---

## 运行示例

### 1️⃣ 运行原始 Workflow（作为对照）

```bash
cd /Users/bytedance/Desktop/paper_agent/dataset_miner

# 测试：处理2024年的前3篇论文
python3 main_neurips.py
```

**输出**:
- 文件: `outputs/dataset_neurips_results.jsonl`
- 日志: `dataset_miner_neurips.log`

---

### 2️⃣ 运行 Agent 系统

```bash
# 测试：处理前3篇论文
python3 main_agent.py
```

**输出**:
- 文件: `outputs/dataset_agent_results.jsonl`
- 日志: `dataset_miner_agent.log`
- 记忆: `memory/long_term_memory.jsonl`

**查看 Agent 决策过程**:
```bash
# 查看日志中的反思和决策
tail -f dataset_miner_agent.log | grep -E "\[观察\]|\[推理\]|\[动作\]|\[反思\]"
```

---

### 3️⃣ 运行对比实验

```bash
# 完整对比：Workflow vs Agent(无反思) vs Agent(有反思)
python3 experiment_framework.py
```

**输出**:
- `experiments/workflow_results.jsonl`
- `experiments/agent_results_no_reflection.jsonl`
- `experiments/agent_results_with_reflection.jsonl`
- `experiments/experiment_report.txt` - 对比报告
- `experiments/experiment.log`

**查看报告**:
```bash
cat experiments/experiment_report.txt
```

---

## 关键概念

### 1. ReAct 循环

Agent 的核心决策循环：

```
loop:
  Observe  → 观察当前状态
  Think    → 推理下一步
  Act      → 执行动作
  Reflect  → 反思结果
  Learn    → 存储经验
  Adjust   → 调整计划
```

**示例日志**:
```
============================================================
[观察] 当前步骤: extract_datasets
[推理] 目标是提取论文中的数据集信息...
[动作] extract_datasets
[结果] ✓ 成功 (耗时: 2.34s)
[反思] 质量=0.85, 进度=0.50
[洞察] 成功提取了3个数据集
============================================================
```

---

### 2. Reflection（反思）

Agent 评估自己行为的机制：

**基础反思** (总是执行):
- 快速，基于规则
- 评估质量、识别问题
- 决定是否重试

**LLM 反思** (可选):
- 深入，使用 LLM
- 生成洞察和改进建议
- 更慢但更智能

**控制反思**:
```python
# 在 main_agent.py 中修改
miner = AgentDatasetMiner(
    enable_llm_reflection=True,  # True=深度反思, False=仅基础反思
    max_retries=2                 # 最大重试次数
)
```

---

### 3. Memory（记忆）

Agent 如何学习和改进：

**短期记忆**:
- 当前会话的经验
- 用于快速检索

**长期记忆**:
- 重要经验的持久化
- 跨会话使用

**查看记忆**:
```python
# 在代码中查看
memory_summary = agent.memory.summarize_session()
print(memory_summary)

# 输出:
# {
#   "total_experiences": 24,
#   "successful": 20,
#   "failed": 4,
#   "success_rate": 0.833,
#   "average_quality_score": 0.78,
#   "recent_insights": ["洞察1", "洞察2", "洞察3"]
# }
```

---

### 4. 质量评分

Agent 如何评估结果质量：

| 评分 | 含义 | Agent 行为 |
|------|------|-----------|
| 0.8-1.0 | 高质量 | 继续下一步 |
| 0.6-0.8 | 良好 | 继续，但记录改进建议 |
| 0.4-0.6 | 一般 | 考虑重试 |
| 0.0-0.4 | 低质量 | 强制重试或重新规划 |

---

## 调试和监控

### 查看实时决策过程

```bash
# 终端1: 运行 Agent
python3 main_agent.py

# 终端2: 实时查看反思
tail -f dataset_miner_agent.log | grep "\[反思\]"
```

---

### 修改反思阈值

```python
# 在 reflection_engine.py 中修改 _should_retry()
def _should_retry(self, result, quality_score, issues):
    # 原始: 质量<0.3 时重试
    if quality_score < 0.3:
        return True

    # 修改为: 质量<0.6 时重试（更严格）
    if quality_score < 0.6:
        return True
```

---

### 添加自定义约束

```python
# 在 agent_controller.py 中添加
class ConstrainedAgent(AgentController):
    def _adjust(self, reflection, plan, context, result):
        # 强制要求：至少提取2个数据集
        if result.metadata.get("datasets_found", 0) < 2:
            logger.info("[约束] 数据集数量不足，重试")
            reflection.needs_retry = True

        return super()._adjust(reflection, plan, context, result)
```

---

### 导出决策轨迹

```python
# 添加到 main_agent.py
def export_decision_trace(agent, output_file="decision_trace.json"):
    """导出完整的决策轨迹"""
    trace = []

    for exp in agent.memory.short_term:
        trace.append({
            "action": exp.action.action_type.value,
            "reasoning": exp.action.reasoning,
            "result_success": exp.result.success,
            "quality_score": exp.reflection.quality_score,
            "insights": exp.reflection.insights,
            "needs_retry": exp.reflection.needs_retry
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)

    logger.info(f"决策轨迹已导出到: {output_file}")

# 使用
export_decision_trace(miner.agent, "trace.json")
```

---

## 常见问题

### Q1: 如何只处理几篇论文进行测试？

```python
# 在 main_agent.py 的 main() 函数中
miner.run(year=2024, max_papers=3)  # 只处理3篇
```

### Q2: 如何禁用 LLM 反思以节省成本？

```python
miner = AgentDatasetMiner(
    enable_llm_reflection=False,  # 禁用 LLM 反思
    max_retries=1
)
```

### Q3: 如何查看 Agent 学到了什么？

```python
# 查看长期记忆
agent.memory.save_to_disk()  # 保存到 memory/long_term_memory.jsonl

# 读取并分析
import json
with open("memory/long_term_memory.jsonl") as f:
    for line in f:
        record = json.loads(line)
        print(f"模式: {record['pattern']}")
        print(f"经验: {record['experience']['reflection']['insights']}")
```

### Q4: 如何对比两个系统的输出？

```bash
# 提取数据集名称进行对比
cat outputs/dataset_neurips_results.jsonl | jq -r '.name' | sort > workflow_datasets.txt
cat outputs/dataset_agent_results.jsonl | jq -r '.name' | sort > agent_datasets.txt

# 查看差异
diff workflow_datasets.txt agent_datasets.txt
```

---

## 下一步

1. **运行完整实验** (更多论文):
   ```python
   miner.run(year=2024, max_papers=50)
   ```

2. **分析 Reflection 效果**:
   - 统计重试次数
   - 对比有/无反思的质量差异
   - 分析自我修正案例

3. **撰写论文**:
   - 使用 `AGENT_SYSTEM_README.md` 作为参考
   - 使用 `experiment_report.txt` 作为实验结果
   - 重点强调 Reflection 在可控性中的作用

---

## 技术支持

遇到问题？检查以下内容：

1. **日志文件**: `dataset_miner_agent.log`
2. **错误信息**: 通常会有详细的 traceback
3. **LLM 调用**: 确保 API key 有效
4. **依赖包**: `pip install -r requirements.txt`

---

**祝实验顺利！** 🎉

如有疑问，请查阅 `AGENT_SYSTEM_README.md` 获取详细信息。
