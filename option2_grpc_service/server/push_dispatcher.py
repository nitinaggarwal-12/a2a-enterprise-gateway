"""Push Notification Dispatcher for Out-of-Band AIP-127 Task Callbacks.

Delivers HTTP POST webhooks to the configured push target with HMAC authentication
upon task completion or asynchronous milestone progression.
"""

import asyncio
import hmac
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("grpc_push_dispatcher")


async def deliver_task_push_notification(
    url: str,
    task_id: str,
    state: str,
    output_data: Dict[str, Any],
    token: Optional[str] = None,
    secret_key: str = "Enterprise-a2a-grpc-push-key-2026",
) -> bool:
    """Deliver push notification payload to the specified AIP-127 push URL."""
    if not url:
        return False

    payload = {
        "taskId": task_id,
        "state": state,
        "timestamp": int(time.time()),
        "output": output_data,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    # Generate HMAC-SHA256 signature for payload integrity
    signature = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Enterprise-Signature": f"sha256={signature}",
        "X-AIP127-Delivery": "a2a.v1.push",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, content=payload_bytes, headers=headers)
            logger.info(
                f"[PushDispatcher] Dispatched notification for {task_id} to {url}. Status: {resp.status_code}"
            )
            return resp.status_code in (200, 201, 202, 204)
    except Exception as exc:
        logger.error(f"[PushDispatcher] Failed delivering notification to {url}: {str(exc)}")
        return False


def dispatch_in_background(
    url: str,
    task_id: str,
    state: str,
    output_data: Dict[str, Any],
    token: Optional[str] = None,
):
    """Schedule asynchronous task push in background event loop."""
    asyncio.create_task(
        deliver_task_push_notification(
            url=url,
            task_id=task_id,
            state=state,
            output_data=output_data,
            token=token,
        )
    )
