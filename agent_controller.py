"""
Agent Controller
智能体控制器，实现 ReAct (Reasoning + Acting) + Reflection 循环
"""

import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from agent_core import (
    Goal,
    Action,
    ActionType,
    ToolResult,
    Reflection,
    Experience,
    Plan,
    EnvironmentState,
)
from memory_system import MemorySystem
from reflection_engine import ReflectionEngine
from tool_manager import ToolManager
from llm_client import call_gpt4o_text

logger = logging.getLogger(__name__)


class AgentController:
    """
    Agent 控制器

    实现 ReAct + Reflection 循环：
    1. Observe: 观察环境和当前状态
    2. Think: 推理下一步应该做什么
    3. Act: 执行动作
    4. Reflect: 反思动作的结果
    5. Learn: 从经验中学习，更新记忆
    """

    def __init__(
        self,
        enable_llm_planning: bool = True,
        enable_llm_reflection: bool = True,
        max_retries: int = 2,
    ):
        """
        初始化 Agent 控制器

        Args:
            enable_llm_planning: 是否启用LLM辅助规划
            enable_llm_reflection: 是否启用LLM辅助反思
            max_retries: 最大重试次数
        """
        self.memory = MemorySystem()
        self.reflection_engine = ReflectionEngine(
            enable_llm_reflection=enable_llm_reflection
        )
        self.tool_manager = ToolManager()

        self.enable_llm_planning = enable_llm_planning
        self.max_retries = max_retries

        # 当前状态
        self.current_goal: Optional[Goal] = None
        self.current_plan: Optional[Plan] = None
        self.retry_count: Dict[str, int] = {}  # 动作重试计数

        logger.info(
            f"Agent Controller 初始化完成 "
            f"(LLM规划: {enable_llm_planning}, LLM反思: {enable_llm_reflection})"
        )

    def process_paper(
        self, paper_info: Dict[str, Any], pdf_path: str
    ) -> List[Dict[str, Any]]:
        """
        处理单篇论文（主入口）

        Args:
            paper_info: 论文信息
            pdf_path: PDF 文件路径

        Returns:
            提取的数据集记录列表
        """
        logger.info(f"开始处理论文: {paper_info.get('title', 'Unknown')}")

        # 1. 创建目标
        goal = self._create_goal(paper_info, pdf_path)
        self.current_goal = goal

        # 2. 制定计划
        plan = self._create_plan(goal)
        self.current_plan = plan

        logger.info(f"目标: {goal.description}")
        logger.info(f"计划: {' -> '.join([s.value for s in plan.steps])}")

        # 3. 执行 ReAct 循环
        datasets = self._execute_react_loop(goal, plan, paper_info, pdf_path)

        # 4. 总结会话
        summary = self.memory.summarize_session()
        logger.info(f"会话总结: {json.dumps(summary, ensure_ascii=False, indent=2)}")

        return datasets

    def _execute_react_loop(
        self,
        goal: Goal,
        plan: Plan,
        paper_info: Dict[str, Any],
        pdf_path: str,
    ) -> List[Dict[str, Any]]:
        """
        执行 ReAct 循环

        Returns:
            提取的数据集列表
        """
        # 共享上下文
        context = {
            "paper_info": paper_info,
            "pdf_path": pdf_path,
            "parsed_data": {},
            "datasets": [],
        }

        while not plan.is_completed():
            # 1. Observe (观察)
            observation = self._observe(goal, plan, context)
            logger.info(f"\n{'='*60}")
            logger.info(f"[观察] 当前步骤: {observation['current_step']}")

            # 2. Think (推理)
            thought = self._think(observation, goal, plan)
            logger.info(f"[推理] {thought['reasoning']}")

            # 3. Decide Action (决策)
            action = self._decide_action(thought, goal, plan, context)
            logger.info(f"[动作] {action.action_type.value}")

            # 4. Act (执行)
            result = self._act(action)
            logger.info(
                f"[结果] {'✓ 成功' if result.success else '✗ 失败'} "
                f"(耗时: {result.execution_time:.2f}s)"
            )

            # 5. Reflect (反思)
            reflection = self._reflect(action, result, goal, context)
            logger.info(
                f"[反思] 质量={reflection.quality_score:.2f}, "
                f"进度={reflection.goal_progress:.2f}"
            )

            if reflection.insights:
                logger.info(f"[洞察] {'; '.join(reflection.insights[:2])}")

            # 6. Learn (学习 - 存储经验)
            self._learn(action, result, reflection, goal, context)

            # 7. Adjust (调整 - 根据反思调整计划)
            should_continue = self._adjust(reflection, plan, context, result)

            if not should_continue:
                logger.warning("中止执行")
                break

            # 更新上下文
            self._update_context(context, action, result)

            # 前进到下一步（如果反思没有要求重试）
            if not reflection.needs_retry:
                plan.advance_step()

        # 返回提取的数据集
        return context.get("datasets", [])

    def _observe(
        self, goal: Goal, plan: Plan, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        观察当前状态

        Returns:
            观察结果
        """
        current_step = plan.get_current_step()
        recent_experiences = self.memory.retrieve_recent_experiences(count=3)

        return {
            "goal": goal,
            "current_step": current_step.value if current_step else "completed",
            "plan_progress": f"{plan.current_step_index}/{len(plan.steps)}",
            "recent_experiences": [e.summary() for e in recent_experiences],
            "context": context,
        }

    def _think(
        self, observation: Dict[str, Any], goal: Goal, plan: Plan
    ) -> Dict[str, Any]:
        """
        推理下一步行动

        Returns:
            思考结果
        """
        current_step = observation["current_step"]

        # 基础推理
        reasoning = f"目标是提取论文中的数据集信息。当前需要执行: {current_step}"

        # 检索相似经验
        similar_experiences = self.memory.retrieve_similar_experiences(
            action_type=current_step, context=observation["context"], top_k=2
        )

        if similar_experiences:
            # 从历史经验中学习
            insights = []
            for exp in similar_experiences:
                if exp.is_successful:
                    insights.append(
                        f"过去成功经验: {exp.reflection.success_assessment}"
                    )
            reasoning += f" 参考经验: {'; '.join(insights[:1])}"

        return {
            "reasoning": reasoning,
            "similar_experiences": similar_experiences,
            "confidence": 0.8,  # 简化版，实际可以更复杂
        }

    def _decide_action(
        self,
        thought: Dict[str, Any],
        goal: Goal,
        plan: Plan,
        context: Dict[str, Any],
    ) -> Action:
        """
        决策具体动作

        Returns:
            动作对象
        """
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        current_step = plan.get_current_step()

        # 根据当前步骤准备参数
        params = self._prepare_action_params(current_step, context)

        return Action(
            action_id=action_id,
            action_type=current_step,
            params=params,
            goal_id=goal.goal_id,
            reasoning=thought["reasoning"],
        )

    def _act(self, action: Action) -> ToolResult:
        """
        执行动作

        Args:
            action: 要执行的动作

        Returns:
            工具执行结果
        """
        # 记录重试次数
        retry_key = f"{action.goal_id}_{action.action_type.value}"
        retry_count = self.retry_count.get(retry_key, 0)

        # 执行工具
        result = self.tool_manager.execute_action(action)

        # 在结果中添加重试次数
        result.metadata["retry_count"] = retry_count

        return result

    def _reflect(
        self,
        action: Action,
        result: ToolResult,
        goal: Goal,
        context: Dict[str, Any],
    ) -> Reflection:
        """
        反思动作执行结果

        Returns:
            反思对象
        """
        # 获取历史经验用于对比
        history = self.memory.retrieve_recent_experiences(count=5)

        # 使用反思引擎进行反思
        reflection = self.reflection_engine.reflect(
            action=action, result=result, goal=goal, context=context, history=history
        )

        # 存储反思
        self.memory.store_reflection(reflection)

        return reflection

    def _learn(
        self,
        action: Action,
        result: ToolResult,
        reflection: Reflection,
        goal: Goal,
        context: Dict[str, Any],
    ):
        """
        从经验中学习，存储到记忆

        Args:
            action: 动作
            result: 结果
            reflection: 反思
            goal: 目标
            context: 上下文
        """
        # 创建经验
        experience_id = f"exp_{uuid.uuid4().hex[:8]}"
        is_successful = result.success and reflection.quality_score >= 0.5

        # 判断是否是重要经验（值得存入长期记忆）
        is_significant = self._is_significant_experience(reflection, result)

        # 创建模式（用于相似度匹配）
        pattern = f"{action.action_type.value}"

        experience = Experience(
            experience_id=experience_id,
            goal=goal,
            action=action,
            result=result,
            reflection=reflection,
            is_successful=is_successful,
            is_significant=is_significant,
            pattern=pattern,
        )

        # 存储经验
        self.memory.store_experience(experience)

        logger.debug(
            f"经验已存储: {experience_id} "
            f"({'重要' if is_significant else '普通'})"
        )

    def _adjust(
        self,
        reflection: Reflection,
        plan: Plan,
        context: Dict[str, Any],
        result: ToolResult,
    ) -> bool:
        """
        根据反思调整计划

        Args:
            reflection: 反思结果
            plan: 当前计划
            context: 上下文
            result: 执行结果

        Returns:
            是否应该继续执行
        """
        # 如果需要重试
        if reflection.needs_retry:
            retry_key = f"{plan.goal_id}_{plan.get_current_step().value}"
            current_retries = self.retry_count.get(retry_key, 0)

            if current_retries < self.max_retries:
                self.retry_count[retry_key] = current_retries + 1
                logger.info(
                    f"将重试动作: {plan.get_current_step().value} "
                    f"(第 {current_retries + 1} 次重试)"
                )
                # 不前进计划，下次循环会重新执行
                return True
            else:
                logger.warning(
                    f"已达到最大重试次数 ({self.max_retries})，跳过此步骤"
                )
                # 继续执行下一步
                return True

        # 如果需要重新规划
        if reflection.needs_replan:
            logger.info("根据反思重新规划...")
            # 简化版：这里可以调用 LLM 重新生成计划
            # 暂时使用默认行为：继续执行
            plan.adjustments.append(f"在步骤 {plan.current_step_index} 触发重新规划")
            return True

        # 如果结果严重失败且没有建议重试，考虑终止
        if not result.success and reflection.quality_score < 0.1:
            logger.error("严重失败，考虑终止")
            # 但对于数据集提取，我们可以容忍某些步骤失败
            return True

        return True

    def _update_context(
        self, context: Dict[str, Any], action: Action, result: ToolResult
    ):
        """更新共享上下文"""
        if not result.success:
            return

        # 根据动作类型更新上下文
        if action.action_type == ActionType.PARSE_PDF:
            context["parsed_data"]["summary_text"] = result.result.get("summary_text")
            context["parsed_data"]["urls"] = result.result.get("urls", [])

        elif action.action_type == ActionType.EXTRACT_META:
            context["parsed_data"]["meta"] = result.result

        elif action.action_type == ActionType.EXTRACT_DATASETS:
            context["parsed_data"]["dataset_names"] = result.result.get("datasets", [])

        elif action.action_type == ActionType.EXTRACT_DATASET_DETAILS:
            # 添加到数据集列表
            context["datasets"].append(result.result)

    def _create_goal(self, paper_info: Dict[str, Any], pdf_path: str) -> Goal:
        """创建目标"""
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"

        return Goal(
            goal_id=goal_id,
            description=f"从论文中提取所有数据集信息",
            goal_type="extract_datasets_from_paper",
            target={"paper_info": paper_info, "pdf_path": pdf_path},
            success_criteria={
                "min_datasets": 1,
                "has_meta": True,
                "quality_threshold": 0.5,
            },
            status="in_progress",
        )

    def _create_plan(self, goal: Goal) -> Plan:
        """创建计划"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # 标准流程
        steps = [
            ActionType.PARSE_PDF,
            ActionType.EXTRACT_META,
            ActionType.EXTRACT_DATASETS,
            # EXTRACT_DATASET_DETAILS 会动态添加（每个数据集一次）
        ]

        return Plan(
            plan_id=plan_id,
            goal_id=goal.goal_id,
            steps=steps,
            reasoning="标准的论文数据集提取流程",
        )

    def _prepare_action_params(
        self, action_type: ActionType, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备动作参数"""
        if action_type == ActionType.PARSE_PDF:
            return {"pdf_path": context["pdf_path"], "max_chars": 25000}

        elif action_type == ActionType.EXTRACT_META:
            return {
                "text": context["parsed_data"].get("summary_text", ""),
                "paper_info": context["paper_info"],
            }

        elif action_type == ActionType.EXTRACT_DATASETS:
            return {"text": context["parsed_data"].get("summary_text", "")}

        elif action_type == ActionType.EXTRACT_DATASET_DETAILS:
            # 这里需要特殊处理，因为要为每个数据集调用
            # 在实际使用中会动态设置
            return {}

        return {}

    def _is_significant_experience(
        self, reflection: Reflection, result: ToolResult
    ) -> bool:
        """判断是否是重要经验"""
        # 高质量成功的经验
        if reflection.quality_score >= 0.8 and result.success:
            return True

        # 失败但有深刻洞察的经验
        if not result.success and len(reflection.insights) >= 2:
            return True

        # 发现重要问题的经验
        if len(reflection.issues_found) >= 2:
            return True

        return False

    def extract_datasets_with_details(
        self, dataset_names: List[str], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为每个数据集提取详细信息（使用 ReAct）

        Args:
            dataset_names: 数据集名称列表
            context: 上下文

        Returns:
            数据集详细信息列表
        """
        datasets = []

        for idx, dataset_name in enumerate(dataset_names, 1):
            logger.info(f"\n处理数据集 {idx}/{len(dataset_names)}: {dataset_name}")

            # 创建子目标
            sub_goal = Goal(
                goal_id=f"subgoal_{uuid.uuid4().hex[:8]}",
                description=f"提取数据集 '{dataset_name}' 的详细信息",
                goal_type="extract_dataset_details",
                target={"dataset_name": dataset_name},
                success_criteria={"has_description": True, "quality_threshold": 0.6},
                status="in_progress",
            )

            # 创建动作
            action = Action(
                action_id=f"act_{uuid.uuid4().hex[:8]}",
                action_type=ActionType.EXTRACT_DATASET_DETAILS,
                params={
                    "dataset_name": dataset_name,
                    "text": context["parsed_data"].get("summary_text", ""),
                    "urls": context["parsed_data"].get("urls", []),
                },
                goal_id=sub_goal.goal_id,
                reasoning=f"提取数据集 {dataset_name} 的详细信息",
            )

            # 执行
            result = self._act(action)

            # 反思
            reflection = self._reflect(action, result, sub_goal, context)

            # 学习
            self._learn(action, result, reflection, sub_goal, context)

            # 如果成功，添加到列表
            if result.success and result.result:
                datasets.append(result.result)

        return datasets
