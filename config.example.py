pool_addresses = [
    "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640", 
    "0xCBCdF9626bC03E24f779434178A73a0B4bad62eD", 
    "0x5777d92f208679DB4b9778590Fa3CAB3aC9e2168",
    "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36",
    "0x7A415B19932c0105c82FDB6b720bb01B0CC2CAe3"
]
weth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
rpc_url = ""
powerloom_endpoint = "https://uniswapv3.powerloom.io/api"

# project ID for top pairs data
top_pools_id = "aggregate_24h_top_pairs_lite:8c7dcfa29f8717cac966f4690f0cdf4e8e5c2bf04ebede61b1ed521383c1e9c4:UNISWAPV3"

# length of blocks to fetch for each get_logs call
get_logs_block_length = 500

# length of epochs for powerloom
powerloom_epoch_size = 10

# length of total blocks to fetch data for in lite mode, must be a multiple of powerloom_epoch_size
lite_mode_block_length = 30

# namespace for powerloom
namespace = "UNISWAPV3"

# project ID for volume data
volume_project_id = "pairContract_trade_volume"
