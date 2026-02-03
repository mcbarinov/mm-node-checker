"""RPC functions to fetch block height from different blockchain networks."""

import logging

import pydash
from mm_http import http_request
from mm_result import Result

logger = logging.getLogger(__name__)


async def get_evm_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    """Fetch current block height from an EVM-compatible node."""
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_err():
        return res.to_result_err()
    try:
        return res.to_result_ok(int(res.json_body("result").unwrap(), 16))
    except Exception as e:
        return res.to_result_err(e)


async def get_starknet_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    """Fetch current block height from a Starknet node."""
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "starknet_blockNumber", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_err():
        return res.to_result_err()
    try:
        return res.to_result_ok(res.json_body("result").unwrap())
    except Exception as e:
        return res.to_result_err(e)


async def get_solana_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    """Fetch current block height from a Solana node."""
    res = await http_request(
        url=url,
        method="post",
        json={"jsonrpc": "2.0", "method": "getBlockHeight", "params": [], "id": "1"},
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_err():
        return res.to_result_err()
    json_body = res.json_body_or_none()
    err = pydash.get(json_body, "error.message")
    if err:
        return res.to_result_err(f"service_error: {err}")
    try:
        return res.to_result_ok(int(json_body["result"]))
    except Exception as e:
        return res.to_result_err(e)


async def get_aptos_height(url: str, proxy: str | None = None, timeout: float = 5) -> Result[int]:
    """Fetch current block height from an Aptos node."""
    res = await http_request(
        url=url,
        proxy=proxy,
        timeout=timeout,
    )
    if res.is_err():
        return res.to_result_err()
    try:
        return res.to_result_ok(int(res.json_body("block_height").unwrap()))
    except Exception as e:
        return res.to_result_err(e)
