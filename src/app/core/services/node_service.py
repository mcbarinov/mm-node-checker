import logging
import time
from typing import cast

import anyio
import pydash
from bson import ObjectId
from mm_crypto_utils import Network, NetworkType, random_proxy
from mm_std import Result, async_synchronized, ok, utc_delta, utc_now
from pydantic import BaseModel

from app.core import rpc
from app.core.db import Check, Node, NodeStatus
from app.core.types_ import AppService, AppServiceParams

logger = logging.getLogger(__name__)


class NetworkInfo(BaseModel):
    network: Network
    all_nodes: int
    live_nodes: int


class NodeService(AppService):
    def __init__(self, base_params: AppServiceParams) -> None:
        super().__init__(base_params)

    @async_synchronized
    async def add(self, network: Network, urls_multiline: str) -> int:
        result = 0
        urls = [url.strip().removesuffix("/") for url in urls_multiline.splitlines() if url.strip()]
        urls = pydash.uniq(urls)
        for url in urls:
            if await self.db.node.exists({"url": url}):
                continue
            await self.db.node.insert_one(Node(id=ObjectId(), network=network, url=url))
            result += 1

        return result

    async def check(self, id: ObjectId) -> Result[int]:
        node = await self.db.node.get(id)
        logger.info("check", extra={"url": node.url, "network": node.network.value})

        proxy = random_proxy(self.dvalue.proxies)

        start_time = time.perf_counter()
        match node.network.network_type:
            case NetworkType.EVM:
                res = await rpc.get_evm_height(node.url, proxy=proxy)
            case NetworkType.SOLANA:
                res = await rpc.get_solana_height(node.url, proxy=proxy)
            case NetworkType.APTOS:
                res = await rpc.get_aptos_height(node.url, proxy=proxy)
            case NetworkType.STARKNET:
                res = await rpc.get_starknet_height(node.url, proxy=proxy)
            case _:
                raise NotImplementedError

        updated: dict[str, object] = {"checked_at": utc_now()}

        if ok(res):
            status = NodeStatus.OK
            updated["height"] = res.ok
            updated["check_history"] = ([True, *node.check_history])[:100]
            updated["last_ok_at"] = utc_now()

        else:
            status = NodeStatus.from_error(cast(str, res.err))
            updated["height"] = None
            updated["check_history"] = ([False, *node.check_history])[:100]

        await self.db.check.insert_one(
            Check(
                id=ObjectId(),
                network=node.network,
                url=node.url,
                proxy=proxy,
                response={"ok": res.ok, "err": res.err, "data": res.data},
                status=status,
                elapsed=round(time.perf_counter() - start_time, 2),
            )
        )
        await self.db.node.set(id, updated | {"status": status})

        return res

    @async_synchronized
    async def check_next(self) -> None:
        logger.debug("check_next")
        limit = self.dconfig.limit_concurrent_checks
        nodes = await self.db.node.find({"checked_at": None}, limit=limit)
        if len(nodes) < limit:
            nodes += await self.db.node.find(
                {"checked_at": {"$lt": utc_delta(minutes=-5)}}, "checked_at", limit=limit - len(nodes)
            )

        async with anyio.create_task_group() as tg:
            for node in nodes:
                tg.start_soon(self.check, node.id, name=f"check_node_{node.id}")

    @async_synchronized
    async def get_live_nodes(self) -> dict[Network, list[Node]]:
        result: dict[Network, list[Node]] = {}
        for network in Network:
            result[network] = await self.db.node.find({"network": network, "last_ok_at": {"$gt": utc_delta(minutes=-5)}})
        return result

    async def get_networks_info(self) -> list[NetworkInfo]:
        live_nodes = await self.get_live_nodes()
        return [
            NetworkInfo(
                network=network,
                live_nodes=len(live_nodes.get(network, [])),
                all_nodes=await self.db.node.count({"network": network}),
            )
            for network in Network
        ]
