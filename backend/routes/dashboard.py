"""Dashboard endpoints: reports and statements CRUD via DynamoDB."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import ReportDetail, ReportSummaryItem, StatementItem
from routes.auth import get_current_user
from services.dynamo import (
    delete_report as dynamo_delete_report,
    delete_statement as dynamo_delete_statement,
    get_report,
    get_statement,
    list_reports,
    list_statements,
)
from services.storage import generate_presigned_url

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/reports", response_model=list[ReportSummaryItem])
async def get_reports(user: dict = Depends(get_current_user)):
    items = await list_reports(user["id"])
    return [ReportSummaryItem(**item) for item in items]


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report_detail(report_id: str, user: dict = Depends(get_current_user)):
    item = await get_report(user["id"], report_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate presigned URL for audio if available
    audio_url = None
    if item.get("audio_s3_key"):
        audio_url = await generate_presigned_url(item["audio_s3_key"])

    # Fetch statement metadata
    stmt_list = []
    for sid in item.get("statement_ids", []):
        stmt = await get_statement(user["id"], sid)
        if stmt:
            stmt_list.append({
                "id": stmt["statement_id"],
                "filename": stmt["filename"],
                "file_type": stmt.get("file_type", ""),
            })

    return ReportDetail(
        id=item["report_id"],
        title=item.get("title", "Financial Analysis"),
        created_at=item.get("created_at", ""),
        language=item.get("language", "en"),
        report=item["report"],
        podcast_script=item.get("podcast_script", ""),
        audio_url=audio_url,
        sentences=item.get("sentences", []),
        statements=stmt_list,
    )


@router.delete("/reports/{report_id}")
async def remove_report(report_id: str, user: dict = Depends(get_current_user)):
    ok = await dynamo_delete_report(user["id"], report_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"ok": True}


@router.get("/statements", response_model=list[StatementItem])
async def get_statements(user: dict = Depends(get_current_user)):
    items = await list_statements(user["id"])
    return [
        StatementItem(
            id=item["statement_id"],
            filename=item["filename"],
            uploaded_at=item.get("uploaded_at", ""),
            file_type=item.get("file_type", ""),
            file_size=item.get("file_size", 0),
        )
        for item in items
    ]


@router.delete("/statements/{statement_id}")
async def remove_statement(statement_id: str, user: dict = Depends(get_current_user)):
    ok = await dynamo_delete_statement(user["id"], statement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Statement not found")
    return {"ok": True}
