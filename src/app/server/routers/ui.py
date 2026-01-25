from typing import Annotated

from fastapi import APIRouter, Form, Query
from mm_base6 import cbv, redirect
from mm_web3 import Network
from pydantic import BaseModel, BeforeValidator
from starlette.responses import HTMLResponse, RedirectResponse

from app.core.types import AppView


def empty_to_none(v: str | None) -> str | None:
    if v == "":
        return None
    return v


router = APIRouter(include_in_schema=False)


@cbv(router)
class PageCBV(AppView):
    @router.get("/")
    async def index(self) -> HTMLResponse:
        return await self.render.html("index.j2")

    @router.get("/nodes")
    async def nodes(self, network: Annotated[Network | None, BeforeValidator(empty_to_none), Query()] = None) -> HTMLResponse:
        query = {}
        if network:
            query["network"] = network
        nodes = await self.core.db.node.find(query, "network")
        return await self.render.html("nodes.j2", form={"network": network}, nodes=nodes)

    @router.get("/networks")
    async def networks(self) -> HTMLResponse:
        info = await self.core.services.node.get_networks_info()
        return await self.render.html("networks.j2", info=info)

    @router.get("/checks")
    async def checks(self) -> HTMLResponse:
        checks = await self.core.db.check.find({}, "created_at", limit=1000)
        return await self.render.html("checks.j2", checks=checks)


@cbv(router)
class ActionCBV(AppView):
    class AddNodes(BaseModel):
        network: Network
        urls: str

    @router.post("/nodes")
    async def add_nodes(self, form: Annotated[AddNodes, Form()]) -> RedirectResponse:
        res = await self.core.services.node.add(form.network, form.urls)
        self.render.flash(f"nodes added: {res}")
        return redirect("/nodes")

    @router.post("/nodes/import")
    async def import_nodes(self, toml: Annotated[str, Form()]) -> RedirectResponse:
        res = await self.core.services.node.import_from_toml(toml)
        self.render.flash(f"nodes imported: {res}")
        return redirect("/nodes")
