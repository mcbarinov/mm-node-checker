from __future__ import annotations

import enum
from datetime import datetime

from bson import ObjectId
from mm_base6 import BaseDb
from mm_crypto_utils import Network
from mm_mongo import AsyncMongoCollection, MongoModel
from mm_std import utc_now
from pydantic import Field
from pymongo import IndexModel


@enum.unique
class NodeStatus(str, enum.Enum):
    NOT_CHECKED = "not_checked"
    OK = "ok"
    TIMEOUT = "timeout"
    PROXY = "proxy"
    UNKNOWN_RESPONSE = "unknown_response"
    ERROR = "error"

    @classmethod
    def from_error(cls, error: str) -> NodeStatus:
        if error == "timeout":
            return cls.TIMEOUT
        if error == "proxy":
            return cls.PROXY
        if error == "unknown_response":
            return cls.UNKNOWN_RESPONSE
        return cls.ERROR


class Node(MongoModel[ObjectId]):
    network: Network
    url: str
    status: NodeStatus = NodeStatus.NOT_CHECKED
    height: int | None = None  # latest block number or slot
    check_history: list[bool] = Field(default_factory=list)  # keep last 100 check results; ok=true, down=false
    checked_at: datetime | None = None  # last check
    last_ok_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def history_ok_count(self) -> int:
        return len([x for x in self.check_history if x is True])

    @property
    def history_down_count(self) -> int:
        return len([x for x in self.check_history if x is False])

    __collection__: str = "node"
    __indexes__ = "network, !url, last_ok_at"


class Check(MongoModel[ObjectId]):
    network: Network
    url: str
    proxy: str | None
    status: NodeStatus
    elapsed: float  # response time in seconds
    response: dict[str, object]
    created_at: datetime = Field(default_factory=utc_now)

    __collection__: str = "check"
    __indexes__ = ["network", IndexModel([("created_at", -1)], expireAfterSeconds=3 * 60 * 60)]


class Db(BaseDb):
    node: AsyncMongoCollection[ObjectId, Node]
    check: AsyncMongoCollection[ObjectId, Check]
