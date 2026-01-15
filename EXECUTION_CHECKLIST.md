# 🚀 执行清单

## 第一步：验证系统完整性

### 1.1 检查文件

```bash
cd /Users/bytedance/Desktop/paper_agent/dataset_miner

# 核心Agent文件
ls -lh agent_*.py memory_system.py reflection_engine.py tool_manager.py

# 应该看到:
# agent_core.py (8.1K)
# agent_controller.py (17K)
# memory_system.py (11K)
# reflection_engine.py (15K)
# tool_manager.py (14K)
```

### 1.2 检查依赖

```bash
# 检查Python版本（需要3.8+）
python3 --version

# 检查必要的包
python3 -c "import openai, fitz, requests, pandas; print('依赖OK')"

# 如果缺少包：
pip3 install openai pymupdf requests pandas matplotlib beautifulsoup4
```

---

## 第二步：快速测试（5分钟）

### 2.1 测试原始Workflow（对照组）

```bash
# 先备份原有配置
cp main_neurips.py main_neurips.py.backup

# 编辑 main_neurips.py，在 run() 方法中添加 max_papers 参数支持
# 或者直接运行（会处理所有论文）

# 测试：只处理少量论文
python3 -c "
from main_neurips import NeurIPSDatasetMiner
miner = NeurIPSDatasetMiner(output_file='outputs/test_workflow.jsonl')
# 注意：可能需要修改 run() 方法支持 max_papers
"
```

### 2.2 测试Agent系统

```bash
# 测试：处理3篇论文
python3 main_agent.py

# 预期输出:
# - outputs/dataset_agent_results.jsonl
# - dataset_miner_agent.log
# - memory/long_term_memory.jsonl

# 查看日志中的决策过程
tail -20 dataset_miner_agent.log
```

### 2.3 验证输出

```bash
# 检查是否生成了结果文件
ls -lh outputs/dataset_agent_results.jsonl

# 查看提取的数据集数量
wc -l outputs/dataset_agent_results.jsonl

# 查看第一个结果
head -1 outputs/dataset_agent_results.jsonl | python3 -m json.tool
```

---

## 第三步：查看Agent决策过程

### 3.1 实时监控

```bash
# 终端1：运行Agent
python3 main_agent.py

# 终端2：实时查看决策
tail -f dataset_miner_agent.log | grep -E "\[观察\]|\[推理\]|\[动作\]|\[反思\]"
```

### 3.2 查看反思详情

```bash
# 过滤反思日志
grep "\[反思\]" dataset_miner_agent.log

# 应该看到类似:
# [反思] 质量=0.85, 进度=0.50
# [洞察] 成功提取了3个数据集
```

### 3.3 查看记忆统计

```bash
# 查看日志末尾的统计信息
tail -50 dataset_miner_agent.log | grep -A 10 "Agent 记忆统计"

# 应该看到:
# [Agent 记忆统计]
#   总经验数: 24
#   成功率: 87.50%
#   平均质量: 0.78
```

---

## 第四步：运行对比实验

### 4.1 运行实验框架

```bash
# 完整对比实验（3篇论文测试）
python3 experiment_framework.py

# 预期耗时：10-15分钟（取决于网络和LLM速度）
```

### 4.2 查看实验结果

```bash
# 查看生成的文件
ls -lh experiments/

# 应该有:
# - workflow_results.jsonl
# - agent_results_no_reflection.jsonl
# - agent_results_with_reflection.jsonl
# - experiment_results.json
# - experiment_report.txt

# 查看对比报告
cat experiments/experiment_report.txt
```

### 4.3 分析结果

```bash
# 比较提取的数据集数量
echo "Workflow:"
wc -l experiments/workflow_results.jsonl

echo "Agent (无反思):"
wc -l experiments/agent_results_no_reflection.jsonl

echo "Agent (有反思):"
wc -l experiments/agent_results_with_reflection.jsonl
```

---

## 第五步：可视化分析

### 5.1 生成可视化

```bash
# 创建可视化目录
mkdir -p visualizations

# 运行可视化脚本
python3 visualize_agent.py

# 查看生成的图表
ls -lh visualizations/

# 应该有:
# - quality_dist.png (质量分布)
# - action_performance.png (动作性能)
# - reflection_impact.png (反思影响)
# - agent_summary.txt (摘要报告)
```

