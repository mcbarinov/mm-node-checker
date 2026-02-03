# mm-node-checker

Blockchain node health monitoring service. Checks the availability of RPC nodes across multiple networks (EVM, Solana, Aptos, Starknet) by verifying they respond and return valid block heights within the last 5 minutes.

## API

### GET /live

Returns live node URLs grouped by network.

Response:
```json
{
  "ethereum": ["https://node1.example.com", "https://node2.example.com"],
  "polygon": ["https://polygon-node.example.com"]
}
```
