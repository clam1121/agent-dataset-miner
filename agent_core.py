"""
Agent 核心数据结构
定义 Agent 系统中使用的基础数据类型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json


class ActionType(Enum):
    """动作类型枚举"""
    DOWNLOAD_PAPER = "download_paper"
    PARSE_PDF = "parse_pdf"
    EXTRACT_META = "extract_meta"
    EXTRACT_DATASETS = "extract_datasets"
    EXTRACT_DATASET_DETAILS = "extract_dataset_details"
    VALIDATE_URL = "validate_url"
    SAVE_RESULTS = "save_results"
    REPLAN = "replan"


class ReflectionType(Enum):
    """反思类型枚举"""
    QUALITY_CHECK = "quality_check"
    GOAL_ALIGNMENT = "goal_alignment"
    STRATEGY_ADJUSTMENT = "strategy_adjustment"
    ERROR_ANALYSIS = "error_analysis"


@dataclass
class Goal:
    """
    目标
    表示 Agent 要达成的目标
    """
    goal_id: str
    description: str
    goal_type: str  # "extract_datasets", "process_paper", etc.
    target: Any  # 目标对象（如论文信息）
    success_criteria: Dict[str, Any]  # 成功标准
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed

    def to_dict(self) -> Dict:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "goal_type": self.goal_type,
            "target": self.target,
            "success_criteria": self.success_criteria,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Action:
    """
    动作
    Agent 执行的具体动作
    """
    action_id: str
    action_type: ActionType
    params: Dict[str, Any]
    goal_id: str  # 关联的目标ID
    reasoning: str  # 执行此动作的推理过程
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "params": self.params,
            "goal_id": self.goal_id,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ToolResult:
    """
    工具执行结果
    """
    action_id: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "success": self.success,
            "result": self.result,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Reflection:
    """
    反思
    Agent 对自己行为和结果的反思
    """
    reflection_id: str
    reflection_type: ReflectionType
    action_id: str
    goal_id: str

    # 反思内容
    quality_score: float  # 0-1，质量评分
    goal_progress: float  # 0-1，目标完成度
    success_assessment: str  # 成功程度评估

    # 洞察和建议
    insights: List[str]  # 从这次执行中学到的
    issues_found: List[str]  # 发现的问题
    suggested_improvements: List[str]  # 改进建议

    # 决策建议
    needs_retry: bool = False
    needs_replan: bool = False
    suggested_next_action: Optional[str] = None

    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "reflection_id": self.reflection_id,
            "reflection_type": self.reflection_type.value,
            "action_id": self.action_id,
            "goal_id": self.goal_id,
            "quality_score": self.quality_score,
            "goal_progress": self.goal_progress,
            "success_assessment": self.success_assessment,
            "insights": self.insights,
            "issues_found": self.issues_found,
            "suggested_improvements": self.suggested_improvements,
            "needs_retry": self.needs_retry,
            "needs_replan": self.needs_replan,
            "suggested_next_action": self.suggested_next_action,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Experience:
    """
    经验
    存储在记忆中的一次完整的"行动-结果-反思"循环
    """
    experience_id: str
    goal: Goal
    action: Action
    result: ToolResult
    reflection: Reflection

    # 经验元数据
    is_successful: bool
    is_significant: bool = False  # 是否是重要经验（值得存入长期记忆）
    pattern: Optional[str] = None  # 经验模式（用于相似度匹配）

    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "experience_id": self.experience_id,
            "goal": self.goal.to_dict(),
            "action": self.action.to_dict(),
            "result": self.result.to_dict(),
            "reflection": self.reflection.to_dict(),
            "is_successful": self.is_successful,
            "is_significant": self.is_significant,
            "pattern": self.pattern,
            "timestamp": self.timestamp.isoformat()
        }

    def summary(self) -> str:
        """返回经验的简短摘要"""
        return f"[{self.action.action_type.value}] → " \
               f"{'SUCCESS' if self.is_successful else 'FAILED'} " \
               f"(Quality: {self.reflection.quality_score:.2f})"


@dataclass
class EnvironmentState:
    """
    环境状态
    Agent 感知到的当前环境信息
    """
    papers_remaining: int
    current_paper: Optional[Dict[str, Any]]
    processed_count: int
    success_count: int
    failure_count: int

    # 资源状态
    api_quota_remaining: Optional[int] = None
    disk_space_available: Optional[float] = None

    # 错误和异常
    recent_errors: List[str] = field(default_factory=list)
    consecutive_failures: int = 0

    # 统计信息
    average_quality_score: float = 0.0
    success_rate: float = 0.0

    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "papers_remaining": self.papers_remaining,
            "current_paper": self.current_paper,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "api_quota_remaining": self.api_quota_remaining,
            "recent_errors": self.recent_errors,
            "consecutive_failures": self.consecutive_failures,
            "average_quality_score": self.average_quality_score,
            "success_rate": self.success_rate,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Plan:
    """
    计划
    Agent 为达成目标制定的行动计划
    """
    plan_id: str
    goal_id: str
    steps: List[ActionType]
    current_step_index: int = 0
    status: str = "active"  # active, completed, replanning

    # 计划元数据
    reasoning: str = ""  # 制定此计划的推理
    adjustments: List[str] = field(default_factory=list)  # 计划调整历史

    created_at: datetime = field(default_factory=datetime.now)

    def get_current_step(self) -> Optional[ActionType]:
        """获取当前步骤"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self):
        """前进到下一步"""
        self.current_step_index += 1

    def is_completed(self) -> bool:
        """计划是否完成"""
        return self.current_step_index >= len(self.steps)

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "steps": [s.value for s in self.steps],
            "current_step_index": self.current_step_index,
            "status": self.status,
            "reasoning": self.reasoning,
            "adjustments": self.adjustments,
            "created_at": self.created_at.isoformat()
        }
