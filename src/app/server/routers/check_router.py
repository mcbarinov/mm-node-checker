from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv

from app.core.db import Check
from app.server.deps import View

router = APIRouter(prefix="/api/checks", tags=["check"])


@cbv(router)
class CBV(View):
    @router.get("/{id}")
    async def get_check(self, id: ObjectId) -> Check:
        return await self.core.db.check.get(id)
