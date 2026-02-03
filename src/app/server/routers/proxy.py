"""Proxy API endpoints."""

from fastapi import APIRouter
from mm_base6 import cbv

from app.core.types import AppView

router = APIRouter(prefix="/api/proxies", tags=["proxy"])


@cbv(router)
class CBV(AppView):
    """Proxy-related API endpoints."""

    @router.post("/update")
    async def update_proxies(self) -> int:
        """Trigger proxy list update."""
        return await self.core.services.proxy.update()
