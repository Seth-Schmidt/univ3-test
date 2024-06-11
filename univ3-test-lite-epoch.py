import asyncio
import requests
from web3 import Web3
from web3._utils.events import get_event_data

from config import pool_addresses
from config import powerloom_endpoint
from config import powerloom_epoch_size
from config import weth_address
from config import lite_mode_block_length
from config import powerloom_end_epoch
from utils.constants import GRAPH_QUERY, GRAPH_URL
from utils.constants import STABLE_COINS
from utils.constants import UNISWAP_EVENTS_ABI
from utils.constants import UNISWAP_TRADE_EVENT_SIGS
from utils.constants import w3
from utils.helpers import batch
from utils.helpers import get_event_sig_and_abi
from utils.helpers import get_project_id
from utils.helpers import sqrtPriceX96ToTokenPrices


async def get_current_block():
    block = await w3.eth.get_block('latest')
    return block


async def build_eth_price_dict(block_number: int):
    start_block = block_number - (lite_mode_block_length - 1)
    end_block = block_number

    token_data = await get_token_decimals(
        pool_address=w3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640")
    )

    token0 = w3.to_checksum_address(token_data['token0'])
    token1 =  w3.to_checksum_address(token_data['token1'])
    weth = w3.to_checksum_address(weth_address)

    with open("static/UniswapV3Pool.json", "r") as f:
        abi = f.read()

    usdc_weth_contract = w3.eth.contract(
        address=w3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"),
        abi=abi,
    )

    eth_price_dict = {}

    # get average price for each block range using the price at the start and end of the block range
    for i in batch(range(start_block, end_block + 1), 10):
        start_data = await usdc_weth_contract.functions.slot0().call(block_identifier=i.start)
        end_data = await usdc_weth_contract.functions.slot0().call(block_identifier=i.stop - 1)

        start_prices = sqrtPriceX96ToTokenPrices(
            start_data[0],
            token_data['token0_decimals'],
            token_data['token1_decimals'],
        )

        end_prices = sqrtPriceX96ToTokenPrices(
            end_data[0],
            token_data['token0_decimals'],
            token_data['token1_decimals'],
        )

        if token0 == weth:
            start_price = start_prices[0]
            end_price = end_prices[0]
        elif token1 == weth:
            start_price = start_prices[1]
            end_price = end_prices[1]

        avg_price = (start_price + end_price) / 2

        # store average price for each block range
        eth_price_dict[(i.start, i.stop - 1)] = avg_price

    return eth_price_dict


async def get_token_decimals(pool_address: str):

    with open("static/UniswapV3Pool.json", "r") as f:
        abi = f.read()

    pool_contract = w3.eth.contract(
        address=Web3.to_checksum_address(pool_address),
        abi=abi,
    )

    token0 = await pool_contract.functions.token0().call()
    token1 = await pool_contract.functions.token1().call()

    with open("static/IERC20.json", "r") as f:
        abi = f.read()

    token0_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token0),
        abi=abi,
    )

    token1_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token1),
        abi=abi,
    )

    token0_decimals = await token0_contract.functions.decimals().call()
    token1_decimals = await token1_contract.functions.decimals().call()

    return {
        'token0_decimals': token0_decimals,
        'token1_decimals': token1_decimals,
        'token0': token0,
        'token1': token1,
    }


