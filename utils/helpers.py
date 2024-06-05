from eth_utils import keccak


def sqrtPriceX96ToTokenPrices(sqrtPriceX96, token0_decimals, token1_decimals):
    # https://blog.uniswap.org/uniswap-v3-math-primer

    price0 = ((sqrtPriceX96 / (2**96))** 2) / (10 ** token1_decimals / 10 ** token0_decimals)
    price1 = 1 / price0

    price0 = round(price0, token0_decimals)
    price1 = round(price1, token1_decimals)

    return price0, price1


def batch(iterable, n=1):
    """
    Batch an iterable into chunks of size n.

    Args:
        iterable (iterable): The iterable to be batched.
        n (int): The size of each batch.

    Yields:
        list: A batch of size n.
    """
    iterable_len = len(iterable)
    for idx in range(0, iterable_len, n):
        yield iterable[idx:min(idx + n, iterable_len)]


def get_event_sig_and_abi(event_signatures, event_abis):
    """
    Given a dictionary of event signatures and a dictionary of event ABIs,
    returns a tuple containing a list of event signatures and a dictionary of
    event ABIs keyed by their corresponding signature hash.
    """
    event_sig = [
        '0x' + keccak(text=sig).hex() for name, sig in event_signatures.items()
    ]
    event_abi = {
        '0x' +
        keccak(text=sig).hex(): event_abis.get(
            name,
            'incorrect event name',
        )
        for name, sig in event_signatures.items()
    }
    return event_sig, event_abi