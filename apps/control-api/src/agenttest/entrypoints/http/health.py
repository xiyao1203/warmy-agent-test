from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: Literal["control-api"] = "control-api"
    status: Literal["ok"] = "ok"
    version: str = "0.1.0"


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()
