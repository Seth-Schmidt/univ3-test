## Overview:
This script is used to compare the Powerloom Snapshotter's, RPC Events, and UniswapV3's GraphQL subgraph 24 hour trading volume data for UniswapV3 pools.

It currently only supports UniswapV3 pools that contain ETH or a stablecoin as one of the tokens.

Example Output:

    Pool: 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
    Powerloom:  203235887.94566
    Swap Event: 203102070.84977224
    GraphQL:    203041947.21340522
    - - -
    Pool: 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD
    Powerloom:  13846305.16321
    Swap Event: 13824836.277449252
    GraphQL:    13798335.715012763
    - - -
    Pool: 0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168
    Powerloom:  4672081.04091
    Swap Event: 4665779.417507376
    GraphQL:    4665826.62804508
    - - -
    Pool: 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36
    Powerloom:  11537232.82287
    Swap Event: 11523415.101480817
    GraphQL:    11527063.060057288
    - - -
    Pool: 0x7A415B19932c0105c82FDB6b720bb01B0CC2CAe3
    Powerloom:  53161834.93248
    Swap Event: 53059881.946644194
    GraphQL:    53106019.04963298


## Setup:
- run `poetry install`
- copy `config.example.py` to `config.py`
- add a RPC endpoint to the `rpc_url` variable in `config.py`
- all settings that may be changed are located in `config.py`
    - `pool_addresses`: a list of UniswapV3 pool addresses that you would like to compare with Powerloom data.
    - `weth_address`: chain wrapped ether token address
    - `rpc_url`: chain rpc url
    - `powerloom_endpoint`: url of core-api endpoint for Powerloom node
    - `top_pools_id`: Powerloom project ID for UniswapV3 aggregate snapshot containing theh 24hr volume data for all pools
    - `get_logs_block_length`: the size of the block length to be used for the RPC `get_logs()` queries
- settings that may be changed for lite mode in `config.py`
    - `powerloom_epoch_size`: length of epochs for powerloom
    - `lite_mode_block_length`: length of total blocks to fetch data for in lite mode, must be a multiple of powerloom_epoch_size

## Run:
- `poetry run python3 univ3-test.py`

## Run (Lite Mode)
- `poetry run python3 univ3-test-lite.py`
 


