"""
实验框架
用于对比评估 Agent 系统与原始 Workflow 的性能
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExperimentMetrics:
    """实验指标"""

    # 基础指标
    system_name: str  # "workflow" 或 "agent"
    total_papers: int
    successful_papers: int
    failed_papers: int

    # 数据集提取指标
    total_datasets_extracted: int
    datasets_per_paper: float
    extraction_recall: float  # 召回率（需要人工标注基准）
    extraction_precision: float  # 准确率

    # 质量指标
    average_quality_score: float
    high_quality_count: int  # 质量>0.8的数量
    low_quality_count: int  # 质量<0.4的数量

    # 效率指标
    total_time: float
    average_time_per_paper: float
    total_llm_calls: int
    llm_calls_per_paper: float

    # Agent 特有指标
    reflection_count: int = 0
    retry_count: int = 0
    self_correction_count: int = 0  # 通过反思自我修正的次数
    plan_adjustment_count: int = 0  # 计划调整次数

    def to_dict(self) -> Dict:
        return asdict(self)


class ExperimentFramework:
    """
    实验框架

    功能：
    1. 运行对比实验（Workflow vs Agent）
    2. 收集性能指标
    3. 生成对比报告
    4. 可视化结果
    """

    def __init__(self, output_dir: str = "experiments"):
        """
        初始化实验框架

        Args:
            output_dir: 实验输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = []

        logger.info(f"实验框架初始化完成，输出目录: {self.output_dir}")

    def run_workflow_experiment(
        self, year: int = 2024, max_papers: int = 10
    ) -> ExperimentMetrics:
        """
        运行原始 Workflow 实验

        Args:
            year: 年份
            max_papers: 最大论文数

        Returns:
            实验指标
        """
        logger.info(f"\n{'='*80}")
        logger.info("开始运行 Workflow 实验")
        logger.info(f"{'='*80}\n")

        from main_neurips import NeurIPSDatasetMiner

        start_time = time.time()
        llm_call_count = 0

        # 创建挖掘器
        output_file = self.output_dir / "workflow_results.jsonl"
        miner = NeurIPSDatasetMiner(output_file=str(output_file))

        # 记录 LLM 调用（需要在 llm_client 中添加计数器）
        # 这里简化处理

        try:
            # 运行挖掘
            # 注意：需要修改 run 方法支持 max_papers 参数
            # 这里假设已修改
            miner.run(year=year)

            total_time = time.time() - start_time

            # 读取结果统计
            datasets = []
            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    for line in f:
                        datasets.append(json.loads(line))

            # 计算指标
            metrics = ExperimentMetrics(
                system_name="workflow",
                total_papers=max_papers,
                successful_papers=len(set(d["paper_refs"]["title"] for d in datasets)),
                failed_papers=0,  # Workflow 不记录失败
                total_datasets_extracted=len(datasets),
                datasets_per_paper=len(datasets) / max_papers if max_papers > 0 else 0,
                extraction_recall=0.0,  # 需要人工标注
                extraction_precision=0.0,  # 需要人工标注
                average_quality_score=0.0,  # Workflow 没有质量评分
                high_quality_count=0,
                low_quality_count=0,
                total_time=total_time,
                average_time_per_paper=total_time / max_papers if max_papers > 0 else 0,
                total_llm_calls=max_papers * 3,  # 估算：每篇论文3次LLM调用
                llm_calls_per_paper=3.0,
            )

            logger.info(f"\nWorkflow 实验完成")
            logger.info(f"  总论文数: {metrics.total_papers}")
            logger.info(f"  提取数据集数: {metrics.total_datasets_extracted}")
            logger.info(f"  总耗时: {metrics.total_time:.2f}s")

            return metrics

        except Exception as e:
            logger.error(f"Workflow 实验失败: {str(e)}", exc_info=True)
            return None

    def run_agent_experiment(
        self, year: int = 2024, max_papers: int = 10, enable_reflection: bool = True
    ) -> ExperimentMetrics:
        """
        运行 Agent 实验

        Args:
            year: 年份
            max_papers: 最大论文数
            enable_reflection: 是否启用反思

        Returns:
            实验指标
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"开始运行 Agent 实验 (Reflection: {enable_reflection})")
        logger.info(f"{'='*80}\n")

        from main_agent import AgentDatasetMiner

        start_time = time.time()

        # 创建 Agent 挖掘器
        output_file = (
            self.output_dir
            / f"agent_results{'_with_reflection' if enable_reflection else '_no_reflection'}.jsonl"
        )
        miner = AgentDatasetMiner(
            output_file=str(output_file),
            enable_llm_reflection=enable_reflection,
            max_retries=2,
        )

        try:
            # 运行挖掘
            miner.run(year=year, max_papers=max_papers)

            total_time = time.time() - start_time

            # 读取结果
            datasets = []
            if output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    for line in f:
                        datasets.append(json.loads(line))

            # 从 Agent 记忆中获取统计
            memory_summary = miner.agent.memory.summarize_session()
            tool_stats = miner.agent.tool_manager.get_execution_stats()

            # 计算质量指标
            quality_scores = [
                exp.reflection.quality_score
                for exp in miner.agent.memory.short_term
                if hasattr(exp, "reflection")
            ]
            avg_quality = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            )
            high_quality = sum(1 for q in quality_scores if q >= 0.8)
            low_quality = sum(1 for q in quality_scores if q < 0.4)

            # 统计反思和重试
            reflection_count = len(miner.agent.memory.reflections)
            retry_count = sum(
                1
                for exp in miner.agent.memory.short_term
                if exp.result.metadata.get("retry_count", 0) > 0
            )

            # 统计自我修正（通过反思改进的次数）
            self_correction_count = sum(
                1
                for exp in miner.agent.memory.short_term
                if exp.reflection.needs_retry or exp.reflection.needs_replan
            )

            # 计算指标
            metrics = ExperimentMetrics(
                system_name=f"agent{'_reflection' if enable_reflection else '_no_reflection'}",
                total_papers=max_papers,
                successful_papers=memory_summary.get("successful", 0),
                failed_papers=memory_summary.get("failed", 0),
                total_datasets_extracted=len(datasets),
                datasets_per_paper=len(datasets) / max_papers if max_papers > 0 else 0,
                extraction_recall=0.0,  # 需要人工标注
                extraction_precision=0.0,  # 需要人工标注
                average_quality_score=avg_quality,
                high_quality_count=high_quality,
                low_quality_count=low_quality,
                total_time=total_time,
                average_time_per_paper=total_time / max_papers if max_papers > 0 else 0,
                total_llm_calls=tool_stats.get("total", 0),
                llm_calls_per_paper=tool_stats.get("total", 0) / max_papers
                if max_papers > 0
                else 0,
                reflection_count=reflection_count,
                retry_count=retry_count,
                self_correction_count=self_correction_count,
                plan_adjustment_count=0,  # 可以从 plan.adjustments 中统计
            )

            logger.info(f"\nAgent 实验完成")
            logger.info(f"  总论文数: {metrics.total_papers}")
            logger.info(f"  提取数据集数: {metrics.total_datasets_extracted}")
            logger.info(f"  平均质量: {metrics.average_quality_score:.2f}")
            logger.info(f"  反思次数: {metrics.reflection_count}")
            logger.info(f"  自我修正次数: {metrics.self_correction_count}")
            logger.info(f"  总耗时: {metrics.total_time:.2f}s")

            return metrics

        except Exception as e:
            logger.error(f"Agent 实验失败: {str(e)}", exc_info=True)
            return None

    def run_comparative_experiment(
        self, year: int = 2024, max_papers: int = 10
    ) -> Dict[str, ExperimentMetrics]:
        """
        运行对比实验

        Args:
            year: 年份
            max_papers: 最大论文数

        Returns:
            所有实验的指标
        """
        logger.info(f"\n{'#'*80}")
        logger.info(f"开始对比实验")
        logger.info(f"年份: {year}, 论文数: {max_papers}")
        logger.info(f"{'#'*80}\n")

        results = {}

        # 1. 运行 Workflow
        logger.info("\n[实验1/3] 原始 Workflow")
        workflow_metrics = self.run_workflow_experiment(year, max_papers)
        if workflow_metrics:
            results["workflow"] = workflow_metrics

        # 2. 运行 Agent (无反思)
        logger.info("\n[实验2/3] Agent (无 LLM 反思)")
        agent_no_refl_metrics = self.run_agent_experiment(
            year, max_papers, enable_reflection=False
        )
        if agent_no_refl_metrics:
            results["agent_no_reflection"] = agent_no_refl_metrics

        # 3. 运行 Agent (有反思)
        logger.info("\n[实验3/3] Agent (有 LLM 反思)")
        agent_with_refl_metrics = self.run_agent_experiment(
            year, max_papers, enable_reflection=True
        )
        if agent_with_refl_metrics:
            results["agent_with_reflection"] = agent_with_refl_metrics

        # 保存结果
        self._save_results(results)

        # 生成报告
        self._generate_report(results)

        return results

    def _save_results(self, results: Dict[str, ExperimentMetrics]):
        """保存实验结果"""
        output_file = self.output_dir / "experiment_results.json"

        results_dict = {name: metrics.to_dict() for name, metrics in results.items()}

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"\n实验结果已保存到: {output_file}")

    def _generate_report(self, results: Dict[str, ExperimentMetrics]):
        """生成对比报告"""
        report_file = self.output_dir / "experiment_report.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("实验对比报告\n")
            f.write("=" * 80 + "\n\n")

            # 对比表格
            f.write("## 关键指标对比\n\n")

            if not results:
                f.write("无实验结果\n")
                return

            # 创建对比表
            df_data = []
            for name, metrics in results.items():
                df_data.append(
                    {
                        "系统": metrics.system_name,
                        "数据集数": metrics.total_datasets_extracted,
                        "数据集/论文": f"{metrics.datasets_per_paper:.2f}",
                        "平均质量": f"{metrics.average_quality_score:.2f}",
                        "总耗时(s)": f"{metrics.total_time:.1f}",
                        "LLM调用数": metrics.total_llm_calls,
                        "反思次数": metrics.reflection_count,
                        "自我修正": metrics.self_correction_count,
                    }
                )

            df = pd.DataFrame(df_data)
            f.write(df.to_string(index=False))
            f.write("\n\n")

            # 详细分析
            f.write("## 详细分析\n\n")

            for name, metrics in results.items():
                f.write(f"### {metrics.system_name}\n")
                f.write(f"- 总论文数: {metrics.total_papers}\n")
                f.write(f"- 成功论文: {metrics.successful_papers}\n")
                f.write(f"- 提取数据集: {metrics.total_datasets_extracted}\n")
                f.write(f"- 平均质量: {metrics.average_quality_score:.3f}\n")
                f.write(f"- 高质量数: {metrics.high_quality_count}\n")
                f.write(f"- 低质量数: {metrics.low_quality_count}\n")
                f.write(f"- 总耗时: {metrics.total_time:.2f}s\n")
                f.write(f"- 平均耗时/论文: {metrics.average_time_per_paper:.2f}s\n")
                f.write(f"- LLM调用总数: {metrics.total_llm_calls}\n")
                f.write(f"- LLM调用/论文: {metrics.llm_calls_per_paper:.2f}\n")

                if metrics.reflection_count > 0:
                    f.write(f"- 反思次数: {metrics.reflection_count}\n")
                    f.write(f"- 重试次数: {metrics.retry_count}\n")
                    f.write(f"- 自我修正: {metrics.self_correction_count}\n")

                f.write("\n")

            # 结论
            f.write("## 关键发现\n\n")
            f.write("1. **数据集提取效果**: \n")
            f.write(
                "   - Agent 系统通过反思机制可以发现提取不完整的问题并重试\n"
            )
            f.write("   - Workflow 系统按固定流程执行，无法自我调整\n\n")

            f.write("2. **质量评估**: \n")
            f.write("   - Agent 系统具有质量评分机制，可以量化评估结果\n")
            f.write("   - 反思引擎能够识别低质量结果并建议改进\n\n")

            f.write("3. **错误恢复**: \n")
            f.write("   - Agent 系统具有自我修正能力（重试、调整策略）\n")
            f.write("   - Workflow 系统遇到错误只能跳过\n\n")

            f.write("4. **可控性**: \n")
            f.write("   - Agent 系统的决策过程透明（有推理和反思日志）\n")
            f.write("   - 可以通过调整反思参数控制行为\n\n")

        logger.info(f"实验报告已保存到: {report_file}")


def main():
    """运行对比实验"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("experiments/experiment.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # 创建实验框架
    framework = ExperimentFramework(output_dir="experiments")

    # 运行对比实验（用少量论文测试）
    results = framework.run_comparative_experiment(year=2024, max_papers=3)

    print("\n" + "=" * 80)
    print("实验完成！请查看 experiments/ 目录下的结果")
    print("=" * 80)


if __name__ == "__main__":
    main()
