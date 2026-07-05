"""Verification routes — global consistency check and conflict resolution."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from fda_engine.api.deps import get_engine, get_state
from fda_engine.api.models import (
    ConflictItem,
    VerifyGlobalRequest,
    VerifyGlobalResponse,
    VerifyResolveRequest,
    VerifyResolveResponse,
)

router = APIRouter(prefix="/verify", tags=["verify"])


@router.post("/global", response_model=VerifyGlobalResponse)
async def verify_global(req: VerifyGlobalRequest):
    """Trigger global parameter consistency verification."""
    state = get_state()
    engine = state.engine

    if not state.truth_params:
        raise HTTPException(status_code=400, detail="No truth params available. Initialize workspace first.")

    if not state.generated_docs:
        raise HTTPException(status_code=400, detail="No documents generated yet.")

    target_docs = req.document_ids or list(state.generated_docs.keys())
    all_conflicts = []

    for doc_id in target_docs:
        if doc_id not in state.extracted_params:
            # Extract params from generated doc
            doc_content = state.generated_docs.get(doc_id, "")
            if doc_content:
                params = await engine.extract_parameters(doc_content)
                state.extracted_params[doc_id] = params

        doc_params = state.extracted_params.get(doc_id, {})

        # Build other docs params for horizontal comparison
        other_params = {
            k: v for k, v in state.extracted_params.items()
            if k != doc_id
        }

        conflicts = await engine.verify_consistency(
            draft_params=doc_params,
            truth_params=state.truth_params,
            other_docs_params=other_params,
        )

        for c in conflicts:
            c["doc_id"] = doc_id
            all_conflicts.append(ConflictItem(**{
                k: v for k, v in c.items()
                if k in ConflictItem.model_fields
            }))

    status = "conflict" if all_conflicts else "passed"

    return VerifyGlobalResponse(
        total_conflicts=len(all_conflicts),
        conflicts=all_conflicts,
        status=status,
    )


@router.post("/resolve", response_model=VerifyResolveResponse)
async def resolve_conflict(req: VerifyResolveRequest):
    """Resolve a conflict with human decision and cascade update."""
    state = get_state()
    engine = state.engine

    if req.param_name not in state.truth_params:
        raise HTTPException(status_code=400, detail=f"Parameter '{req.param_name}' not found in truth params.")

    old_value = state.truth_params[req.param_name].get("value", "")

    # Update truth params
    state.truth_params[req.param_name] = {
        "value": req.resolved_value,
        "confidence": 1.0,
        "source_context": "Human-resolved",
    }

    if not req.apply_to_all:
        return VerifyResolveResponse(
            param_name=req.param_name,
            resolved_value=req.resolved_value,
            documents_updated=0,
            status="resolved_local",
        )

    # Cascade update: find and rewrite all docs containing the old value
    docs_updated = 0
    for doc_id, content in list(state.generated_docs.items()):
        if old_value.lower() in content.lower():
            new_content = await engine.rewrite_paragraph(
                original_paragraph=content,
                old_value=old_value,
                new_value=req.resolved_value,
                context=f"Parameter: {req.param_name}",
            )
            state.generated_docs[doc_id] = new_content
            # Re-extract params after update
            state.extracted_params[doc_id] = await engine.extract_parameters(new_content)
            docs_updated += 1

    return VerifyResolveResponse(
        param_name=req.param_name,
        resolved_value=req.resolved_value,
        documents_updated=docs_updated,
        status="resolved_cascaded",
    )