### 5.2 查看图表

```bash
# macOS
open visualizations/*.png

# Linux
xdg-open visualizations/*.png

# 或者用你喜欢的图片查看器
```

### 5.3 阅读摘要

```bash
cat visualizations/agent_summary.txt
```

---

## 第六步：调整和优化

### 6.1 调整反思阈值

编辑 `reflection_engine.py`:

```python
def _should_retry(self, result, quality_score, issues):
    # 原始: 质量<0.3 时重试
    if quality_score < 0.3:
        return True

    # 修改为: 质量<0.6 时重试（更严格）
    if quality_score < 0.6:
        return True
    return False
```

### 6.2 调整Agent参数

编辑 `main_agent.py` 的 `main()` 函数:

```python
def main():
    miner = AgentDatasetMiner(
        output_file="outputs/dataset_agent_results.jsonl",
        enable_llm_reflection=True,  # 改为 False 禁用LLM反思
        max_retries=2,                # 改为 5 允许更多重试
    )

    # 调整处理的论文数量
    miner.run(year=2024, max_papers=10)  # 从 3 改为 10
```

### 6.3 添加自定义约束

在 `agent_controller.py` 中添加:

```python
class ConstrainedAgent(AgentController):
    """带约束的Agent"""

    def _adjust(self, reflection, plan, context, result):
        # 强制要求：至少提取2个数据集
        if result.metadata.get("datasets_found", 0) < 2:
            logger.info("[约束] 数据集数量不足，重试")
            reflection.needs_retry = True

        return super()._adjust(reflection, plan, context, result)
```

然后在 `main_agent.py` 中使用:

```python
from agent_controller import ConstrainedAgent

# 在 AgentDatasetMiner.__init__ 中:
self.agent = ConstrainedAgent(...)  # 而不是 AgentController
```

---

## 第七步：扩展实验

### 7.1 增加论文数量

```bash
# 处理50篇论文
python3 -c "
from main_agent import AgentDatasetMiner
miner = AgentDatasetMiner()
miner.run(year=2024, max_papers=50)
"
```

### 7.2 测试不同年份

```bash
# 测试2023年
python3 -c "
from main_agent import AgentDatasetMiner
miner = AgentDatasetMiner(output_file='outputs/neurips_2023_agent.jsonl')
miner.run(year=2023, max_papers=10)
"
```

### 7.3 测试其他会议

如果要测试ICML或ICLR，需要创建对应的downloader（已有icml_downloader.py）:

```python
# main_agent_icml.py
from main_agent import AgentDatasetMiner
from icml_downloader import ICMLDownloader

# 修改 AgentDatasetMiner.run() 中的 downloader
# downloader = ICMLDownloader(year=year, temp_dir="temp")
```

---

## 第八步：数据分析

### 8.1 导出决策轨迹

在 `main_agent.py` 末尾添加:

```python
def export_decision_trace(agent, output_file="decision_trace.json"):
    """导出完整的决策轨迹"""
    import json

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

    print(f"决策轨迹已导出到: {output_file}")

# 在 main() 函数末尾调用
if __name__ == "__main__":
    main()
    # 如果已运行过，可以这样导出
    # export_decision_trace(miner.agent, "trace.json")
```

### 8.2 分析反思模式

```bash
# 提取所有反思洞察
python3 -c "
import json

insights = []
with open('memory/long_term_memory.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)
        exp = record['experience']
        insights.extend(exp['reflection']['insights'])

# 统计最常见的洞察
from collections import Counter
common = Counter(insights).most_common(10)

print('最常见的10个洞察:')
for insight, count in common:
    print(f'  {count}次: {insight}')
"
```

### 8.3 对比数据集提取效果

```bash
# 提取所有数据集名称进行对比
python3 -c "
import json

def extract_datasets(file):
    datasets = set()
    with open(file, 'r') as f:
        for line in f:
            record = json.loads(line)
            datasets.add(record['name'])
    return datasets

workflow_datasets = extract_datasets('outputs/test_workflow.jsonl')
agent_datasets = extract_datasets('outputs/dataset_agent_results.jsonl')

print(f'Workflow提取: {len(workflow_datasets)} 个')
print(f'Agent提取: {len(agent_datasets)} 个')
print(f'Agent多提取: {agent_datasets - workflow_datasets}')
print(f'Agent漏提取: {workflow_datasets - agent_datasets}')
"
```

