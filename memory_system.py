"""
Memory System
Agent 的记忆系统，包含短期记忆、长期记忆和反思存储
"""

import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from agent_core import Experience, Reflection, Action, Goal, ToolResult

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    记忆系统

    组成部分：
    1. 短期记忆 (Short-term Memory): 当前任务的执行历史
    2. 长期记忆 (Long-term Memory): 跨任务的重要经验
    3. 反思存储 (Reflection Store): 所有反思记录
    4. 统计信息 (Statistics): 用于决策的统计数据
    """

    def __init__(self, memory_dir: str = "memory"):
        """
        初始化记忆系统

        Args:
            memory_dir: 记忆持久化目录
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # 短期记忆：当前会话的经验列表
        self.short_term: List[Experience] = []

        # 长期记忆：重要经验的索引，按模式分类
        self.long_term: Dict[str, List[Experience]] = defaultdict(list)

        # 反思存储：所有反思记录
        self.reflections: List[Reflection] = []

        # 统计信息
        self.statistics = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "average_quality_score": 0.0,
            "action_type_stats": defaultdict(lambda: {"success": 0, "failure": 0}),
        }

        # 加载持久化的长期记忆
        self._load_long_term_memory()

        logger.info("记忆系统初始化完成")

    def store_experience(self, experience: Experience):
        """
        存储经验到记忆中

        Args:
            experience: 要存储的经验
        """
        # 添加到短期记忆
        self.short_term.append(experience)
        logger.info(f"已存储经验到短期记忆: {experience.experience_id}")

        # 更新统计信息
        self._update_statistics(experience)

        # 如果是重要经验，存入长期记忆
        if experience.is_significant:
            self._store_to_long_term(experience)

        # 如果短期记忆过多，清理旧记忆
        if len(self.short_term) > 100:
            self._cleanup_short_term_memory()

    def store_reflection(self, reflection: Reflection):
        """
        存储反思

        Args:
            reflection: 反思对象
        """
        self.reflections.append(reflection)
        logger.debug(f"已存储反思: {reflection.reflection_id}")

    def retrieve_recent_experiences(self, count: int = 5) -> List[Experience]:
        """
        检索最近的经验

        Args:
            count: 要检索的经验数量

        Returns:
            最近的经验列表
        """
        return self.short_term[-count:] if self.short_term else []

    def retrieve_similar_experiences(
        self, action_type: str, context: Dict[str, Any], top_k: int = 3
    ) -> List[Experience]:
        """
        检索相似的历史经验

        Args:
            action_type: 动作类型
            context: 当前上下文
            top_k: 返回前k个最相似的经验

        Returns:
            相似经验列表
        """
        # 从长期记忆中检索
        pattern = self._create_pattern(action_type, context)
        similar_experiences = self.long_term.get(pattern, [])

        # 如果没找到完全匹配的，尝试模糊匹配
        if not similar_experiences:
            similar_experiences = self._fuzzy_match_experiences(action_type, context)

        # 按质量评分排序
        similar_experiences.sort(
            key=lambda e: e.reflection.quality_score, reverse=True
        )

        result = similar_experiences[:top_k]
        logger.info(f"检索到 {len(result)} 个相似经验")
        return result

    def retrieve_reflections_for_goal(self, goal_id: str) -> List[Reflection]:
        """
        检索特定目标的所有反思

        Args:
            goal_id: 目标ID

        Returns:
            反思列表
        """
        return [r for r in self.reflections if r.goal_id == goal_id]

    def get_action_success_rate(self, action_type: str) -> float:
        """
        获取某类动作的成功率

        Args:
            action_type: 动作类型

        Returns:
            成功率 (0-1)
        """
        stats = self.statistics["action_type_stats"].get(action_type)
        if not stats:
            return 0.0

        total = stats["success"] + stats["failure"]
        if total == 0:
            return 0.0

        return stats["success"] / total

    def get_average_quality_for_action(self, action_type: str) -> float:
        """
        获取某类动作的平均质量评分

        Args:
            action_type: 动作类型

        Returns:
            平均质量评分 (0-1)
        """
        relevant_experiences = [
            e
            for e in self.short_term + self._get_all_long_term_experiences()
            if e.action.action_type.value == action_type
        ]

        if not relevant_experiences:
            return 0.0

        total_quality = sum(e.reflection.quality_score for e in relevant_experiences)
        return total_quality / len(relevant_experiences)

    def get_recent_insights(self, count: int = 5) -> List[str]:
        """
        获取最近的洞察

        Args:
            count: 数量

        Returns:
            洞察列表
        """
        recent_reflections = self.reflections[-count * 2 :]
        insights = []
        for reflection in recent_reflections:
            insights.extend(reflection.insights)

        return insights[-count:]

    def summarize_session(self) -> Dict[str, Any]:
        """
        总结当前会话的记忆

        Returns:
            会话摘要
        """
        if not self.short_term:
            return {"message": "当前会话暂无经验"}

        successful = [e for e in self.short_term if e.is_successful]
        failed = [e for e in self.short_term if not e.is_successful]

        quality_scores = [e.reflection.quality_score for e in self.short_term]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_experiences": len(self.short_term),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.short_term) if self.short_term else 0,
            "average_quality_score": avg_quality,
            "significant_experiences": len(
                [e for e in self.short_term if e.is_significant]
            ),
            "recent_insights": self.get_recent_insights(3),
        }

    def clear_short_term(self):
        """清空短期记忆（用于新会话）"""
        logger.info(f"清空短期记忆，共 {len(self.short_term)} 条经验")
        self.short_term = []

    def save_to_disk(self):
        """将长期记忆保存到磁盘"""
        try:
            long_term_file = self.memory_dir / "long_term_memory.jsonl"
            with open(long_term_file, "w", encoding="utf-8") as f:
                for pattern, experiences in self.long_term.items():
                    for exp in experiences:
                        record = {
                            "pattern": pattern,
                            "experience": exp.to_dict(),
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")

            logger.info(f"长期记忆已保存到 {long_term_file}")
        except Exception as e:
            logger.error(f"保存长期记忆失败: {str(e)}")

    def _load_long_term_memory(self):
        """从磁盘加载长期记忆"""
        try:
            long_term_file = self.memory_dir / "long_term_memory.jsonl"
            if not long_term_file.exists():
                return

            with open(long_term_file, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    pattern = record["pattern"]
                    exp_dict = record["experience"]

                    # 重建 Experience 对象（简化版，实际需要完整重建）
                    # 这里暂时只加载统计信息
                    pass

            logger.info(f"已加载长期记忆")
        except Exception as e:
            logger.warning(f"加载长期记忆失败: {str(e)}")

    def _clean_experience_for_storage(self, experience: Experience) -> Experience:
        """
        清理经验对象中的大文本字段，避免存储时占用过多空间

        Args:
            experience: 原始经验对象

        Returns:
            清理后的经验对象
        """
        import copy
        cleaned = copy.deepcopy(experience)

        # 清理 action.params 中的大文本字段
        if hasattr(cleaned.action, 'params') and isinstance(cleaned.action.params, dict):
            for key in ['text', 'summary_text', 'content']:
                if key in cleaned.action.params and isinstance(cleaned.action.params[key], str):
                    text = cleaned.action.params[key]
                    if len(text) > 500:
                        # 只保留前后各200字符
                        cleaned.action.params[key] = f"{text[:200]}...[省略{len(text)-400}字]...{text[-200:]}"

        return cleaned

    def _store_to_long_term(self, experience: Experience):
        """
        将经验存入长期记忆

        Args:
            experience: 经验对象
        """
        pattern = experience.pattern or self._create_pattern(
            experience.action.action_type.value, {}
        )

        # 清理大文本字段后再存储
        cleaned_experience = self._clean_experience_for_storage(experience)
        self.long_term[pattern].append(cleaned_experience)
        logger.info(f"已将经验存入长期记忆，模式: {pattern}")

        # 定期持久化
        if len(self._get_all_long_term_experiences()) % 10 == 0:
            self.save_to_disk()

    def _update_statistics(self, experience: Experience):
        """
        更新统计信息

        Args:
            experience: 经验对象
        """
        self.statistics["total_actions"] += 1

        if experience.is_successful:
            self.statistics["successful_actions"] += 1
            self.statistics["action_type_stats"][experience.action.action_type.value][
                "success"
            ] += 1
        else:
            self.statistics["failed_actions"] += 1
            self.statistics["action_type_stats"][experience.action.action_type.value][
                "failure"
            ] += 1

        # 更新平均质量评分
        total = self.statistics["total_actions"]
        current_avg = self.statistics["average_quality_score"]
        new_score = experience.reflection.quality_score
        self.statistics["average_quality_score"] = (
            current_avg * (total - 1) + new_score
        ) / total

    def _cleanup_short_term_memory(self):
        """清理短期记忆，只保留最近的50条"""
        logger.info("清理短期记忆...")
        self.short_term = self.short_term[-50:]

    def _create_pattern(self, action_type: str, context: Dict[str, Any]) -> str:
        """
        创建经验模式

        Args:
            action_type: 动作类型
            context: 上下文

        Returns:
            模式字符串
        """
        # 简化版模式：仅基于动作类型
        # 实际可以根据上下文细化，如 "extract_datasets_from_NeurIPS"
        return f"{action_type}"

    def _fuzzy_match_experiences(
        self, action_type: str, context: Dict[str, Any]
    ) -> List[Experience]:
        """
        模糊匹配经验

        Args:
            action_type: 动作类型
            context: 上下文

        Returns:
            匹配的经验列表
        """
        all_experiences = self._get_all_long_term_experiences()
        return [
            e for e in all_experiences if e.action.action_type.value == action_type
        ]

    def _get_all_long_term_experiences(self) -> List[Experience]:
        """获取所有长期记忆中的经验"""
        all_experiences = []
        for experiences in self.long_term.values():
            all_experiences.extend(experiences)
        return all_experiences
