"""Core FDA engine wrapping agent_core's AgentLoop and AgentRunner."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger

from fda_engine.core.config import FDAConfig


class FDAEngine:
    """Headless AI engine for FDA document generation.

    Wraps agent_core's AgentLoop/AgentRunner to provide a pure API interface.
    No MessageBus, no channels, no interactive CLI — just process() calls.
    """

    def __init__(self, config: FDAConfig):
        self.config = config
        self._provider = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the LLM provider from config."""
        if self._initialized:
            return

        from agent_core.providers.factory import make_provider
        from agent_core.config.loader import load_config

        base_config = load_config()
        self._provider = make_provider(base_config)
        self._initialized = True
        logger.info("FDA engine initialized")

    async def generate_document(
        self,
        system_prompt: str,
        user_message: str,
        context_chunks: list[str] | None = None,
        max_iterations: int = 50,
    ) -> str:
        """Generate a single document using the LLM with tool execution.

        Args:
            system_prompt: The system prompt defining the document task.
            user_message: The user message with instructions/context.
            context_chunks: RAG-retrieved context chunks to include.
            max_iterations: Max LLM+tool iterations.

        Returns:
            Generated document content as string.
        """
        if not self._initialized:
            await self.initialize()

        from agent_core.agent.runner import AgentRunner, AgentRunSpec
        from agent_core.agent.tools.base import ToolResult
        from agent_core.agent.tools.registry import ToolRegistry

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context_chunks:
            context_text = "\n\n---\n\n".join(context_chunks)
            messages.append({
                "role": "user",
                "content": f"Reference materials:\n\n{context_text}",
            })

        messages.append({"role": "user", "content": user_message})

        from agent_core.config.loader import load_config
        from agent_core.providers.factory import make_provider
        base_config = load_config()
        model = base_config.agents.defaults.model
        provider = make_provider(base_config, model=model)

        spec = AgentRunSpec(
            initial_messages=messages,
            tools=ToolRegistry(),
            model=model,
            max_iterations=max_iterations,
            max_tool_result_chars=16000,
        )
        
        runner = AgentRunner(provider)
        result = await runner.run(spec)

        if result.error:
            logger.error(f"Document generation failed: {result.error}")
            raise RuntimeError(f"Generation failed: {result.error}")

        return result.final_content or ""

    async def extract_product_details(self, document_text: str) -> dict[str, Any]:
        """Extract detailed product information from technical documents.
        
        This extracts ACTUAL product information from the source documents,
        not just classification characteristics.
        """
        if not self._initialized:
            await self.initialize()

        system_prompt = (
            "你是一名医疗器械技术资料分析专家。\n"
            "请从以下产品技术资料中，提取完整的产品信息。\n\n"
            "【必须提取的信息】\n"
            "请返回JSON格式，包含以下字段（尽量从资料中提取真实内容）：\n\n"
            "{\n"
            '  "product_name": "产品名称（中文全称）",\n'
            '  "product_name_en": "产品英文名称",\n'
            '  "model": "产品型号",\n'
            '  "specifications": "产品规格（如尺寸、重量等）",\n'
            '  "intended_use": "预期用途（详细描述）",\n'
            '  "indications": "适用范围",\n'
            '  "contraindications": "禁忌症",\n'
            '  "warnings": "注意事项",\n'
            '  "structure": "结构组成（主要部件及功能描述）",\n'
            '  "principle": "工作原理",\n'
            '  "performance": {\n'
            '    "measurement_range": "测量范围",\n'
            '    "accuracy": "测量精度",\n'
            '    "resolution": "分辨率",\n'
            '    "response_time": "响应时间",\n'
            '    "battery_life": "电池续航",\n'
            '    "storage_capacity": "存储容量"\n'
            '  },\n'
            '  "materials": "主要材料",\n'
            '  "dimensions": "外形尺寸",\n'
            '  "weight": "产品重量",\n'
            '  "power": "供电方式",\n'
            '  "connectivity": "连接方式",\n'
            '  "software_version": "软件版本",\n'
            '  "environment": {\n'
            '    "working_temp": "工作温度",\n'
            '    "working_humidity": "工作湿度",\n'
            '    "storage_temp": "储存温度"\n'
            '  },\n'
            '  "standards": ["适用的标准列表"],\n'
            '  "accessories": "配件清单",\n'
            '  "shelf_life": "有效期",\n'
            '  "manufacturer": "生产企业"\n'
            "}\n\n"
            "【重要】\n"
            "- 请从资料中提取真实信息，不要编造\n"
            "- 如果资料中没有某项信息，填写\"待补充\"\n"
            "- 保留原始数据的准确性\n"
            "- 返回 ONLY valid JSON"
        )

        result = await self.generate_document(
            system_prompt=system_prompt,
            user_message=f"请从以下产品技术资料中提取完整的产品信息：\n\n{document_text[:12000]}",
            max_iterations=10,
        )

        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse product details as JSON")
            return {"error": "解析失败", "raw": result}

    async def analyze_product(self, document_text: str) -> dict[str, Any]:
        """Analyze product to determine characteristics for document generation.
        
        Identifies: product_type, sterility, device_class, product_category,
        applicable_standards, required_documents, etc.
        
        Returns:
            Dict of product characteristics.
        """
        if not self._initialized:
            await self.initialize()

        system_prompt = (
            "你是一名医疗器械法规专家。分析以下产品资料，确定产品特征。\n"
            "请返回JSON格式，包含以下字段：\n"
            "{\n"
            '  "product_name": "产品名称",\n'
            '  "product_type": "有源/无源/体外诊断",\n'
            '  "sterility": "无菌/非无菌",\n'
            '  "device_class": "一类/二类/三类",\n'
            '  "product_category": "如 07-03-03",\n'
            '  "applicable_standards": ["适用标准列表"],\n'
            '  "has_software": true/false,\n'
            '  "has_battery": true/false,\n'
            '  "has_wireless": true/false,\n'
            '  "invasiveness": "非侵入/微创/侵入",\n'
            '  "contact_duration": "有限接触/长期接触/永久接触",\n'
            '  "contact_tissue": "表面/外部沟通/植入",\n'
            '  "required_documents": ["必须提交的文件列表"]\n'
            "}\n\n"
            "根据产品特征，确定 required_documents 应包含哪些注册申报文件。\n"
            "例如：有源医疗器械需要电气安全报告；无菌产品需要灭菌验证报告。\n"
            "返回 ONLY valid JSON."
        )

        result = await self.generate_document(
            system_prompt=system_prompt,
            user_message=f"请分析以下产品资料：\n\n{document_text[:8000]}",
            max_iterations=5,
        )

        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse product characteristics as JSON")
            return {
                "product_name": "未知产品",
                "product_type": "有源",
                "sterility": "非无菌",
                "device_class": "二类",
                "has_software": False,
                "has_battery": False,
                "has_wireless": False,
                "required_documents": []
            }

    async def extract_parameters(self, document_text: str) -> dict[str, Any]:
        """Extract key-value parameter matrix from a document.

        Uses LLM to identify technical parameters like:
        - sterilization method, shelf life, materials, dimensions, etc.

        Returns:
            Dict of {param_name: {value, confidence, source_context}}.
        """
        if not self._initialized:
            await self.initialize()

        system_prompt = (
            "You are a FDA technical parameter extractor. "
            "Extract ALL technical parameters from the given document. "
            "Return a JSON object where each key is a parameter name (snake_case) "
            "and each value is an object with: value (string), confidence (0-1), "
            "source_context (the sentence containing this parameter). "
            "Common parameters to look for: sterilization_method, shelf_life, "
            "material, dimensions, weight, biocompatibility, electrical_safety, "
            "performance_specifications, intended_use, indications_for_use, "
            "patient_population, mechanism_of_action, regulatory_class, "
            "product_code, regulation_number. "
            "Return ONLY valid JSON, no other text."
        )

        result = await self.generate_document(
            system_prompt=system_prompt,
            user_message=f"Extract parameters from:\n\n{document_text}",
            max_iterations=5,
        )

        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted parameters as JSON")
            return {}

    async def rewrite_paragraph(
        self,
        original_paragraph: str,
        old_value: str,
        new_value: str,
        context: str = "",
    ) -> str:
        """Rewrite a paragraph to replace a parameter value.

        Used for cascade updates after conflict resolution.
        """
        if not self._initialized:
            await self.initialize()

        system_prompt = (
            "You are a technical document editor. "
            "Rewrite the given paragraph to replace the old parameter value with the new one. "
            "Maintain the same tone, style, and technical accuracy. "
            "Only change what is necessary — do not add or remove information. "
            "Return ONLY the rewritten paragraph."
        )

        user_message = (
            f"Original paragraph:\n{original_paragraph}\n\n"
            f"Replace '{old_value}' with '{new_value}'.\n"
        )
        if context:
            user_message += f"Additional context: {context}\n"

        return await self.generate_document(
            system_prompt=system_prompt,
            user_message=user_message,
            max_iterations=5,
        )

    async def verify_consistency(
        self,
        draft_params: dict[str, Any],
        truth_params: dict[str, Any],
        other_docs_params: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Verify parameter consistency across documents.

        Args:
            draft_params: Parameters extracted from the draft document.
            truth_params: The ground truth parameters from source files.
            other_docs_params: Parameters from other generated documents.

        Returns:
            List of conflict dicts with details.
        """
        conflicts = []

        # Vertical comparison: draft vs truth
        for param_name, draft_info in draft_params.items():
            if param_name in truth_params:
                truth_value = truth_params[param_name].get("value", "")
                draft_value = draft_info.get("value", "")
                if str(truth_value).lower().strip() != str(draft_value).lower().strip():
                    conflicts.append({
                        "param_name": param_name,
                        "source_value": str(truth_value),
                        "draft_value": str(draft_value),
                        "comparison_type": "vertical",
                        "context": draft_info.get("source_context", ""),
                        "suggestion": f"Replace '{draft_value}' with '{truth_value}'",
                    })

        # Horizontal comparison: draft vs other docs
        if other_docs_params:
            for doc_name, doc_params in other_docs_params.items():
                for param_name, draft_info in draft_params.items():
                    if param_name in doc_params:
                        other_value = doc_params[param_name].get("value", "")
                        draft_value = draft_info.get("value", "")
                        if str(other_value).lower().strip() != str(draft_value).lower().strip():
                            conflicts.append({
                                "param_name": param_name,
                                "source_value": str(other_value),
                                "draft_value": str(draft_value),
                                "comparison_type": "horizontal",
                                "other_doc": doc_name,
                                "context": draft_info.get("source_context", ""),
                                "suggestion": f"Align with '{doc_name}': use '{other_value}'",
                            })

        return conflicts