---

## 第九步：论文撰写

### 9.1 收集实验数据

创建 `paper_data/` 目录：

```bash
mkdir -p paper_data

# 复制关键结果
cp experiments/experiment_report.txt paper_data/
cp visualizations/*.png paper_data/
cp visualizations/agent_summary.txt paper_data/

# 导出决策轨迹（用于案例分析）
python3 -c "
from main_agent import AgentDatasetMiner, export_decision_trace
# 假设已经运行过
# export_decision_trace(miner.agent, 'paper_data/decision_trace.json')
"
```

### 9.2 选择典型案例

```bash
# 从日志中提取有趣的案例
grep -B 5 -A 5 "需要重试" dataset_miner_agent.log > paper_data/retry_cases.txt
grep -B 5 -A 5 "质量.*0\.[89]" dataset_miner_agent.log > paper_data/high_quality_cases.txt
```

### 9.3 生成表格数据

创建 `generate_tables.py`:

```python
import json
import pandas as pd

# 读取实验结果
with open('experiments/experiment_results.json', 'r') as f:
    results = json.load(f)

# 生成表格
df = pd.DataFrame([
    {
        '系统': res['system_name'],
        '数据集数': res['total_datasets_extracted'],
        '平均质量': f"{res['average_quality_score']:.2f}",
        '反思次数': res['reflection_count'],
        '重试次数': res['retry_count'],
        '总耗时(s)': f"{res['total_time']:.1f}",
    }
    for res in results.values()
])

# 导出LaTeX表格
print(df.to_latex(index=False))

# 保存CSV
df.to_csv('paper_data/results_table.csv', index=False)
```

运行:
```bash
python3 generate_tables.py > paper_data/results_table.tex
```

---

## 第十步：问题排查

### 常见问题

#### Q1: 找不到论文

**症状**: "未找到任何论文"

**原因**: 2025年的论文可能还未发布

**解决**:
```python
# 改用2024年
miner.run(year=2024, max_papers=10)
```

#### Q2: LLM调用失败

**症状**: "LLM调用失败: ..."

**原因**: API key无效或网络问题

**解决**:
```bash
# 检查API key
grep "api_key" llm_client.py

# 测试LLM连接
python3 -c "
from llm_client import call_gpt4o_text
try:
    resp = call_gpt4o_text('Hello')
    print('LLM连接正常:', resp[:50])
except Exception as e:
    print('LLM连接失败:', e)
"
```

#### Q3: 内存不足

**症状**: MemoryError

**原因**: 处理过多论文

**解决**:
```python
# 减少论文数量
miner.run(year=2024, max_papers=5)  # 从50改为5

# 或者清理短期记忆
agent.memory.clear_short_term()
```

#### Q4: PDF解析失败

**症状**: "PDF解析失败"

**原因**: PDF文件损坏或格式不支持

**解决**: Agent会自动跳过失败的论文，查看日志了解详情

---

## 🎉 完成检查清单

- [ ] 系统文件完整
- [ ] 依赖包已安装
- [ ] 快速测试通过
- [ ] 能看到Agent决策过程
- [ ] 对比实验完成
- [ ] 可视化生成成功
- [ ] 理解了如何调整参数
- [ ] 扩展实验运行成功
- [ ] 数据分析完成
- [ ] 论文数据已收集

---

## 📚 参考文档

1. **完整文档**: `AGENT_SYSTEM_README.md`
2. **快速开始**: `QUICK_START.md`
3. **研究亮点**: `RESEARCH_HIGHLIGHTS.md`
4. **项目总结**: `PROJECT_SUMMARY.md`
5. **本清单**: `EXECUTION_CHECKLIST.md`

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件: `dataset_miner_agent.log`
2. 检查错误信息: 通常有详细的 traceback
3. 查阅相关文档
4. 检查代码注释

---

**祝实验顺利！** 🚀

记住：先从小规模测试开始（3-5篇论文），确认系统工作正常后，再扩展到更大规模的实验。
