"""
Agent-based Dataset Miner
基于智能体的数据集挖掘器主程序
"""

import os
import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，使用系统环境变量
    pass

from agent_controller import AgentController
from neurips_downloader import NeurIPSDownloader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dataset_miner_agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AgentDatasetMiner:
    """
    基于 Agent 的数据集挖掘器

    核心特性：
    1. ReAct (Reasoning + Acting) 循环
    2. Reflection 机制
    3. Memory 系统（短期/长期记忆）
    4. 自主决策和错误恢复
    """

    def __init__(
        self,
        output_file: str = "outputs/dataset_agent_results.jsonl",
        enable_llm_reflection: bool = True,
        max_retries: int = 2,
    ):
        """
        初始化 Agent 数据集挖掘器

        Args:
            output_file: 输出文件路径
            enable_llm_reflection: 是否启用LLM辅助反思
            max_retries: 最大重试次数
        """
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # 初始化 Agent Controller
        self.agent = AgentController(
            enable_llm_planning=True,
            enable_llm_reflection=enable_llm_reflection,
            max_retries=max_retries,
        )

        # 数据集计数器
        self.dataset_counter = 0

        logger.info("=" * 80)
        logger.info("Agent-based Dataset Miner 初始化完成")
        logger.info(f"输出文件: {self.output_file}")
        logger.info(f"LLM反思: {'启用' if enable_llm_reflection else '禁用'}")
        logger.info(f"最大重试次数: {max_retries}")
        logger.info("=" * 80)

    def process_paper_with_agent(
        self, pdf_path: str, category: str, paper_info: dict
    ) -> List[Dict]:
        """
        使用 Agent 处理单篇论文

        Args:
            pdf_path: PDF文件路径
            category: 论文类别
            paper_info: 论文基本信息

        Returns:
            数据集信息列表
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[AGENT] 开始处理论文: {paper_info['title']}")
        logger.info(f"[AGENT] 类别: {category}")
        logger.info(f"{'='*80}")

        results = []

        try:
            # 阶段1: 使用 Agent 处理论文（提取元信息和数据集名称）
            logger.info("\n[阶段1] Agent 自主处理论文...")
            agent_result = self.agent.process_paper(paper_info, pdf_path)

            # agent_result 包含上下文，我们需要从中提取信息
            # 由于 process_paper 返回的是 datasets 列表，我们需要获取完整信息

            # 重新组织流程：先获取基础信息
            context = {}

            # 执行标准流程获取元信息和数据集名称
            from agent_core import Goal, Action, ActionType

            # 1. 解析 PDF
            parse_result = self.agent.tool_manager.execute_action(
                Action(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    action_type=ActionType.PARSE_PDF,
                    params={"pdf_path": pdf_path, "max_chars": 25000},
                    goal_id="temp",
                    reasoning="解析PDF获取文本",
                )
            )

            if not parse_result.success:
                logger.error("PDF解析失败")
                return results

            summary_text = parse_result.result["summary_text"]
            urls = parse_result.result["urls"]

            logger.info(
                f"✓ PDF解析完成: 文本长度={len(summary_text)}, URL数={len(urls)}"
            )

            # 2. 提取论文元信息
            meta_result = self.agent.tool_manager.execute_action(
                Action(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    action_type=ActionType.EXTRACT_META,
                    params={"text": summary_text[:15000], "paper_info": paper_info},
                    goal_id="temp",
                    reasoning="提取论文元信息",
                )
            )

            if not meta_result.success:
                logger.warning("元信息提取失败，使用默认值")
                paper_meta = {
                    "title": paper_info.get("title", "Unknown"),
                    "authors": [],
                    "venue": f"NeurIPS {category}",
                    "year": "2025",
                    "url": paper_info.get("url", ""),
                    "is_fellow": "true" if category == "best" else "false",
                }
            else:
                paper_meta = meta_result.result
                paper_meta["url"] = paper_info.get("url", paper_meta.get("url", ""))
                paper_meta["is_fellow"] = "true" if category == "best" else "false"

            logger.info(f"✓ 元信息提取完成: {paper_meta.get('title', 'Unknown')}")

            # 3. 提取数据集名称（带反思）
            logger.info("\n[阶段2] 使用 ReAct + Reflection 提取数据集...")

            datasets_result = self.agent.tool_manager.execute_action(
                Action(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    action_type=ActionType.EXTRACT_DATASETS,
                    params={"text": summary_text},
                    goal_id="temp",
                    reasoning="提取数据集名称",
                )
            )

            # 反思：评估提取质量
            from agent_core import Goal

            temp_goal = Goal(
                goal_id="temp",
                description="提取数据集名称",
                goal_type="extract_datasets",
                target={},
                success_criteria={"min_datasets": 1},
            )

            reflection = self.agent.reflection_engine.reflect(
                action=Action(
                    action_id=f"act_{uuid.uuid4().hex[:8]}",
                    action_type=ActionType.EXTRACT_DATASETS,
                    params={},
                    goal_id="temp",
                    reasoning="",
                ),
                result=datasets_result,
                goal=temp_goal,
                context={"summary_text": summary_text},
            )

            logger.info(
                f"[反思] 质量评分: {reflection.quality_score:.2f}, "
                f"评估: {reflection.success_assessment}"
            )

            if reflection.insights:
                logger.info(f"[洞察] {reflection.insights[0]}")

            dataset_names = datasets_result.result.get("datasets", [])

            if not dataset_names:
                logger.warning("未找到数据集")

                # 根据反思决定是否重试
                if reflection.needs_retry:
                    logger.info("[决策] 反思建议重试，尝试使用更宽松的提取策略...")
                    # 这里可以实现重试逻辑
                    # 简化版：直接跳过

                return results

            logger.info(f"✓ 找到 {len(dataset_names)} 个数据集: {dataset_names}")

            # 4. 为每个数据集提取详细信息（使用 Agent 的子目标机制）
            logger.info(f"\n[阶段3] 提取每个数据集的详细信息...")

            context = {
                "parsed_data": {"summary_text": summary_text, "urls": urls},
                "paper_info": paper_info,
            }

            dataset_details = self.agent.extract_datasets_with_details(
                dataset_names, context
            )

            logger.info(f"✓ 成功提取 {len(dataset_details)} 个数据集的详细信息")

            # 5. 组装最终结果
            for details in dataset_details:
                self.dataset_counter += 1
                dataset_record = {
                    "dataset id": str(self.dataset_counter).zfill(3),
                    "name": details.get("name", "Unknown"),
                    "dataset describe": {
                        "content": details.get("content", ""),
                        "type": details.get("type", ["unspecified"]),
                        "domain": details.get("domain", ["unspecified"]),
                        "fields": details.get("fields", ["unspecified"]),
                    },
                    "paper_refs": paper_meta,
                    "dataset link": details.get("dataset_link", ""),
                    "platform": details.get("platform", ""),
                }

                results.append(dataset_record)

            logger.info(f"\n[完成] 本篇论文提取了 {len(results)} 个数据集")

        except Exception as e:
            logger.error(f"[错误] 处理论文时出错: {str(e)}", exc_info=True)

        return results

    def save_results(self, results: List[Dict]):
        """
        保存结果到JSONL文件

        Args:
            results: 数据集信息列表
        """
        if not results:
            return

        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                for record in results:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    logger.info(
                        f"  ✓ 已保存: {record['name']} (ID: {record['dataset id']})"
                    )
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")

    def run(self, year: int = 2025, max_papers: int = None):
        """
        运行主流程

        Args:
            year: NeurIPS年份
            max_papers: 最大处理论文数（用于测试）
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"开始 Agent-based 数据集挖掘")
        logger.info(f"目标会议: NeurIPS {year}")
        logger.info(f"论文类型: Spotlight, Oral, Best Papers")
        if max_papers:
            logger.info(f"限制: 最多处理 {max_papers} 篇论文")
        logger.info(f"{'='*80}\n")

        # 初始化下载器
        downloader = NeurIPSDownloader(year=year, temp_dir="temp")

        total_papers = 0
        total_datasets = 0

        try:
            # 流式处理论文
            for pdf_path, category, paper_info in downloader.download_and_process_papers():
                total_papers += 1

                if max_papers and total_papers > max_papers:
                    logger.info(f"\n已达到最大论文数限制 ({max_papers})，停止处理")
                    break

                logger.info(f"\n{'#'*80}")
                logger.info(f"论文 {total_papers} [{category.upper()}]")
                logger.info(f"标题: {paper_info['title']}")
                logger.info(f"{'#'*80}")

                try:
                    # 使用 Agent 处理论文
                    results = self.process_paper_with_agent(
                        pdf_path, category, paper_info
                    )

                    # 保存结果
                    if results:
                        self.save_results(results)
                        total_datasets += len(results)

                except Exception as e:
                    logger.error(f"处理论文失败: {str(e)}", exc_info=True)

                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {str(e)}")

            # 输出统计信息
            logger.info(f"\n{'='*80}")
            logger.info(f"处理完成！")
            logger.info(f"总论文数: {total_papers}")
            logger.info(f"总数据集数: {total_datasets}")
            logger.info(f"输出文件: {self.output_file}")

            # Agent 记忆统计
            memory_summary = self.agent.memory.summarize_session()
            logger.info(f"\n[Agent 记忆统计]")
            logger.info(f"  总经验数: {memory_summary['total_experiences']}")
            logger.info(f"  成功率: {memory_summary['success_rate']:.2%}")
            logger.info(
                f"  平均质量: {memory_summary['average_quality_score']:.2f}"
            )
            logger.info(
                f"  重要经验: {memory_summary['significant_experiences']}"
            )

            # 工具统计
            tool_stats = self.agent.tool_manager.get_execution_stats()
            logger.info(f"\n[工具执行统计]")
            logger.info(f"  总调用: {tool_stats['total']}")
            logger.info(f"  成功: {tool_stats['success']}")
            logger.info(f"  失败: {tool_stats['failure']}")
            logger.info(f"  成功率: {tool_stats['success_rate']:.2%}")
            logger.info(
                f"  平均耗时: {tool_stats.get('average_execution_time', 0):.2f}s"
            )

            logger.info(f"{'='*80}\n")

        except Exception as e:
            logger.error(f"运行出错: {str(e)}", exc_info=True)

        finally:
            # 保存长期记忆
            self.agent.memory.save_to_disk()
            logger.info("已保存 Agent 长期记忆")


def main():
    """主函数"""
    # 创建 Agent 挖掘器
    miner = AgentDatasetMiner(
        output_file="outputs/dataset_agent_results.jsonl",
        enable_llm_reflection=True,  # 启用 LLM 反思
        max_retries=2,
    )

    # 运行（先用少量论文测试）
    miner.run(year=2024, max_papers=3)  # 测试：只处理3篇论文


if __name__ == "__main__":
    main()
