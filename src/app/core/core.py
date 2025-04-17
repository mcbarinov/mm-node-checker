from typing import Self

from mm_base6 import BaseCore, CoreConfig

from app.core.db import Db
from app.core.services.node_service import NodeService
from app.settings import DynamicConfigs, DynamicValues


class Core(BaseCore[DynamicConfigs, DynamicValues, Db]):
    node_service: NodeService

    @classmethod
    async def init(cls, core_config: CoreConfig) -> Self:
        res = await super().base_init(core_config, DynamicConfigs, DynamicValues, Db)
        res.node_service = NodeService(res.base_service_params)

        return res

    async def configure_scheduler(self) -> None:
        self.scheduler.add_task("check", 3, self.node_service.check_next)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass
