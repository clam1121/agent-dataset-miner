"""
Tool Manager
工具管理器，负责管理和执行所有工具
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from agent_core import Action, ActionType, ToolResult

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具

        Args:
            params: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def _create_result(
        self,
        action_id: str,
        success: bool,
        result: Any,
        error_message: Optional[str] = None,
        execution_time: float = 0.0,
        metadata: Dict[str, Any] = None,
    ) -> ToolResult:
        """创建工具结果"""
        return ToolResult(
            action_id=action_id,
            success=success,
            result=result,
            error_message=error_message,
            execution_time=execution_time,
            metadata=metadata or {},
        )


class PDFParserTool(BaseTool):
    """PDF 解析工具"""

    def __init__(self):
        super().__init__("pdf_parser")
        # 延迟导入以避免循环依赖
        from pdf_parser import PDFParser

        self.PDFParser = PDFParser

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行 PDF 解析

        Args:
            params: {"pdf_path": str, "max_chars": int}

        Returns:
            ToolResult 包含 (summary_text, urls)
        """
        start_time = time.time()
        action_id = params.get("action_id", "unknown")

        try:
            pdf_path = params["pdf_path"]
            max_chars = params.get("max_chars", 25000)

            parser = self.PDFParser(pdf_path)
            summary_text, urls = parser.get_summary_text(max_chars=max_chars)
            parser.close()

            execution_time = time.time() - start_time

            return self._create_result(
                action_id=action_id,
                success=True,
                result={"summary_text": summary_text, "urls": urls},
                execution_time=execution_time,
                metadata={
                    "text_length": len(summary_text),
                    "url_count": len(urls),
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"PDF解析失败: {str(e)}")
            return self._create_result(
                action_id=action_id,
                success=False,
                result=None,
                error_message=str(e),
                execution_time=execution_time,
            )


class MetaExtractorTool(BaseTool):
    """论文元信息提取工具"""

    def __init__(self):
        super().__init__("meta_extractor")
        from llm_client import call_gpt4o_text
        from prompts import EXTRACT_PAPER_META_PROMPT

        self.call_llm = call_gpt4o_text
        self.prompt_template = EXTRACT_PAPER_META_PROMPT

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        提取论文元信息

        Args:
            params: {"text": str, "paper_info": dict}

        Returns:
            ToolResult 包含论文元信息
        """
        start_time = time.time()
        action_id = params.get("action_id", "unknown")

        try:
            text = params["text"][:15000]  # 限制长度
            paper_info = params.get("paper_info", {})

            # 调用 LLM
            prompt = self.prompt_template.format(text=text)
            response = self.call_llm(prompt)

            # 解析响应
            meta = self._parse_json_response(response)

            # 补充信息
            if not meta.get("url"):
                meta["url"] = paper_info.get("url", "")

            execution_time = time.time() - start_time

            return self._create_result(
                action_id=action_id,
                success=True,
                result=meta,
                execution_time=execution_time,
                metadata={"has_authors": len(meta.get("authors", [])) > 0},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"元信息提取失败: {str(e)}")
            return self._create_result(
                action_id=action_id,
                success=False,
                result=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        import json
        import re

        try:
            return json.loads(response)
        except:
            pass

        # 尝试提取 JSON 块
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # 返回默认值
        return {
            "title": "Unknown",
            "authors": [],
            "venue": "Unknown",
            "year": "2025",
            "url": "",
            "is_fellow": "false",
        }


class DatasetFinderTool(BaseTool):
    """数据集名称提取工具"""

    def __init__(self):
        super().__init__("dataset_finder")
        from llm_client import call_gpt4o_text
        from prompts import EXTRACT_DATASET_NAMES_PROMPT

        self.call_llm = call_gpt4o_text
        self.prompt_template = EXTRACT_DATASET_NAMES_PROMPT

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        提取数据集名称

        Args:
            params: {"text": str}

        Returns:
            ToolResult 包含数据集名称列表
        """
        start_time = time.time()
        action_id = params.get("action_id", "unknown")

        try:
            text = params["text"]

            # 调用 LLM
            prompt = self.prompt_template.format(text=text)
            response = self.call_llm(prompt)

            # 解析响应
            result = self._parse_json_response(response)
            datasets = result.get("datasets", [])

            execution_time = time.time() - start_time

            return self._create_result(
                action_id=action_id,
                success=True,
                result={"datasets": datasets},
                execution_time=execution_time,
                metadata={"datasets_found": len(datasets)},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"数据集提取失败: {str(e)}")
            return self._create_result(
                action_id=action_id,
                success=False,
                result={"datasets": []},
                error_message=str(e),
                execution_time=execution_time,
            )

    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        import json
        import re

        try:
            return json.loads(response)
        except:
            pass

        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        return {"datasets": []}


class DatasetDetailsExtractorTool(BaseTool):
    """数据集详细信息提取工具"""

    def __init__(self):
        super().__init__("dataset_details_extractor")
        from llm_client import call_gpt4o_text
        from prompts import EXTRACT_DATASET_DETAILS_PROMPT

        self.call_llm = call_gpt4o_text
        self.prompt_template = EXTRACT_DATASET_DETAILS_PROMPT

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        提取数据集详细信息

        Args:
            params: {"dataset_name": str, "text": str, "urls": list}

        Returns:
            ToolResult 包含数据集详细信息
        """
        start_time = time.time()
        action_id = params.get("action_id", "unknown")

        try:
            dataset_name = params["dataset_name"]
            text = params["text"]
            urls = params.get("urls", [])

            # 调用 LLM
            prompt = self.prompt_template.format(
                dataset_name=dataset_name, text=text, urls="\n".join(urls)
            )
            response = self.call_llm(prompt)

            # 解析响应
            details = self._parse_json_response(response)

            execution_time = time.time() - start_time

            return self._create_result(
                action_id=action_id,
                success=True,
                result=details,
                execution_time=execution_time,
                metadata={
                    "has_link": bool(details.get("dataset_link")),
                    "has_description": bool(details.get("content")),
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"数据集详情提取失败: {str(e)}")
            return self._create_result(
                action_id=action_id,
                success=False,
                result=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        import json
        import re

        try:
            return json.loads(response)
        except:
            pass

        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        return {
            "content": "",
            "type": ["unspecified"],
            "domain": ["unspecified"],
            "fields": ["unspecified"],
            "dataset_link": "",
            "platform": "",
        }


class ToolManager:
    """
    工具管理器

    职责：
    1. 注册和管理所有工具
    2. 根据动作选择和执行工具
    3. 记录工具调用历史
    """

    def __init__(self):
        """初始化工具管理器"""
        self.tools: Dict[str, BaseTool] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # 注册所有工具
        self._register_default_tools()

        logger.info(f"工具管理器初始化完成，已注册 {len(self.tools)} 个工具")

    def _register_default_tools(self):
        """注册默认工具"""
        self.register_tool(ActionType.PARSE_PDF, PDFParserTool())
        self.register_tool(ActionType.EXTRACT_META, MetaExtractorTool())
        self.register_tool(ActionType.EXTRACT_DATASETS, DatasetFinderTool())
        self.register_tool(
            ActionType.EXTRACT_DATASET_DETAILS, DatasetDetailsExtractorTool()
        )

    def register_tool(self, action_type: ActionType, tool: BaseTool):
        """
        注册工具

        Args:
            action_type: 动作类型
            tool: 工具实例
        """
        self.tools[action_type.value] = tool
        logger.info(f"已注册工具: {tool.name} -> {action_type.value}")

    def execute_action(self, action: Action) -> ToolResult:
        """
        执行动作

        Args:
            action: 要执行的动作

        Returns:
            工具执行结果
        """
        logger.info(f"执行动作: {action.action_type.value}")

        # 查找对应的工具
        tool = self.tools.get(action.action_type.value)

        if not tool:
            logger.error(f"未找到对应工具: {action.action_type.value}")
            return ToolResult(
                action_id=action.action_id,
                success=False,
                result=None,
                error_message=f"未找到对应工具: {action.action_type.value}",
            )

        # 添加 action_id 到参数
        params = action.params.copy()
        params["action_id"] = action.action_id

        # 执行工具
        try:
            result = tool.execute(params)

            # 记录执行历史
            self.execution_history.append(
                {
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "tool_name": tool.name,
                    "success": result.success,
                    "execution_time": result.execution_time,
                }
            )

            logger.info(
                f"动作执行完成: {action.action_type.value} "
                f"({'成功' if result.success else '失败'})"
            )

            return result

        except Exception as e:
            logger.error(f"工具执行异常: {str(e)}", exc_info=True)
            return ToolResult(
                action_id=action.action_id,
                success=False,
                result=None,
                error_message=f"工具执行异常: {str(e)}",
            )

    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self.tools.keys())

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        if not self.execution_history:
            return {"total": 0, "success": 0, "failure": 0, "success_rate": 0.0}

        total = len(self.execution_history)
        success = sum(1 for h in self.execution_history if h["success"])
        failure = total - success

        return {
            "total": total,
            "success": success,
            "failure": failure,
            "success_rate": success / total if total > 0 else 0.0,
            "average_execution_time": sum(h["execution_time"] for h in self.execution_history)
            / total
            if total > 0
            else 0.0,
        }