async def get_swap_event_total(pool_address: str, block_number: int, eth_price_dict: dict = {}):

    token_data = await get_token_decimals(
        pool_address=pool_address
    )

    weth = w3.to_checksum_address(weth_address)
    token0 = w3.to_checksum_address(token_data['token0'])
    token1 = w3.to_checksum_address(token_data['token1'])

    # set flags based on pool composition for later price calculations
    stable_weth_flag = False
    stable_flag = False

    if token0 in STABLE_COINS and token1 == weth:
        stable_weth_flag = True
    elif token1 in STABLE_COINS and token0 == weth:
        stable_weth_flag = True
    elif token0 in STABLE_COINS or token1 in STABLE_COINS:
        stable_flag = True
    
    # build block range for last 24 hours
    start_block = block_number - (lite_mode_block_length - 1)
    end_block = block_number

    event_signatures, event_abis = get_event_sig_and_abi(
        UNISWAP_TRADE_EVENT_SIGS,
        UNISWAP_EVENTS_ABI,
    )

    all_events = []

    # get and decode all swap events for each chunk of blocks
    for i in batch(range(start_block, end_block + 1), 10):
        
        # print(i.start, i.stop - 1)

        event_log_query = {
            'address': Web3.to_checksum_address(pool_address),
            'toBlock': i.stop - 1,
            'fromBlock': i.start,
            'topics': [event_signatures],
        }

        event_log = await w3.eth.get_logs(
            event_log_query,
        )

        codec = w3.codec
        for log in event_log:
            abi = event_abis.get(log.topics[0].hex(), '')
            evt = get_event_data(codec, abi, log)
            all_events.append((evt, (i.start, i.stop - 1)))

    total = 0
    swaps = []

    # iterate over all swap events and calculate total USD value of all swaps
    for evt_tuple in all_events:
        evt = evt_tuple[0]
        block_range = evt_tuple[1]
        if evt['event'] == 'Swap':
            swaps.append(evt)
            sqrtPriceX96 = evt['args']['sqrtPriceX96']

            price0, price1 = sqrtPriceX96ToTokenPrices(
                sqrtPriceX96,
                token_data['token0_decimals'],
                token_data['token1_decimals'],
            )

            if stable_weth_flag:
                if token1 == weth:
                    swap_amount = abs(evt['args']['amount1'] / 10 ** token_data['token1_decimals'])
                    swap_usd = price1 * swap_amount
                elif token0 == weth:
                    swap_amount = abs(evt['args']['amount0'] / 10 ** token_data['token0_decimals'])
                    swap_usd = price0 * swap_amount
            elif stable_flag:
                if token1 in STABLE_COINS:
                    swap_amount = abs(evt['args']['amount1'] / 10 ** token_data['token1_decimals'])
                    swap_usd = price1 * swap_amount
                elif token0 in STABLE_COINS:
                    swap_amount = abs(evt['args']['amount0'] / 10 ** token_data['token0_decimals'])
                    swap_usd = price0 * swap_amount
            else:
                if token1 == weth:
                    swap_amount = abs(evt['args']['amount1'] / 10 ** token_data['token1_decimals'])
                elif token0 == weth:
                    swap_amount = abs(evt['args']['amount0'] / 10 ** token_data['token0_decimals'])

                swap_usd = eth_price_dict[block_range] * swap_amount   

            total += swap_usd

    return total


async def get_powerloom_last_finalized_epoch_block(pool_address: str):

    address = pool_address.lower()

    project_id = get_project_id(address)

    resp = requests.get(f"{powerloom_endpoint}/last_finalized_epoch/{project_id}")
    resp = resp.json()
    epoch_end = resp['epochEnd']

    return epoch_end


async def get_powerloom_epoch_end_block(epoch_id: int):
    resp = requests.get(f"{powerloom_endpoint}/epoch/{epoch_id}")
    resp = resp.json()
    epoch_end = resp['epochEnd']

    return epoch_end


async def get_powerloom_data(pool_address: str, epoch_end: int):

    address = pool_address.lower()

    project_id = get_project_id(address)

    # get last finalized epoch and epoch end block
    # resp = requests.get(f"{powerloom_endpoint}/last_finalized_epoch/{project_id}")
    # resp = resp.json()
    # last_finalized_epoch = resp['epochId']
    # epoch_end = resp['epochEnd']

    epochs_in_range = lite_mode_block_length // powerloom_epoch_size
    start_epoch = (epoch_end - epochs_in_range) + 1

    current_block = epoch_end

    print(f"Getting powerloom data for pool: {address}")
    print(f"Last finalized epoch: {epoch_end}")

    print(f"Epochs in range: {epochs_in_range}")
    print(f"Start epoch: {start_epoch}")

    total = 0

    for i in reversed(range(start_epoch, epoch_end + 1)):
       
        data_url = f"{powerloom_endpoint}/data/{i}/{project_id}/"
        resp = requests.get(data_url)
        resp = resp.json()

        total += resp['totalTrade']
        current_block -= powerloom_epoch_size

    return total, epoch_end


