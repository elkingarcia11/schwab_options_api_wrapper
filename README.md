# Schwab Options API Client

A Python client for interacting with the Charles Schwab Options API to fetch option chains, expiration dates, and option symbols for multiple underlying symbols.

## Features

- **Get symbol prices** - Fetch real-time or last trading price for any stock symbol or option symbol
- **Batch quote retrieval** - Get comprehensive quote and reference data for multiple symbols (stocks or options) in a single API call, including Greeks, volume, and contract details
- **Expiration chain retrieval** - Get all available expiration dates for a symbol
- **Option chain data** - Fetch complete option chain data including calls and puts
- **Smart strike selection** - Automatically selects strikes based on underlying price using round down/up strategy
- **Batch processing** - Process multiple symbols with different days-to-expiration requirements in a single call
- **Configurable contract types** - Support for CALL, PUT, or ALL contract types

## Prerequisites

- Python 3.7+
- Charles Schwab API access token
- Valid access token stored in `schwab_access_token.txt`

## Installation

1. **Clone or download this repository**

2. **Set up a virtual environment** (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Set up your access token**:
   - Create a file named `schwab_access_token.txt` in the project root
   - Add your Schwab API access token as a single line in the file

## Usage

### Basic Example

```python
from schwab_options_api_client import SchwabOptionsApiClient

# Initialize the client
client = SchwabOptionsApiClient('schwab_access_token.txt')

# Get option symbols for multiple symbols
# Note: Symbols are paired with DTE values by index
# SYMBOL[0] uses DAYS_TO_EXPIRATION[0], SYMBOL[1] uses DAYS_TO_EXPIRATION[1], etc.
symbols = ['SPY', 'QQQ']
days_to_expiration = [2, 3]  # SPY uses 2 DTE, QQQ uses 3 DTE
result = client.get_option_symbols_for_multiple_symbols(
    symbols,
    days_to_expiration,
    contract_type="ALL",
    strikes_below=10,
    strikes_above=10
)

# Access the results
for key, option_data in result.items():
    symbol, expiration_date = key.split('_')
    print(f"\n{symbol} - {expiration_date}")
    print(f"Calls ({len(option_data['calls'])}): {option_data['calls']}")
    print(f"Puts ({len(option_data['puts'])}): {option_data['puts']}")
    print(f"Strikes: {option_data['strikes']}")
```

### Individual Methods

#### Get Symbol Price (Stock or Option)

```python
# Get price for a stock symbol
price = client.get_symbol_price('AAPL')
print(f"AAPL price: ${price:.2f}")

# Get price for an option symbol
option_price = client.get_symbol_price('SPY   251106C00674000')
print(f"Option price: ${option_price:.2f}")
```

#### Get Quotes for Multiple Symbols

```python
# Get comprehensive quote and reference data for multiple symbols
symbols = ['SPY   251106C00674000', 'SPY   251106P00674000', 'SPY']
quotes = client.get_symbols_quote(symbols)

for symbol, data in quotes.items():
    print(f"\n{symbol}:")
    print(f"  Last Price: ${data['quote']['lastPrice']:.2f}")
    print(f"  Bid: ${data['quote']['bidPrice']:.2f}, Ask: ${data['quote']['askPrice']:.2f}")
    print(f"  Mark: ${data['quote']['mark']:.2f}")

    # For options, show Greeks and reference info
    if data['assetMainType'] == 'OPTION':
        print(f"  Delta: {data['quote']['delta']:.4f}")
        print(f"  Gamma: {data['quote']['gamma']:.4f}")
        print(f"  Theta: {data['quote']['theta']:.4f}")
        print(f"  Vega: {data['quote']['vega']:.4f}")
        print(f"  Strike: ${data['reference']['strikePrice']:.2f}")
        print(f"  DTE: {data['reference']['daysToExpiration']}")
        print(f"  Underlying: {data['reference']['underlying']}")
```

#### Get Expiration Chain

```python
expiration_chain = client.get_expiration_chain('SPY')
for expiration in expiration_chain:
    print(f"Expiration: {expiration['expirationDate']}, DTE: {expiration['daysToExpiration']}")
```

#### Find Next Expiration Date

```python
# Get expiration chain first
expiration_chain = client.get_expiration_chain('SPY')

# Find first expiration with at least 5 days to expiration
expiration_date = client.find_next_expiration_date_greater_than_or_equal_to(expiration_chain, 5)
print(f"Next expiration: {expiration_date}")
```

#### Get Option Chains for Specific Expiration

```python
option_chains = client.get_all_option_chains('AAPL', '2025-01-15', contract_type='ALL')
```

#### Get Option Symbols for Single Symbol

```python
# Get option symbols with 10 strikes below and 10 strikes above
# Both calls and puts will get the same 20 strikes (10 below + 10 above)
option_symbols = client.get_option_symbols(
    symbol='SPY',
    expiration_date='2025-01-15',
    contract_type='ALL',
    strikes_below=10,
    strikes_above=10
)

print(f"Calls ({len(option_symbols['calls'])}): {option_symbols['calls']}")
print(f"Puts ({len(option_symbols['puts'])}): {option_symbols['puts']}")
print(f"Call strikes: {option_symbols['strikes']['calls']}")
print(f"Put strikes: {option_symbols['strikes']['puts']}")

# Example output for price 653.43:
# Call strikes: [644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663]
# Put strikes: [644, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663]
```

## API Methods

### `get_symbol_price(symbol: str) -> float`

Get the last trading price for a stock symbol or option symbol.

**Parameters:**

- `symbol` (str): Stock ticker symbol (e.g., 'AAPL', 'SPY', 'QQQ') or option symbol (e.g., 'SPY 251106C00674000', 'SPY 251106P00674000').
  Case-insensitive, but typically uppercase.

**Returns:**

- `float`: The symbol's last trading price in dollars. Returns 0.0 if an error occurs or price data is unavailable.

**Example:**

```python
# Get stock price
stock_price = client.get_symbol_price('AAPL')

# Get option price
option_price = client.get_symbol_price('SPY   251106C00674000')
```

### `get_symbols_quote(symbols: List[str]) -> Dict`

Get comprehensive quote and reference data for multiple symbols (stocks or options) in a single API call.

**Parameters:**

- `symbols` (List[str]): List of stock ticker symbols or option symbols.
  Example: `['SPY', 'AAPL']` or
  `['SPY   251106C00674000', 'SPY   251106P00674000']`
  or a mix of both.

**Returns:**

- `Dict`: A dictionary where keys are symbol strings and values contain:
  - `assetMainType` (str): Type of asset (e.g., 'OPTION', 'EQUITY')
  - `realtime` (bool): Whether data is real-time
  - `symbol` (str): The symbol
  - `quote` (Dict): Quote data including:
    - Pricing: `bidPrice`, `askPrice`, `lastPrice`, `mark`, `closePrice`
    - Trading: `volume`, `openInterest`, `totalVolume`
    - Greeks (for options): `delta`, `gamma`, `theta`, `vega`, `rho`
    - Options data: `volatility`, `theoreticalOptionValue`, `timeValue`, `moneyIntrinsicValue`
    - And many other fields
  - `reference` (Dict): Reference data including:
    - For options: `contractType`, `strikePrice`, `daysToExpiration`, `underlying`,
      `expirationType`, `exerciseType`, `multiplier`, etc.
    - For stocks: Company information, etc.
      Returns an empty dictionary `{}` if an error occurs.

**Example:**

```python
symbols = ['SPY   251106C00674000', 'SPY   251106P00674000']
quotes = client.get_symbols_quote(symbols)

for symbol, data in quotes.items():
    print(f"{symbol}: ${data['quote']['lastPrice']:.2f}")
    if data['assetMainType'] == 'OPTION':
        print(f"  Delta: {data['quote']['delta']:.4f}")
        print(f"  Strike: ${data['reference']['strikePrice']:.2f}")
```

### `get_expiration_chain(symbol: str) -> List[Dict]`

Fetch all available expiration dates for a symbol.

**Parameters:**

- `symbol` (str): Stock symbol

**Returns:**

- `List[Dict]`: List of expiration date dictionaries with details

### `find_next_expiration_date_greater_than_or_equal_to(expiration_chain: List[Dict], days_to_expiration: int) -> Optional[str]`

Find the first expiration date that meets or exceeds the specified days to expiration.

**Parameters:**

- `expiration_chain` (List[Dict]): Expiration chain list returned by `get_expiration_chain()`
- `days_to_expiration` (int): Minimum number of days to expiration

**Returns:**

- `Optional[str]`: Expiration date in YYYY-MM-DD format, or the last expiration date in the chain if no suitable date exists

### `get_all_option_chains(symbol: str, expiration_date: str, contract_type: str = "ALL") -> Dict`

Fetch complete option chain data for a symbol and expiration date.

**Parameters:**

- `symbol` (str): Stock symbol
- `expiration_date` (str): Expiration date in YYYY-MM-DD format
- `contract_type` (str): 'CALL', 'PUT', or 'ALL' (default: 'ALL')

**Returns:**

- `Dict`: Complete option chain data from Schwab API

### `get_option_symbols(symbol: str, expiration_date: str, contract_type: str = "ALL", strikes_below: int = 2, strikes_above: int = 2) -> Dict[str, List[str]]`

Get option symbols using smart strike selection based on underlying price.

**Important:** Both calls and puts get the same set of strikes (strikes below + strikes above).

**Parameters:**

- `symbol` (str): Stock symbol
- `expiration_date` (str): Expiration date in YYYY-MM-DD format
- `contract_type` (str): 'CALL', 'PUT', or 'ALL' (default: 'ALL')
- `strikes_below` (int): Total number of strikes below current price. Rounds down to get first strike, then gets (strikes_below - 1) more below. Default: 2
- `strikes_above` (int): Total number of strikes above current price. Rounds up to get first strike, then gets (strikes_above - 1) more above. Default: 2

**Returns:**

- `Dict[str, List[str]]`: Dictionary with:
  - `'calls'`: List of call option symbols (same strikes as puts)
  - `'puts'`: List of put option symbols (same strikes as calls)
  - `'strikes'`: Dictionary with `'calls'` and `'puts'` strike price lists (both contain the same strikes)

**Example:** For price 653.43 with `strikes_below=10, strikes_above=10`:

- Strikes below: [653, 652, 651, 650, 649, 648, 647, 646, 645, 644]
- Strikes above: [654, 655, 656, 657, 658, 659, 660, 661, 662, 663]
- Total: 20 strikes for both calls and puts

### `get_option_symbols_for_multiple_symbols(symbols: List[str], days_to_expiration: List[int], contract_type: str, strikes_below: int, strikes_above: int) -> Dict[str, Dict[str, List[str]]]`

Get option symbols for multiple symbols, pairing each symbol with its corresponding DTE value by index.

**Important:** Symbols and days_to_expiration are paired by index (one-to-one mapping):

- `SYMBOL[0]` uses `DAYS_TO_EXPIRATION[0]`
- `SYMBOL[1]` uses `DAYS_TO_EXPIRATION[1]`
- etc.

Both lists must have the same length.

**Parameters:**

- `symbols` (List[str]): List of stock symbols (e.g., ['SPY', 'QQQ'])
- `days_to_expiration` (List[int]): List of minimum days to expiration. Must have same length as symbols.
- `contract_type` (str): 'CALL', 'PUT', or 'ALL'
- `strikes_below` (int): Number of strikes below current price
- `strikes_above` (int): Number of strikes above current price

**Returns:**

- `Dict[str, Dict[str, List[str]]]`: Dictionary with composite keys `{symbol}_{expiration_date}` containing option symbol data

**Example:**

```python
symbols = ['SPY', 'QQQ']
dte = [2, 3]  # SPY uses 2 DTE, QQQ uses 3 DTE
result = client.get_option_symbols_for_multiple_symbols(symbols, dte, 'ALL', 10, 10)
# Result: {'SPY_2025-11-06': {...}, 'QQQ_2025-11-07': {...}}
```

## Strike Selection Strategy

The client uses a smart strike selection strategy based on the underlying price. **Both calls and puts get the same set of strikes** (strikes below + strikes above).

### Strikes Below Current Price

- Rounds down to get the first strike (floor of current price)
- Then selects `(strikes_below - 1)` additional strikes below
- Example: Price 653.43, `strikes_below=10` → `[653, 652, 651, 650, 649, 648, 647, 646, 645, 644]` (10 strikes)

### Strikes Above Current Price

- Rounds up to get the first strike (ceiling of current price)
- Then selects `(strikes_above - 1)` additional strikes above
- Example: Price 653.43, `strikes_above=10` → `[654, 655, 656, 657, 658, 659, 660, 661, 662, 663]` (10 strikes)

### Total Strikes

- **Total strikes for both calls and puts**: `strikes_below + strikes_above`
- Example: `strikes_below=10, strikes_above=10` → 20 strikes total (10 below + 10 above)
- Both calls and puts receive the same 20 strikes, sorted in ascending order

This strategy targets options with higher liquidity typically found at or near the current market price, while providing comprehensive coverage both above and below the current price.

## Error Handling

All methods include error handling and will:

- Print error messages to console
- Return safe default values (empty lists, empty dicts, or 0) instead of raising exceptions
- Continue processing even if individual API calls fail

## Requirements

- `httpx` - HTTP client library for making API requests

## Notes

- The client assumes a valid access token is stored in `schwab_access_token.txt`
- API rate limits may apply based on your Schwab API subscription
- Market data availability depends on market hours and trading sessions
- Option chains may not be available for all symbols or expiration dates

## License

This project is provided as-is for educational and personal use.
