from fastapi import APIRouter
from mm_base6 import cbv

from app.core.types import AppView

router = APIRouter(prefix="/api/proxies", tags=["proxy"])


@cbv(router)
class CBV(AppView):
    @router.post("/update")
    async def update_proxies(self) -> int:
        return await self.core.services.proxy.update()