async def graph_request(pool_address: str, from_block: str, to_block: str):

    # build variables for GraphQL query
    variables = {
        "pool": pool_address.lower(),
        "blockNumber_gte": str(from_block),
        "blockNumber_lte": str(to_block)
    }

    response = requests.post(
        GRAPH_URL,
        headers={"Content-Type": "application/json"}, 
        json={'query': GRAPH_QUERY, 'variables': variables}
    )

    if response.status_code == 200:
        data = response.json()
        swaps = data['data']['swaps']

        total = 0

        # calculate total USD value of all swaps for given block range
        for swap in swaps:
            total += float(swap['amountUSD'])

        return {
            'total': total,
            'length': len(swaps),
            'from_block': from_block,
            'to_block': to_block,
        }


async def get_graph_data(pool_address: str, block_number: int):
    start_block = block_number - (lite_mode_block_length - 1)
    end_block = block_number

    graph_tasks = []

    # make initial request to get total swaps for each block range
    for i in batch(range(start_block, end_block + 1), 10):
        to_block = i.stop - 1
        graph_tasks.append(asyncio.create_task(
            graph_request(
                pool_address=pool_address, 
                from_block=i.start, 
                to_block=to_block
            )
        )
        )

    results = await asyncio.gather(*graph_tasks)
    
    total = 0
    
    # check if any batch length is 1000 (the max return allowed), if so retry with smaller batch sizes
    for result in results:
        if result['length'] == 1000:
            print("Warning: Batch length is 1000, possible missed swaps - retrying")
            print(f"Retrying: {result}")
            retry_tasks = []

            # retry with smaller batch sizes once for each initial batch
            for i in batch(range(result['from_block'], result['to_block']), (10 / 2)):
                to_block = i.stop - 1
                retry_tasks.append(asyncio.create_task(
                    graph_request(
                        pool_address=pool_address, 
                        from_block=i.start, 
                        to_block=to_block
                    )
                )
                )

            retry_results = await asyncio.gather(*retry_tasks)

            for retry_result in retry_results:
                # check if any retry batch length is 1000, if so print warning
                if retry_result['length'] == 1000:
                    print("Warning: Batch length is 1000, possible missed swaps - not retrying again")
                    print(f"Not retrying: {retry_result}")
                total += retry_result['total']

        # add total USD value of swaps for each batch
        else:
            total += result['total']

    return total


async def get_all_totals_for_pool(pool_address: str, block_number: int, end_epoch: int, eth_price_dict: dict = {}):
    powerloom_total, epoch_end_block = await get_powerloom_data(pool_address, epoch_end=end_epoch)
    print(f"Finished gather Powerloom data for pool: {pool_address}")
    print("- - - - -")
    swap_event_total = await get_swap_event_total(pool_address, block_number, eth_price_dict)
    print(f"Finished gather Swap Event data for pool: {pool_address}")
    print("- - - - -")
    graph_total = await get_graph_data(pool_address, block_number)
    print(f"Finished gather Graph data for pool: {pool_address}")
    print("- - - - -")

    return powerloom_total, swap_event_total, graph_total


# get total volume for the given config pools for the last 24 hours using Powerloom, direct RPC Swap Events, and The Graph
async def main():

    epoch_end_block = await get_powerloom_epoch_end_block(powerloom_end_epoch)

    print("Using end epoch:", powerloom_end_epoch)
    print("Using epoch end block:", epoch_end_block)

    print(f"Getting data for pools: {pool_addresses}")
    print("This may take a minute or two...")

    address = w3.to_checksum_address(pool_addresses[0])

    # build an average ETH price dictionary for the last 24 hours up to the epoch end block
    # this is only used to calculate USD value of swaps for pools without stablecoins
    eth_price_dict = await build_eth_price_dict(epoch_end_block)

    total_tasks = []
    for address in pool_addresses:
        total_tasks.append(
            asyncio.create_task(
                get_all_totals_for_pool(
                    pool_address=address,
                    block_number=epoch_end_block,
                    end_epoch=powerloom_end_epoch,
                    eth_price_dict=eth_price_dict
                )
            )
        )

    results = await asyncio.gather(*total_tasks)

    for i, result in enumerate(results):
        print(f"Pool: {pool_addresses[i]}")
        print(f"Powerloom:  {result[0]}")
        print(f"Swap Event: {result[1]}")
        print(f"GraphQL:    {result[2]}")
        print("- - -")

    
if __name__ == "__main__":
    asyncio.run(main())






