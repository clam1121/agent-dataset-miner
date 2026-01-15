"""
Reflection Engine
Agent 的反思引擎，负责对动作和结果进行多维度反思
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from agent_core import (
    Reflection,
    ReflectionType,
    Action,
    ToolResult,
    Goal,
    Experience,
)
from llm_client import call_gpt4o_text

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """
    反思引擎

    核心能力：
    1. 评估动作执行的质量
    2. 判断目标完成进度
    3. 发现问题和不足
    4. 提供改进建议
    5. 决定是否需要重试或重新规划
    """

    def __init__(self, enable_llm_reflection: bool = True):
        """
        初始化反思引擎

        Args:
            enable_llm_reflection: 是否启用LLM辅助反思（更深入但更慢）
        """
        self.enable_llm_reflection = enable_llm_reflection
        logger.info(
            f"反思引擎初始化完成 (LLM反思: {'启用' if enable_llm_reflection else '禁用'})"
        )

    def reflect(
        self,
        action: Action,
        result: ToolResult,
        goal: Goal,
        context: Dict[str, Any],
        history: List[Experience] = None,
    ) -> Reflection:
        """
        对一次动作执行进行反思

        Args:
            action: 执行的动作
            result: 动作执行结果
            goal: 当前目标
            context: 上下文信息
            history: 历史经验（用于对比）

        Returns:
            反思对象
        """
        logger.info(f"开始反思动作: {action.action_type.value}")

        # 1. 基础反思（快速，基于规则）
        base_reflection = self._basic_reflection(action, result, goal)

        # 2. LLM 深度反思（可选，更深入）
        if self.enable_llm_reflection and result.success:
            try:
                llm_reflection = self._llm_reflection(
                    action, result, goal, context, history
                )
                # 合并 LLM 反思的洞察
                base_reflection = self._merge_reflections(base_reflection, llm_reflection)
            except Exception as e:
                logger.warning(f"LLM反思失败，使用基础反思: {str(e)}")

        logger.info(
            f"反思完成 - 质量: {base_reflection.quality_score:.2f}, "
            f"进度: {base_reflection.goal_progress:.2f}"
        )

        return base_reflection

    def _basic_reflection(
        self, action: Action, result: ToolResult, goal: Goal
    ) -> Reflection:
        """
        基础反思（基于规则的快速反思）

        Args:
            action: 动作
            result: 结果
            goal: 目标

        Returns:
            反思对象
        """
        reflection_id = f"refl_{uuid.uuid4().hex[:8]}"

        # 评估质量
        quality_score = self._assess_quality(action, result)

        # 评估目标进度
        goal_progress = self._assess_goal_progress(action, result, goal)

        # 判断成功程度
        success_assessment = self._assess_success(result, quality_score)

        # 发现问题
        issues_found = self._identify_issues(action, result)

        # 生成洞察
        insights = self._generate_basic_insights(action, result, quality_score)

        # 生成改进建议
        suggested_improvements = self._generate_basic_improvements(
            action, result, issues_found
        )

        # 决定是否需要重试或重新规划
        needs_retry = self._should_retry(result, quality_score, issues_found)
        needs_replan = self._should_replan(result, quality_score, goal_progress)

        # 建议下一步动作
        suggested_next_action = self._suggest_next_action(
            action, result, goal, needs_retry, needs_replan
        )

        return Reflection(
            reflection_id=reflection_id,
            reflection_type=ReflectionType.QUALITY_CHECK,
            action_id=action.action_id,
            goal_id=action.goal_id,
            quality_score=quality_score,
            goal_progress=goal_progress,
            success_assessment=success_assessment,
            insights=insights,
            issues_found=issues_found,
            suggested_improvements=suggested_improvements,
            needs_retry=needs_retry,
            needs_replan=needs_replan,
            suggested_next_action=suggested_next_action,
        )

    def _llm_reflection(
        self,
        action: Action,
        result: ToolResult,
        goal: Goal,
        context: Dict[str, Any],
        history: Optional[List[Experience]],
    ) -> Dict[str, Any]:
        """
        使用 LLM 进行深度反思

        Args:
            action: 动作
            result: 结果
            goal: 目标
            context: 上下文
            history: 历史经验

        Returns:
            LLM 反思结果
        """
        # 构建反思 prompt
        reflection_prompt = self._build_llm_reflection_prompt(
            action, result, goal, context, history
        )

        # 调用 LLM
        llm_response = call_gpt4o_text(reflection_prompt)

        # 解析响应
        reflection_data = self._parse_llm_reflection(llm_response)

        return reflection_data

    def _build_llm_reflection_prompt(
        self,
        action: Action,
        result: ToolResult,
        goal: Goal,
        context: Dict[str, Any],
        history: Optional[List[Experience]],
    ) -> str:
        """构建 LLM 反思的 prompt"""

        history_summary = ""
        if history and len(history) > 0:
            recent = history[-3:]
            history_summary = "\n".join([f"- {exp.summary()}" for exp in recent])

        prompt = f"""
