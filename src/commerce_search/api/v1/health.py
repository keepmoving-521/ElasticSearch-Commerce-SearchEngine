import asyncio
from collections.abc import Awaitable
from time import perf_counter
from typing import Literal

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from commerce_search.api.schemas import ApiResponse, success_response
from commerce_search.infrastructure.dependencies import InfrastructureDep, SettingsDep
from commerce_search.shared.exceptions import ServiceUnavailableError
from commerce_search.shared.middleware import get_request_id

router = APIRouter()


class HealthData(BaseModel):
    status: Literal["ok"]


class ComponentHealth(BaseModel):
    status: Literal["ok"]
    latency_ms: float


class ReadinessData(HealthData):
    components: dict[str, ComponentHealth]


async def probe_component(
    operation: Awaitable[None],
    *,
    timeout_seconds: float,
) -> float:
    started_at = perf_counter()
    await asyncio.wait_for(operation, timeout=timeout_seconds)
    return round((perf_counter() - started_at) * 1000, 2)


@router.get(
    "/live",
    response_model=ApiResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="检查服务进程是否存活",
)
async def liveness(request: Request) -> ApiResponse[HealthData]:
    return success_response(
        HealthData(status="ok"),
        request_id=get_request_id(request),
    )


@router.get(
    "/ready",
    response_model=ApiResponse[ReadinessData],
    status_code=status.HTTP_200_OK,
    summary="检查服务是否可以接收流量",
)
async def readiness(
    request: Request,
    clients: InfrastructureDep,
    settings: SettingsDep,
) -> ApiResponse[ReadinessData]:
    probes = {
        "database": clients.database.ping(),
        "elasticsearch": clients.elasticsearch.ping(),
        "redis": clients.redis.ping(),
        "kafka": clients.kafka.ping(),
    }
    results = await asyncio.gather(
        *(
            probe_component(
                operation,
                timeout_seconds=settings.health_check_timeout_seconds,
            )
            for operation in probes.values()
        ),
        return_exceptions=True,
    )
    failed_components = [
        {
            "field": component,
            "message": (
                "Dependency health check timed out"
                if isinstance(result, TimeoutError)
                else "Dependency health check failed"
            ),
            "type": type(result).__name__,
        }
        for component, result in zip(probes, results, strict=True)
        if isinstance(result, BaseException)
    ]
    if failed_components:
        raise ServiceUnavailableError(
            "One or more infrastructure dependencies are unavailable",
            code="INFRASTRUCTURE_UNAVAILABLE",
            errors=failed_components,
        )

    return success_response(
        ReadinessData(
            status="ok",
            components={
                component: ComponentHealth(
                    status="ok",
                    latency_ms=latency,
                )
                for component, latency in zip(probes, results, strict=True)
                if isinstance(latency, float)
            },
        ),
        request_id=get_request_id(request),
    )
