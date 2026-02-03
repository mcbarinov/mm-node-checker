"""Check API endpoints."""

from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv

from app.core.db import Check
from app.core.types import AppView

router = APIRouter(prefix="/api/checks", tags=["check"])


@cbv(router)
class CBV(AppView):
    """Check-related API endpoints."""

    @router.get("/{id}")
    async def get_check(self, id: ObjectId) -> Check:
        """Get a check by ID."""
        return await self.core.db.check.get(id)
