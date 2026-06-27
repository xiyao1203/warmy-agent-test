"""Webhook 通知服务。

任务完成时通过 Webhook POST 回调通知外部系统。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def send_webhook_notification(
    webhook_url: str,
    payload: dict[str, Any],
) -> bool:
    """发送 Webhook 通知，返回是否成功。"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code < 400:
                return True
            logger.warning("webhook %s returned %d", webhook_url, resp.status_code)
            return False
    except Exception:
        logger.exception("webhook %s failed", webhook_url)
        return False
