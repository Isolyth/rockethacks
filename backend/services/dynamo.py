"""DynamoDB operations for reports and statements."""

import asyncio
import json
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    DYNAMO_REPORTS_TABLE,
    DYNAMO_STATEMENTS_TABLE,
)

logger = logging.getLogger("uvicorn.error")

_dynamodb = None


def _get_dynamodb():
    global _dynamodb
    if _dynamodb is None and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        _dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
    return _dynamodb


def _reports_table():
    db = _get_dynamodb()
    return db.Table(DYNAMO_REPORTS_TABLE) if db else None


def _statements_table():
    db = _get_dynamodb()
    return db.Table(DYNAMO_STATEMENTS_TABLE) if db else None


def _decimal_to_num(obj):
    """Convert DynamoDB Decimal values back to int/float for JSON serialization."""
    if isinstance(obj, list):
        return [_decimal_to_num(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _decimal_to_num(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    return obj


# --- Reports ---

async def save_report(user_id: str, report_id: str, data: dict) -> bool:
    """Save a report to DynamoDB. `data` must include all fields except keys."""
    table = _reports_table()
    if table is None:
        return False

    item = {
        "user_id": user_id,
        "report_id": report_id,
        "created_at": data["created_at"],
        "language": data.get("language", "en"),
        "title": data.get("title", "Financial Analysis"),
        "report_json": json.dumps(data["report"]),
        "podcast_script": data.get("podcast_script", ""),
        "audio_s3_key": data.get("audio_s3_key") or "",
        "statement_ids": data.get("statement_ids", []),
    }

    await asyncio.to_thread(table.put_item, Item=item)
    return True


async def list_reports(user_id: str) -> list[dict]:
    table = _reports_table()
    if table is None:
        return []

    resp = await asyncio.to_thread(
        table.query,
        KeyConditionExpression=Key("user_id").eq(user_id),
    )
    items = resp.get("Items", [])

    results = []
    for item in items:
        report = json.loads(item.get("report_json", "{}"))
        summary = report.get("summary", {})
        results.append({
            "id": item["report_id"],
            "title": item.get("title", "Financial Analysis"),
            "created_at": item.get("created_at", ""),
            "language": item.get("language", "en"),
            "total_income": summary.get("total_income", 0),
            "total_expenses": summary.get("total_expenses", 0),
            "net_savings": summary.get("net_savings", 0),
        })

    results.sort(key=lambda r: r["created_at"], reverse=True)
    return results


async def get_report(user_id: str, report_id: str) -> dict | None:
    table = _reports_table()
    if table is None:
        return None

    resp = await asyncio.to_thread(
        table.get_item,
        Key={"user_id": user_id, "report_id": report_id},
    )
    item = resp.get("Item")
    if item is None:
        return None

    item = _decimal_to_num(item)
    item["report"] = json.loads(item.pop("report_json", "{}"))
    return item


async def delete_report(user_id: str, report_id: str) -> bool:
    table = _reports_table()
    if table is None:
        return False

    await asyncio.to_thread(
        table.delete_item,
        Key={"user_id": user_id, "report_id": report_id},
    )
    return True


# --- Statements ---

async def save_statement(user_id: str, statement_id: str, data: dict) -> bool:
    table = _statements_table()
    if table is None:
        return False

    item = {
        "user_id": user_id,
        "statement_id": statement_id,
        "uploaded_at": data["uploaded_at"],
        "filename": data["filename"],
        "s3_key": data.get("s3_key", ""),
        "file_size": data.get("file_size", 0),
        "file_type": data.get("file_type", ""),
    }

    await asyncio.to_thread(table.put_item, Item=item)
    return True


async def list_statements(user_id: str) -> list[dict]:
    table = _statements_table()
    if table is None:
        return []

    resp = await asyncio.to_thread(
        table.query,
        KeyConditionExpression=Key("user_id").eq(user_id),
    )
    items = _decimal_to_num(resp.get("Items", []))
    items.sort(key=lambda s: s.get("uploaded_at", ""), reverse=True)
    return items


async def get_statement(user_id: str, statement_id: str) -> dict | None:
    table = _statements_table()
    if table is None:
        return None

    resp = await asyncio.to_thread(
        table.get_item,
        Key={"user_id": user_id, "statement_id": statement_id},
    )
    item = resp.get("Item")
    return _decimal_to_num(item) if item else None


async def delete_statement(user_id: str, statement_id: str) -> bool:
    table = _statements_table()
    if table is None:
        return False

    await asyncio.to_thread(
        table.delete_item,
        Key={"user_id": user_id, "statement_id": statement_id},
    )
    return True


async def ensure_tables():
    """Create DynamoDB tables if they don't exist. No-op if AWS not configured."""
    db = _get_dynamodb()
    if db is None:
        logger.info("AWS DynamoDB not configured — running in guest-only mode")
        return

    client = db.meta.client
    existing = (await asyncio.to_thread(client.list_tables))["TableNames"]

    for table_name, key_schema, attr_defs in [
        (
            DYNAMO_REPORTS_TABLE,
            [{"AttributeName": "user_id", "KeyType": "HASH"},
             {"AttributeName": "report_id", "KeyType": "RANGE"}],
            [{"AttributeName": "user_id", "AttributeType": "S"},
             {"AttributeName": "report_id", "AttributeType": "S"}],
        ),
        (
            DYNAMO_STATEMENTS_TABLE,
            [{"AttributeName": "user_id", "KeyType": "HASH"},
             {"AttributeName": "statement_id", "KeyType": "RANGE"}],
            [{"AttributeName": "user_id", "AttributeType": "S"},
             {"AttributeName": "statement_id", "AttributeType": "S"}],
        ),
    ]:
        if table_name not in existing:
            logger.info(f"Creating DynamoDB table: {table_name}")
            await asyncio.to_thread(
                client.create_table,
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attr_defs,
                BillingMode="PAY_PER_REQUEST",
            )
            logger.info(f"Created DynamoDB table: {table_name}")
        else:
            logger.info(f"DynamoDB table already exists: {table_name}")
