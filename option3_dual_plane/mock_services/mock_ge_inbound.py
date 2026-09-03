"""Mock Gemini Enterprise Inbound Webhook Receiver.

Simulates GE's incoming push endpoint that displays interactive A2UI review cards
in the Medical Director's Gemini Enterprise workspace / chat canvas.
"""

import json
import logging
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

logger = logging.getLogger("mock_ge_inbound")
app = FastAPI(title="Mock Gemini Enterprise Inbound Webhook Receiver")

# In-memory store for delivered cards
RECEIVED_CARDS: List[Dict[str, Any]] = []


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "mock-ge-inbound"}


@app.post("/api/v1/ge/inbound-webhook")
async def receive_inbound_card(request: Request):
    """Receive A2UI approval card pushed from Enterprise Plane 2 Bridge Service."""
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {str(exc)}")

    RECEIVED_CARDS.append(body)
    card_id = body.get("cardId") or body.get("a2ui", {}).get("id") or "unknown"
    logger.info(f" Successfully received inbound A2UI card in Gemini Enterprise: {card_id}")

    return {
        "status": "DELIVERED_TO_USER_SURFACE",
        "cardId": card_id,
        "displayedInWorkspace": True,
        "recipient": "medical_director@enterprise.internal",
    }


@app.get("/api/v1/ge/received-cards")
async def get_received_cards():
    """Inspection endpoint for test automation harnesses."""
    return {"count": len(RECEIVED_CARDS), "cards": RECEIVED_CARDS}


@app.delete("/api/v1/ge/received-cards")
async def clear_received_cards():
    """Clear recorded cards for clean test execution."""
    RECEIVED_CARDS.clear()
    return {"cleared": True}
