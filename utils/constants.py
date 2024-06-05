from web3 import Web3
from web3.eth import AsyncEth
from config import pool_addresses
from config import rpc_url

CHAIN_ID = 1
BLOCK_TIME = 12
EPOCH_SIZE = 10
DAY = 86400
BLOCKS_PER_DAY = int(DAY / BLOCK_TIME)

w3 = Web3(
    Web3.AsyncHTTPProvider(rpc_url),
    modules={'eth': (AsyncEth,)},
)

with open("static/UniswapV3Pool.json", "r") as f:
    abi = f.read()

pool_contract = w3.eth.contract(
    address=Web3.to_checksum_address(pool_addresses[0]), 
    abi=abi
)

STABLE_COINS = (
    w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    w3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
    w3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F")
)

# FUNCTION SIGNATURES and OTHER CONSTANTS
UNISWAP_TRADE_EVENT_SIGS = {
    'Swap': 'Swap(address,address,int256,int256,uint160,uint128,int24)',
    'Mint': 'Mint(address,address,int24,int24,uint128,uint256,uint256)',
    'Burn': 'Burn(address,int24,int24,uint128,uint256,uint256)',
}

UNISWAP_EVENTS_ABI = {
    'Swap': pool_contract.events.Swap._get_event_abi(),
    'Mint': pool_contract.events.Mint._get_event_abi(),
    'Burn': pool_contract.events.Burn._get_event_abi(),
}

GRAPH_URL = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

GRAPH_QUERY = """
    query MyQuery($pool: String!, $blockNumber_lte: String!, $blockNumber_gte: String!) {
        swaps(
            first: 1000
            subgraphError: allow
            orderBy: timestamp
            orderDirection: desc
            where: {pool: $pool, transaction_: {blockNumber_lte: $blockNumber_lte, blockNumber_gte: $blockNumber_gte}}
        ) {
            amount0
            amount1
            amountUSD
            id
            timestamp
            transaction {
                blockNumber
            }
        }
    }
    """