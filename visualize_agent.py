"""
Agent 决策过程可视化工具
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)


class AgentVisualizer:
    """Agent 可视化工具"""

    def __init__(self, memory_file: str = "memory/long_term_memory.jsonl"):
        """
        初始化可视化工具

        Args:
            memory_file: 记忆文件路径
        """
        self.memory_file = Path(memory_file)
        self.experiences = []

        if self.memory_file.exists():
            self._load_experiences()

    def _load_experiences(self):
        """加载经验数据"""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    self.experiences.append(record)

            logger.info(f"加载了 {len(self.experiences)} 条经验")
        except Exception as e:
            logger.error(f"加载经验失败: {str(e)}")

    def visualize_quality_distribution(self, output_file: str = "quality_dist.png"):
        """
        可视化质量评分分布

        Args:
            output_file: 输出图片文件
        """
        if not self.experiences:
            logger.warning("没有经验数据")
            return

        # 提取质量评分
        quality_scores = []
        for exp in self.experiences:
            score = exp["experience"]["reflection"]["quality_score"]
            quality_scores.append(score)

        # 绘制直方图
        plt.figure(figsize=(10, 6))
        plt.hist(quality_scores, bins=20, edgecolor="black", alpha=0.7)
        plt.xlabel("质量评分", fontsize=12)
        plt.ylabel("频数", fontsize=12)
        plt.title("Agent 质量评分分布", fontsize=14, fontweight="bold")
        plt.axvline(
            sum(quality_scores) / len(quality_scores),
            color="red",
            linestyle="--",
            label=f"平均值: {sum(quality_scores)/len(quality_scores):.2f}",
        )
        plt.legend()
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()

        logger.info(f"质量分布图已保存到: {output_file}")

    def visualize_action_performance(
        self, output_file: str = "action_performance.png"
    ):
        """
        可视化不同动作的性能

        Args:
            output_file: 输出图片文件
        """
        if not self.experiences:
            logger.warning("没有经验数据")
            return

        # 统计每种动作的性能
        action_stats = {}

        for exp in self.experiences:
            action_type = exp["experience"]["action"]["action_type"]
            quality_score = exp["experience"]["reflection"]["quality_score"]
            is_successful = exp["experience"]["is_successful"]

            if action_type not in action_stats:
                action_stats[action_type] = {
                    "quality_scores": [],
                    "success_count": 0,
                    "total_count": 0,
                }

            action_stats[action_type]["quality_scores"].append(quality_score)
            action_stats[action_type]["total_count"] += 1
            if is_successful:
                action_stats[action_type]["success_count"] += 1

        # 计算平均质量和成功率
        action_names = []
        avg_qualities = []
        success_rates = []

        for action, stats in action_stats.items():
            action_names.append(action)
            avg_quality = sum(stats["quality_scores"]) / len(stats["quality_scores"])
            avg_qualities.append(avg_quality)
            success_rate = stats["success_count"] / stats["total_count"]
            success_rates.append(success_rate)

        # 绘制条形图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 平均质量
        ax1.bar(action_names, avg_qualities, color="skyblue", edgecolor="black")
        ax1.set_xlabel("动作类型", fontsize=12)
        ax1.set_ylabel("平均质量评分", fontsize=12)
        ax1.set_title("各动作的平均质量", fontsize=14, fontweight="bold")
        ax1.set_ylim(0, 1)
        ax1.grid(axis="y", alpha=0.3)
        ax1.tick_params(axis="x", rotation=45)

        # 成功率
        ax2.bar(action_names, success_rates, color="lightgreen", edgecolor="black")
        ax2.set_xlabel("动作类型", fontsize=12)
        ax2.set_ylabel("成功率", fontsize=12)
        ax2.set_title("各动作的成功率", fontsize=14, fontweight="bold")
        ax2.set_ylim(0, 1)
        ax2.grid(axis="y", alpha=0.3)
        ax2.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()

        logger.info(f"动作性能图已保存到: {output_file}")

    def visualize_reflection_impact(
        self, output_file: str = "reflection_impact.png"
    ):
        """
        可视化反思的影响

        Args:
            output_file: 输出图片文件
        """
        if not self.experiences:
            logger.warning("没有经验数据")
            return

        # 统计反思建议
        needs_retry_count = 0
        needs_replan_count = 0
        high_quality_count = 0
        low_quality_count = 0
        insights_count = 0

        for exp in self.experiences:
            reflection = exp["experience"]["reflection"]

            if reflection["needs_retry"]:
                needs_retry_count += 1
            if reflection["needs_replan"]:
                needs_replan_count += 1
            if reflection["quality_score"] >= 0.8:
                high_quality_count += 1
            if reflection["quality_score"] < 0.4:
                low_quality_count += 1
            insights_count += len(reflection["insights"])

        # 绘制饼图和条形图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 质量分布饼图
        quality_labels = ["高质量 (≥0.8)", "中质量", "低质量 (<0.4)"]
        quality_sizes = [
            high_quality_count,
            len(self.experiences) - high_quality_count - low_quality_count,
            low_quality_count,
        ]
        colors = ["#90EE90", "#FFD700", "#FF6B6B"]

        ax1.pie(
            quality_sizes,
            labels=quality_labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
        )
        ax1.set_title("质量分布", fontsize=14, fontweight="bold")

        # 反思建议条形图
        reflection_labels = ["需要重试", "需要重新规划", "总洞察数"]
        reflection_counts = [needs_retry_count, needs_replan_count, insights_count]

        ax2.bar(reflection_labels, reflection_counts, color="coral", edgecolor="black")
        ax2.set_ylabel("次数", fontsize=12)
        ax2.set_title("反思建议统计", fontsize=14, fontweight="bold")
        ax2.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.close()

        logger.info(f"反思影响图已保存到: {output_file}")

    def print_decision_trace(self, max_steps: int = 10):
        """
        打印决策轨迹

        Args:
            max_steps: 最多显示的步骤数
        """
        if not self.experiences:
            logger.warning("没有经验数据")
            return

        print("\n" + "=" * 80)
        print("Agent 决策轨迹")
        print("=" * 80)

        for i, exp in enumerate(self.experiences[:max_steps], 1):
            action = exp["experience"]["action"]
            result = exp["experience"]["result"]
            reflection = exp["experience"]["reflection"]

            print(f"\n步骤 {i}: {action['action_type']}")
            print(f"  推理: {action['reasoning']}")
            print(
                f"  结果: {'✓ 成功' if result['success'] else '✗ 失败'} "
                f"(耗时: {result['execution_time']:.2f}s)"
            )
            print(
                f"  反思: 质量={reflection['quality_score']:.2f}, "
                f"{reflection['success_assessment']}"
            )

            if reflection["insights"]:
                print(f"  洞察: {reflection['insights'][0]}")

            if reflection["needs_retry"]:
                print("  ⚠️  建议: 需要重试")

        if len(self.experiences) > max_steps:
            print(f"\n... 还有 {len(self.experiences) - max_steps} 个步骤")

        print("\n" + "=" * 80)

    def export_summary_report(self, output_file: str = "agent_summary.txt"):
        """
        导出摘要报告

        Args:
            output_file: 输出文件
        """
        if not self.experiences:
            logger.warning("没有经验数据")
            return

        # 统计信息
        total_experiences = len(self.experiences)
        successful = sum(
            1 for exp in self.experiences if exp["experience"]["is_successful"]
        )
        failed = total_experiences - successful

        quality_scores = [
            exp["experience"]["reflection"]["quality_score"]
            for exp in self.experiences
        ]
        avg_quality = sum(quality_scores) / len(quality_scores)

        all_insights = []
        for exp in self.experiences:
            all_insights.extend(exp["experience"]["reflection"]["insights"])

        retry_count = sum(
            1
            for exp in self.experiences
            if exp["experience"]["reflection"]["needs_retry"]
        )

        # 写入报告
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("Agent 摘要报告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 总体统计\n\n")
            f.write(f"- 总经验数: {total_experiences}\n")
            f.write(f"- 成功: {successful} ({successful/total_experiences*100:.1f}%)\n")
            f.write(f"- 失败: {failed} ({failed/total_experiences*100:.1f}%)\n")
            f.write(f"- 平均质量: {avg_quality:.3f}\n")
            f.write(f"- 重试次数: {retry_count}\n\n")

            f.write("## 质量分布\n\n")
            high = sum(1 for q in quality_scores if q >= 0.8)
            medium = sum(1 for q in quality_scores if 0.4 <= q < 0.8)
            low = sum(1 for q in quality_scores if q < 0.4)
            f.write(f"- 高质量 (≥0.8): {high} ({high/total_experiences*100:.1f}%)\n")
            f.write(
                f"- 中质量 (0.4-0.8): {medium} ({medium/total_experiences*100:.1f}%)\n"
            )
            f.write(f"- 低质量 (<0.4): {low} ({low/total_experiences*100:.1f}%)\n\n")

            f.write("## 关键洞察 (前10条)\n\n")
            unique_insights = list(set(all_insights))[:10]
            for i, insight in enumerate(unique_insights, 1):
                f.write(f"{i}. {insight}\n")

        logger.info(f"摘要报告已保存到: {output_file}")


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    # 创建可视化工具
    visualizer = AgentVisualizer(memory_file="memory/long_term_memory.jsonl")

    # 如果没有数据，生成模拟数据用于演示
    if not visualizer.experiences:
        logger.warning("未找到记忆文件，请先运行 Agent 系统生成数据")
        return

    # 生成可视化
    print("\n生成可视化...")

    visualizer.visualize_quality_distribution("visualizations/quality_dist.png")
    visualizer.visualize_action_performance("visualizations/action_performance.png")
    visualizer.visualize_reflection_impact("visualizations/reflection_impact.png")

    # 打印决策轨迹
    visualizer.print_decision_trace(max_steps=5)

    # 导出摘要报告
    visualizer.export_summary_report("visualizations/agent_summary.txt")

    print("\n✓ 可视化完成！请查看 visualizations/ 目录")


if __name__ == "__main__":
    # 创建输出目录
    Path("visualizations").mkdir(exist_ok=True)

    main()