你是一个智能 Agent 的反思引擎。请对以下动作执行进行深度反思。

## 目标
{goal.description}
期望标准: {json.dumps(goal.success_criteria, ensure_ascii=False)}

## 执行的动作
动作类型: {action.action_type.value}
执行推理: {action.reasoning}
参数: {json.dumps(action.params, ensure_ascii=False)}

## 执行结果
成功: {result.success}
结果摘要: {self._summarize_result(result)}
执行时间: {result.execution_time:.2f}秒
错误信息: {result.error_message or '无'}

## 上下文
{json.dumps(context, ensure_ascii=False, indent=2)}

## 最近的历史
{history_summary if history_summary else '无历史记录'}

---

请从以下角度进行反思：

1. **质量评估** (0-1评分)
   - 结果的准确性和完整性如何？
   - 是否达到了预期目标？

2. **问题识别**
   - 发现了哪些问题或不足？
   - 有哪些潜在风险？

3. **深层洞察**
   - 从这次执行中学到了什么？
   - 哪些做得好，哪些可以改进？

4. **改进建议**
   - 具体的改进措施是什么？
   - 下一步应该采取什么行动？

请以JSON格式返回反思结果：
```json
{{
  "quality_score": 0.85,
  "quality_reasoning": "结果完整性较好，但准确性有待提高...",
  "issues_found": ["问题1", "问题2"],
  "insights": ["洞察1", "洞察2"],
  "suggested_improvements": ["改进建议1", "改进建议2"],
  "needs_retry": false,
  "needs_different_approach": false,
  "recommended_next_action": "continue_to_next_step"
}}
```

