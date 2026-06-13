from typing import Literal

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="检查服务进程是否存活",
)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="检查服务是否可以接收流量",
)
async def readiness() -> HealthResponse:
    # External dependency probes will be added with their infrastructure adapters.
    return HealthResponse(status="ok")
