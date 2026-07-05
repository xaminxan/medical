"""Workspace initialization route."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from fda_engine.api.deps import get_engine, get_state
from fda_engine.api.models import WorkspaceInitRequest, WorkspaceInitResponse

router = APIRouter(prefix="/workspace", tags=["workspace"])


async def _init_workspace_bg(folder_path: str, template: str):
    """Background task for workspace initialization."""
    from loguru import logger

    state = get_state()
    engine = state.engine

    try:
        folder = Path(folder_path).expanduser().resolve()
        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            return

        state.workspace_path = folder

        # Index documents
        from fda_engine.ingestion.workspace import index_workspace
        doc_count = await index_workspace(folder, state.config)

        # Load all text for analysis
        all_text = _load_all_text(folder)
        
        # Store raw text for detailed extraction
        state.raw_document_text = all_text

        logger.info(f"Workspace initialized: {doc_count} docs, text length: {len(all_text)}")
    except Exception as e:
        logger.exception(f"Workspace init failed: {e}")


def _load_all_text(folder: Path) -> str:
    """Load all readable text from a folder."""
    texts = []
    for ext in ("*.md", "*.txt", "*.csv"):
        for f in folder.rglob(ext):
            try:
                texts.append(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    for f in folder.rglob("*.pdf"):
        try:
            import pymupdf
            doc = pymupdf.open(str(f))
            texts.append("\n".join(page.get_text() for page in doc))
        except Exception:
            pass
    for f in folder.rglob("*.docx"):
        try:
            from docx import Document
            doc = Document(str(f))
            texts.append("\n".join(p.text for p in doc.paragraphs))
        except Exception:
            pass
    return "\n\n---\n\n".join(texts)


@router.post("/init", response_model=WorkspaceInitResponse)
async def init_workspace(req: WorkspaceInitRequest, bg: BackgroundTasks):
    """Initialize workspace from a folder of technical documents."""
    folder = Path(req.folder_path).expanduser().resolve()
    if not folder.exists():
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {folder}")

    state = get_state()
    state.config.fda_template = req.fda_template
    
    # Auto-detect language from template
    if req.fda_template in ("nmpa", "qtms_nmpa"):
        state.config.language = "zh"
    else:
        state.config.language = "en"

    bg.add_task(_init_workspace_bg, str(folder), req.fda_template)

    return WorkspaceInitResponse(
        workspace_id=folder.name,
        workspace_path=str(folder),
        documents_indexed=0,
        parameters_extracted={},
        product_characteristics={},
        status="initializing",
        language=state.config.language,
    )


@router.post("/analyze")
async def analyze_product():
    """Analyze product and extract detailed information from documents."""
    from loguru import logger
    
    state = get_state()
    
    if not state.workspace_path:
        raise HTTPException(status_code=400, detail="Workspace not initialized.")
    
    try:
        # Get text from stored raw text or reload
        all_text = getattr(state, 'raw_document_text', '') or _load_all_text(state.workspace_path)
        
        if not all_text.strip():
            return {"status": "no_text", "message": "No readable text found in folder"}
        
        engine = state.engine
        
        # Step 1: Extract detailed product information
        logger.info("Extracting detailed product information...")
        product_details = await engine.extract_product_details(all_text[:12000])
        state.product_details = product_details
        
        # Step 2: Extract basic characteristics for classification
        logger.info("Analyzing product characteristics...")
        characteristics = await engine.analyze_product(all_text[:8000])
        state.product_characteristics = characteristics
        
        # Merge details into characteristics for frontend
        characteristics['details'] = product_details
        
        logger.info(f"Product analyzed: {characteristics.get('product_name', 'unknown')}")
        return {"status": "success", "characteristics": characteristics}
    except Exception as e:
        logger.exception(f"Product analysis failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/chat")
async def chat_with_assistant(request: dict):
    """Real-time chat with FDA/NMPA regulatory assistant."""
    from loguru import logger
    
    message = request.get("message", "")
    context = request.get("context", "general")
    
    state = get_state()
    engine = state.engine
    lang = state.config.language
    template = state.config.fda_template
    product_chars = state.product_characteristics
    
    # Build system prompt based on context
    if lang == "zh":
        if context == "fill_missing":
            system_prompt = (
                "你是一名医疗器械注册申报助手。\n"
                "用户正在填写申报资料中的缺失信息。\n"
                "请根据用户提供的信息，帮助生成符合法规要求的内容。\n"
                "确保内容专业、准确，符合相关法规要求。\n\n"
                "【输出格式要求】\n"
                "- 使用Markdown格式\n"
                "- 重要信息使用表格展示\n"
                "- 使用列表清晰列出要点\n"
                "- 使用**加粗**突出关键信息\n"
                "- 段落之间空一行\n\n"
                f"当前产品信息：{product_chars}\n"
            )
        elif context == "quality_system":
            system_prompt = (
                "你是一名ISO 13485质量管理体系专家。\n"
                "用户正在建立质量管理体系。\n"
                "请根据用户的问题，提供专业的质量体系咨询服务。\n"
                "确保建议符合ISO 13485:2016标准要求。\n\n"
                "【输出格式要求】\n"
                "- 使用Markdown格式\n"
                "- 文件清单用表格展示\n"
                "- 条款引用要准确\n"
                "- 使用层级结构展示\n\n"
                f"当前产品信息：{product_chars}\n"
            )
        else:
            system_prompt = (
                "你是一名医疗器械注册申报专家。\n"
                "精通FDA 510(k)和NMPA医疗器械注册流程。\n"
                "请根据用户的问题，提供专业的法规咨询服务。\n"
                "确保建议准确、专业，符合相关法规要求。\n\n"
                "【输出格式要求】\n"
                "- 使用Markdown格式\n"
                "- 数据对比用表格展示\n"
                "- 步骤流程用有序列表\n"
                "- 要点用无序列表\n"
                "- 重要信息**加粗**\n"
                "- 段落之间空一行\n\n"
                f"当前产品信息：{product_chars}\n"
                f"当前模板：{template}\n"
            )
    else:
        system_prompt = (
            "You are a FDA regulatory expert specializing in 510(k) submissions.\n"
            "Provide professional regulatory consultation based on user questions.\n"
            "Ensure advice is accurate and compliant with FDA regulations.\n\n"
            "OUTPUT FORMAT:\n"
            "- Use Markdown format\n"
            "- Use tables for data comparison\n"
            "- Use numbered lists for steps\n"
            "- Use bullet lists for key points\n"
            "- **Bold** important information\n"
            "- Add blank lines between paragraphs\n\n"
            f"Current product information: {product_chars}\n"
            f"Current template: {template}\n"
        )
    
    try:
        # Add conversation history if available
        if not hasattr(state, 'chat_history'):
            state.chat_history = []
        
        # Generate response
        response = await engine.generate_document(
            system_prompt=system_prompt,
            user_message=message,
            max_iterations=10,
        )
        
        # Save to history
        state.chat_history.append({"role": "user", "content": message})
        state.chat_history.append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "context": context,
        }
    except Exception as e:
        logger.exception(f"Chat failed: {e}")
        return {"error": str(e)}


@router.post("/save-company-products")
async def save_company_products(request: dict):
    """Save comprehensive company information for QMS generation."""
    from loguru import logger
    
    state = get_state()
    
    # Save all company information
    state.company_info = {
        "name": request.get("name", ""),
        "size": request.get("size", ""),
        "employees": request.get("employees", ""),
        "address": request.get("address", ""),
        "productionAddress": request.get("productionAddress", ""),
        "departments": request.get("departments", {}),
        "products": request.get("products", []),
        "business": request.get("business", ""),
    }
    
    # Also save products separately for convenience
    state.company_products = request.get("products", [])
    state.company_name = request.get("name", "")
    
    logger.info(f"Saved company info: {state.company_info['name']}, {len(state.company_products)} products")
    return {"status": "success", "count": len(state.company_products)}


@router.post("/analyze-qms")
async def analyze_existing_qms(request: dict):
    """Analyze existing QMS documents in a folder and identify gaps."""
    from loguru import logger
    from pathlib import Path
    
    state = get_state()
    folder_path = request.get("folder_path", "")
    
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        return {"status": "error", "message": f"文件夹不存在: {folder_path}"}
    
    if not folder.is_dir():
        return {"status": "error", "message": f"不是文件夹: {folder_path}"}
    
    # Scan for existing QMS documents
    existing_docs = {
        "quality_manual": [],
        "procedures": [],
        "work_instructions": [],
        "forms": [],
        "other": []
    }
    
    for f in folder.rglob("*"):
        if f.is_file():
            name = f.name.lower()
            if "质量手册" in name or "quality_manual" in name or name.startswith("qm"):
                existing_docs["quality_manual"].append(str(f.relative_to(folder)))
            elif "程序文件" in name or "procedure" in name or "qp" in name:
                existing_docs["procedures"].append(str(f.relative_to(folder)))
            elif "作业指导" in name or "work_instruction" in name or "wi" in name:
                existing_docs["work_instructions"].append(str(f.relative_to(folder)))
            elif "记录" in name or "form" in name or "fm" in name:
                existing_docs["forms"].append(str(f.relative_to(folder)))
            elif f.suffix in (".doc", ".docx", ".pdf", ".md", ".txt"):
                existing_docs["other"].append(str(f.relative_to(folder)))
    
    # Build analysis report
    total_docs = sum(len(v) for v in existing_docs.values())
    
    analysis = f"**文件夹：** {folder_path}\n\n"
    analysis += f"**找到文件总数：** {total_docs} 个\n\n"
    analysis += "| 文件类型 | 数量 | 状态 |\n|----------|------|------|\n"
    analysis += f"| 质量手册 | {len(existing_docs['quality_manual'])} | {'✅ 有' if existing_docs['quality_manual'] else '❌ 缺失'} |\n"
    analysis += f"| 程序文件 | {len(existing_docs['procedures'])} | {'✅ 有' if existing_docs['procedures'] else '❌ 缺失'} |\n"
    analysis += f"| 作业指导书 | {len(existing_docs['work_instructions'])} | {'✅ 有' if existing_docs['work_instructions'] else '❌ 缺失'} |\n"
    analysis += f"| 记录表格 | {len(existing_docs['forms'])} | {'✅ 有' if existing_docs['forms'] else '❌ 缺失'} |\n"
    analysis += f"| 其他文件 | {len(existing_docs['other'])} | - |\n\n"
    
    # List existing files
    if existing_docs["procedures"]:
        analysis += "**已有程序文件：**\n"
        for f in existing_docs["procedures"][:10]:
            analysis += f"- {f}\n"
        if len(existing_docs["procedures"]) > 10:
            analysis += f"- ... 共 {len(existing_docs['procedures'])} 个\n"
    
    # Identify gaps
    required_procs = ["文件控制", "记录控制", "管理评审", "设计控制", "采购控制", "生产控制", "不合格品", "纠正措施", "内部审核"]
    missing = []
    for proc in required_procs:
        found = False
        for f in existing_docs["procedures"]:
            if proc in f:
                found = True
                break
        if not found:
            missing.append(proc)
    
    if missing:
        analysis += f"\n**缺失的程序文件：**\n"
        for m in missing:
            analysis += f"- ❌ {m}程序\n"
    
    analysis += "\n**建议操作：**\n"
    analysis += "1. 补充缺失的程序文件\n"
    analysis += "2. 更新现有文件中的产品信息\n"
    analysis += "3. 确保所有文件引用最新法规版本\n"
    
    # Store analysis in state
    state.existing_qms_analysis = existing_docs
    
    return {"status": "success", "analysis": analysis, "existing_docs": existing_docs}