只返回JSON，不要其他说明文字。
"""
        return prompt

    def _parse_llm_reflection(self, llm_response: str) -> Dict[str, Any]:
        """解析 LLM 反思响应"""
        try:
            # 尝试直接解析
            return json.loads(llm_response)
        except:
            pass

        # 尝试提取 JSON 块
        json_match = re.search(r"```json\s*(.*?)\s*```", llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # 尝试提取 {} 块
        json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass

        logger.warning("无法解析LLM反思响应，返回空字典")
        return {}

    def _merge_reflections(
        self, base: Reflection, llm_data: Dict[str, Any]
    ) -> Reflection:
        """合并基础反思和 LLM 反思"""
        if not llm_data:
            return base

        # 更新质量评分（取平均）
        if "quality_score" in llm_data:
            base.quality_score = (base.quality_score + llm_data["quality_score"]) / 2

        # 合并洞察
        if "insights" in llm_data:
            base.insights.extend(llm_data["insights"])
            base.insights = list(set(base.insights))  # 去重

        # 合并问题
        if "issues_found" in llm_data:
            base.issues_found.extend(llm_data["issues_found"])
            base.issues_found = list(set(base.issues_found))

        # 合并改进建议
        if "suggested_improvements" in llm_data:
            base.suggested_improvements.extend(llm_data["suggested_improvements"])
            base.suggested_improvements = list(set(base.suggested_improvements))

        # 更新决策
        if "needs_retry" in llm_data:
            base.needs_retry = base.needs_retry or llm_data["needs_retry"]

        if "needs_different_approach" in llm_data:
            base.needs_replan = (
                base.needs_replan or llm_data["needs_different_approach"]
            )

        return base

    def _assess_quality(self, action: Action, result: ToolResult) -> float:
        """评估质量评分 (0-1)"""
        if not result.success:
            return 0.0

        # 根据动作类型和结果评估质量
        score = 0.5  # 基础分

        # 如果有元数据，根据元数据调整
        if result.metadata:
            # 示例：如果提取到数据集，增加分数
            if "datasets_found" in result.metadata:
                count = result.metadata["datasets_found"]
                if count > 0:
                    score += 0.3
                if count > 2:
                    score += 0.2

            # 如果执行时间合理
            if result.execution_time < 10:
                score += 0.1

        return min(score, 1.0)

    def _assess_goal_progress(
        self, action: Action, result: ToolResult, goal: Goal
    ) -> float:
        """评估目标完成进度 (0-1)"""
        if not result.success:
            return 0.0

        # 简化版：根据动作类型估算进度
        progress_map = {
            "download_paper": 0.1,
            "parse_pdf": 0.2,
            "extract_meta": 0.3,
            "extract_datasets": 0.5,
            "extract_dataset_details": 0.8,
            "save_results": 1.0,
        }

        return progress_map.get(action.action_type.value, 0.0)

    def _assess_success(self, result: ToolResult, quality_score: float) -> str:
        """评估成功程度"""
        if not result.success:
            return "失败：执行出错"

        if quality_score >= 0.8:
            return "成功：高质量完成"
        elif quality_score >= 0.6:
            return "成功：质量良好"
        elif quality_score >= 0.4:
            return "部分成功：质量一般"
        else:
            return "低质量成功：需要改进"

    def _identify_issues(self, action: Action, result: ToolResult) -> List[str]:
        """识别问题"""
        issues = []

        if not result.success:
            issues.append(f"执行失败: {result.error_message}")

        if result.execution_time > 30:
            issues.append(f"执行时间过长: {result.execution_time:.1f}秒")

        # 根据结果内容识别问题
        if isinstance(result.result, dict):
            if not result.result:
                issues.append("返回结果为空")
            elif "datasets" in result.result and not result.result["datasets"]:
                issues.append("未提取到数据集")

        return issues

    def _generate_basic_insights(
        self, action: Action, result: ToolResult, quality_score: float
    ) -> List[str]:
        """生成基础洞察"""
        insights = []

        if quality_score >= 0.8:
            insights.append(f"{action.action_type.value} 执行效果良好")

        if result.execution_time < 5:
            insights.append("执行效率高")

        if result.metadata:
            insights.append(f"获得了丰富的元数据: {list(result.metadata.keys())}")

        return insights

    def _generate_basic_improvements(
        self, action: Action, result: ToolResult, issues: List[str]
    ) -> List[str]:
        """生成基础改进建议"""
        improvements = []

        if not result.success:
            improvements.append("检查输入参数是否正确")
            improvements.append("考虑使用备用方法")

        if "执行时间过长" in str(issues):
            improvements.append("优化处理流程，减少耗时操作")

        if "未提取到数据集" in str(issues):
            improvements.append("扩大搜索范围或调整关键词")
            improvements.append("检查论文内容是否真的包含数据集")

        return improvements

    def _should_retry(
        self, result: ToolResult, quality_score: float, issues: List[str]
    ) -> bool:
        """判断是否应该重试"""
        # 如果执行失败，考虑重试
        if not result.success:
            # 但如果是某些不可恢复的错误，不重试
            if result.error_message and "not found" in result.error_message.lower():
                return False
            return True

        # 如果质量太低，考虑重试
        if quality_score < 0.3 and len(issues) > 0:
            return True

        return False

    def _should_replan(
        self, result: ToolResult, quality_score: float, goal_progress: float
    ) -> bool:
        """判断是否应该重新规划"""
        # 如果多次失败，需要重新规划
        if not result.success and result.metadata.get("retry_count", 0) > 2:
            return True

        # 如果进度停滞，考虑重新规划
        if quality_score < 0.4 and goal_progress < 0.2:
            return True

        return False

    def _suggest_next_action(
        self,
        action: Action,
        result: ToolResult,
        goal: Goal,
        needs_retry: bool,
        needs_replan: bool,
    ) -> Optional[str]:
        """建议下一步动作"""
        if needs_retry:
            return f"retry_{action.action_type.value}"

        if needs_replan:
            return "replan"

        if not result.success:
            return "skip_to_next"

        # 根据当前动作建议下一步
        next_action_map = {
            "download_paper": "parse_pdf",
            "parse_pdf": "extract_meta",
            "extract_meta": "extract_datasets",
            "extract_datasets": "extract_dataset_details",
            "extract_dataset_details": "save_results",
        }

        return next_action_map.get(action.action_type.value, "continue")

    def _summarize_result(self, result: ToolResult) -> str:
        """总结结果（用于 prompt）"""
        if isinstance(result.result, dict):
            summary = {}
            for k, v in result.result.items():
                if isinstance(v, list):
                    summary[k] = f"列表(长度={len(v)})"
                elif isinstance(v, dict):
                    summary[k] = f"字典(键={list(v.keys())})"
                else:
                    summary[k] = str(v)[:100]
            return json.dumps(summary, ensure_ascii=False)
        else:
            return str(result.result)[:200]
