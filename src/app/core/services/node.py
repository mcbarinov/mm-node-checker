import logging
import time
from typing import Any

import anyio
import pydash
import tomlkit
from bson import ObjectId
from mm_base6.core.utils import toml_dumps, toml_loads
from mm_concurrency import async_synchronized
from mm_cryptocurrency import Network, NetworkType, random_proxy
from mm_result import Result
from mm_std import utc_delta, utc_now
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

    async def export_as_toml(self) -> str:
        nodes = []
        for network in Network:
            urls = await self.db.node.collection.distinct("url", {"network": network})
            if urls:
                nodes.append(
                    {
                        "network": network.value,
                        "urls": tomlkit.string("\n".join(urls), multiline=True),
                    }
                )

        return toml_dumps({"nodes": nodes})

    async def import_from_toml(self, toml: str) -> int:
        result = 0
        data: Any = toml_loads(toml)
        for node in data["nodes"]:
            network = Network(node["network"])
            urls = node["urls"].strip().splitlines()
            urls = [url.strip().removesuffix("/") for url in urls if url.strip()]
            urls = pydash.uniq(urls)
            for url in urls:
                if await self.db.node.exists({"url": url}):
                    continue
                await self.db.node.insert_one(Node(id=ObjectId(), network=network, url=url))
                result += 1

        return result

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

        proxy = random_proxy(self.dynamic_values.proxies)

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

        if res.is_ok():
            status = NodeStatus.OK
            updated["height"] = res.unwrap()
            updated["check_history"] = ([True, *node.check_history])[:100]
            updated["last_ok_at"] = utc_now()

        else:
            status = NodeStatus.from_error(res.unwrap_err())
            updated["height"] = None
            updated["check_history"] = ([False, *node.check_history])[:100]

        await self.db.check.insert_one(
            Check(
                id=ObjectId(),
                network=node.network,
                url=node.url,
                proxy=proxy,
                response=res.to_dict(safe_exception=True),
                status=status,
                elapsed=round(time.perf_counter() - start_time, 2),
            )
        )
        await self.db.node.set(id, updated | {"status": status})

        return res

    @async_synchronized
    async def check_next(self) -> None:
        if not self.dynamic_configs.auto_check:
            return
        logger.debug("check_next")
        limit = self.dynamic_configs.limit_concurrent_checks
        nodes = await self.db.node.find({"checked_at": None}, limit=limit)
        if len(nodes) < limit:
            nodes += await self.db.node.find(
                {"checked_at": {"$lt": utc_delta(minutes=-1)}}, "checked_at", limit=limit - len(nodes)
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
