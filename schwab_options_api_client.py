import httpx
from typing import Optional, Dict, List

class SchwabOptionsApiClient:
    def __init__(self, access_token_file_path: str):
        """
        Initialize the Schwab Options API client with an access token.
        
        Reads the access token from a file and sets up the authorization headers
        needed for all API requests. The token should be a valid Schwab API access token.
        
        Args:
            access_token_file_path (str): Path to a text file containing the Schwab API access token.
                                        The file should contain only the access token as a single line.
        
        Raises:
            FileNotFoundError: If the access token file cannot be found.
            IOError: If there is an error reading the access token file.
        
        Example:
            >>> client = SchwabOptionsApiClient('schwab_access_token.txt')
        """
        with open(access_token_file_path, 'r') as file:
            self.access_token = file.read()
            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }

    def get_symbol_price(self, symbol: str) -> float:
        """
        Retrieve the last trading price for a stock symbol.
        
        Fetches real-time or last available quote data from Schwab's market data API.
        This price is used for strike selection calculations in option chain analysis.
        The price reflects the most recent trade during regular trading hours.

        Args:
            symbol (str): The stock ticker symbol (e.g., 'AAPL', 'SPY', 'QQQ') or option symbol (e.g., 'SPY   251106C00674000', 'SPY   251106P00674000').
                         Case-insensitive, but typically uppercase.

        Returns:
            float: The symbol's last trading price in dollars.
                   Returns 0.0 if an error occurs or price data is unavailable.
                   
        Example:
            >>> price = client.get_symbol_price('AAPL')
            >>> print(f"AAPL is trading at ${price:.2f}")
            AAPL is trading at $270.57
        """

        try:
            url = f"https://api.schwabapi.com/marketdata/v1/quotes?symbols={symbol}"
            
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers)
                
            if response.status_code != 200:
                raise Exception(f"Quote request failed: {response.status_code} - {response.text}")
            
            quote_data = response.json()
            
            if symbol not in quote_data:
                raise Exception(f"No quote data found for {symbol}")
            
            quote = quote_data[symbol]
            
            if 'quote' in quote and 'lastPrice' in quote['quote']:
                print(f"🎯 Underlying price for {symbol}: ${quote['quote']['lastPrice']:.2f}")
                return quote['quote']['lastPrice']
            
        except Exception as e:
            print(f"❌ Error getting underlying price for {symbol}: {e}")
            return 0 

    def get_symbols_quote(self, symbols: List[str]) -> Dict:
        """
        Retrieve quote and reference data for multiple symbols (stocks or options).
        
        Fetches comprehensive quote data including bid/ask prices, Greeks (for options),
        volume, open interest, and reference information such as expiration dates,
        strike prices, and contract details.
        
        Args:
            symbols (List[str]): List of stock ticker symbols or option symbols.
                               Example: ['SPY', 'AAPL'] or 
                               ['SPY   251106C00674000', 'SPY   251106P00674000']
                               or a mix of both.
        
        Returns:
            Dict: A dictionary where keys are symbol strings and values contain:
                - 'assetMainType' (str): Type of asset (e.g., 'OPTION', 'EQUITY')
                - 'realtime' (bool): Whether data is real-time
                - 'ssid' (int): Symbol security ID
                - 'symbol' (str): The symbol
                - 'quote' (Dict): Quote data including:
                    - bidPrice, askPrice, lastPrice, mark
                    - volume, openInterest
                    - Greeks: delta, gamma, theta, vega, rho (for options)
                    - volatility, theoreticalOptionValue (for options)
                    - And many other fields
                - 'reference' (Dict): Reference data including:
                    - For options: contractType, strikePrice, expirationDate info,
                      daysToExpiration, underlying, etc.
                    - For stocks: company info, etc.
            Returns an empty dictionary {} if an error occurs.
            
        Example:
            >>> symbols = ['SPY   251106C00674000', 'SPY   251106P00674000']
            >>> quotes = client.get_symbols_quote(symbols)
            >>> for symbol, data in quotes.items():
            ...     print(f"{symbol}: ${data['quote']['lastPrice']:.2f}")
            SPY   251106C00674000: $4.51
            SPY   251106P00674000: $2.69
        """
        try:
            # Join symbols with commas for the API
            symbols_str = ','.join(symbols)
            
            url = "https://api.schwabapi.com/marketdata/v1/quotes"
            params = {
                'symbols': symbols_str,
                'fields': 'quote,reference',
                'indicative': 'false'
            }
            
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                
            if response.status_code != 200:
                raise Exception(f"Quote request failed: {response.status_code} - {response.text}")
            
            quote_data = response.json()
            print(f"🎯 Retrieved quotes for {len(quote_data)} symbol(s)")
            return quote_data
            
        except Exception as e:
            print(f"❌ Error getting quotes for symbols: {e}")
            return {}

    def get_expiration_chain(self, symbol: str) -> List[Dict]:
        """
        Retrieve all available option expiration dates for a given symbol.
        
        Fetches the complete expiration chain from Schwab's API, which includes
        all expiration dates with their corresponding days-to-expiration, expiration
        types (weekly, monthly), and whether they are standard expirations.
        This is essential for finding suitable expiration dates for option trading.

        Args:
            symbol (str): The stock ticker symbol (e.g., 'AAPL', 'SPY', 'QQQ').
            
        Returns:
            List[Dict]: A list of dictionaries, each containing expiration details:
                - expirationDate (str): Date in YYYY-MM-DD format
                - daysToExpiration (int): Number of days until expiration
                - expirationType (str): Type of expiration (e.g., 'M' for End Of Month Expiration Calendar Cycle, 'Q' for Quarterly expirations, 'W' for Weekly expiration and 'S' for Expires 3rd Friday of the month)
                - settlementType (str): option contract settlement type AM or PM
                - optionRoots (str): The root symbol of the option (e.g., 'SPY', 'QQQ', 'AAPL')
                - standard (bool): Whether this is a standard expiration
            Returns an empty list if an error occurs or no data is available.
        """
        try:
            url = f"https://api.schwabapi.com/marketdata/v1/expirationchain?symbol={symbol}"
            
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers)
                
            if response.status_code != 200:
                raise Exception(f"Expiration chain request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            return data.get('expirationList', [])
        except Exception as e:
            print(f"❌ Error getting expiration chain: {e}")
            return None
    
    def find_next_expiration_date_greater_than_or_equal_to(self, expiration_chain: List[Dict], days_to_expiration: int) -> Optional[str]:
        """
        Find the earliest expiration date that meets or exceeds the minimum days-to-expiration requirement.
        
        Searches through the expiration chain for the symbol and returns the first expiration
        date that has at least the specified number of days remaining until expiration.
        This is useful for finding suitable expiration dates based on your trading timeframe.
        
        Args:
            expiration_chain (List[Dict]): The expiration chain list returned by get_expiration_chain.
            days_to_expiration (int): Minimum number of days to expiration required.
                                    Must be a positive integer.
            
        Returns:
            Optional[str]: The expiration date in YYYY-MM-DD format if found, 
                          or the last expiration date in the chain if no suitable expiration date exists.
                          
        Example:
            >>> # Find expiration with at least 5 days remaining
            >>> exp_date = client.find_next_expiration_date_greater_than_or_equal_to(expiration_chain, 5)
            >>> print(exp_date)
            2025-01-17
            
            >>> # If no expiration meets the requirement, returns first lest than or equal to x days to expiration (last expiration date in the chain)
            >>> exp_date = client.find_next_expiration_date_greater_than_or_equal_to(expiration_chain, 365)
            >>> print(exp_date)
            2025-11-10
        """
        try:
            # Find the first expiration date that meets or exceeds our target
            for expiration in expiration_chain:
                if expiration['daysToExpiration'] >= days_to_expiration:
                    print(f"🎯 Next expiration date with {days_to_expiration} DTE: {expiration['expirationDate']}")
                    return expiration['expirationDate']
            
            print(f"🎯 No expiration date found with {days_to_expiration} DTE, returning last expiration date: {expiration_chain[-1]['expirationDate']}")
            return expiration_chain[-1]['expirationDate']
        except Exception as e:
            print(f"❌ Error finding expiration date: {e}")
            return None

    def get_all_option_chains(self, symbol: str, expiration_date: str, contract_type: str = "ALL") -> Dict:
        """
        Retrieve complete option chain data for a specific symbol and expiration date.
        
        Fetches comprehensive option chain information including all available strikes,
        bid/ask prices, Greeks (delta, gamma, theta, vega), open interest, volume,
        and other option metrics. This is the raw data from Schwab's API that contains
        all option contracts for the specified expiration.
        
        Args:
            symbol (str): The stock ticker symbol (e.g., 'AAPL', 'SPY', 'QQQ').
            expiration_date (str): The expiration date in YYYY-MM-DD format.
                                 Must be a valid expiration date for the symbol.
            contract_type (str, optional): Filter for contract type. Options:
                - 'CALL': Retrieve only call options
                - 'PUT': Retrieve only put options
                - 'ALL': Retrieve both calls and puts (default)
            
        Returns:
            Dict: A dictionary containing complete option chain data with the following structure:
                - symbol (str): The underlying symbol
                - status (str): Request status (typically 'SUCCESS')
                - underlyingPrice (float): Current price of the underlying asset
                - daysToExpiration (int): Days remaining until expiration
                - callExpDateMap (Dict): Nested dictionary mapping expiration dates to strikes to call options
                - putExpDateMap (Dict): Nested dictionary mapping expiration dates to strikes to put options
                - Each option contract includes: bid, ask, last, mark, volume, open interest,
                  Greeks (delta, gamma, theta, vega, rho), and other metrics
            Returns an empty dictionary {} if an error occurs.
            
        Example:
            >>> chains = client.get_all_option_chains('AAPL', '2025-01-15', 'ALL')
            >>> print(f"Underlying price: ${chains['underlyingPrice']:.2f}")
            >>> print(f"Days to expiration: {chains['daysToExpiration']}")
            Underlying price: $270.70
            Days to expiration: 3
        """
        try:
            url = f"https://api.schwabapi.com/marketdata/v1/chains"
            params = {
                'symbol': symbol,
                'contractType': contract_type,
                'strikeCount': '8',
                'fromDate': expiration_date,
                'toDate': expiration_date
            }
            
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers, params=params)
                
            if response.status_code != 200:
                raise Exception(f"Option chains request failed: {response.status_code} - {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error getting option chains: {e}")
            return {}


    
    def get_option_symbols(self, symbol: str, expiration_date: str, contract_type: str = "ALL", strikes_below: int = 2, strikes_above: int = 2) -> Dict[str, List[str]]:
        """
        Get option symbols for a symbol using an intelligent strike selection strategy.
        
        This method implements a smart strike selection algorithm that focuses on
        at-the-money and near-the-money options based on the current underlying price.
        The strategy uses a round down/up approach:
        
        Both CALLS and PUTS get the same set of strikes:
        - Strikes below current price: Rounds down to get first strike, then selects
          (strikes_below - 1) additional strikes below.
          Example: Price 653.43, strikes_below=10 → [653, 652, 651, 650, 649, 648, 647, 646, 645, 644]
        
        - Strikes above current price: Rounds up to get first strike, then selects
          (strikes_above - 1) additional strikes above.
          Example: Price 653.43, strikes_above=10 → [654, 655, 656, 657, 658, 659, 660, 661, 662, 663]
        
        Total strikes for both calls and puts: strikes_below + strikes_above
        Example: strikes_below=10, strikes_above=10 → 20 strikes total (10 below + 10 above)
        
        This approach targets options with higher liquidity typically found at or near
        the current market price. The method automatically fetches the underlying price
        and filters available strikes to return only those that exist in the option chain.
        
        Args:
            symbol (str): The stock ticker symbol (e.g., 'AAPL', 'SPY', 'QQQ').
            expiration_date (str): The expiration date in YYYY-MM-DD format.
            contract_type (str, optional): Filter for contract type:
                - 'CALL': Retrieve only call option symbols
                - 'PUT': Retrieve only put option symbols
                - 'ALL': Retrieve both calls and puts (default)
            strikes_below (int, optional): Total number of strikes below current price to retrieve.
                                         Rounds down to get first strike, then gets (strikes_below - 1)
                                         more strikes below. Both calls and puts get these strikes. Default: 2
            strikes_above (int, optional): Total number of strikes above current price to retrieve.
                                         Rounds up to get first strike, then gets (strikes_above - 1)
                                         more strikes above. Both calls and puts get these strikes. Default: 2
        
        Returns:
            Dict[str, List[str]]: A dictionary containing:
                - 'calls' (List[str]): List of call option symbols (e.g., ['SPY  250115C00580000', ...])
                - 'puts' (List[str]): List of put option symbols (e.g., ['SPY  250115P00580000', ...])
                - 'strikes' (Dict): Dictionary with:
                    - 'calls' (List[float]): Strike prices for selected call options
                    - 'puts' (List[float]): Strike prices for selected put options
            Returns {'calls': [], 'puts': []} if an error occurs.
            
        Example:
            >>> # Get 10 strikes below and 10 strikes above for SPY (both calls and puts get same strikes)
            >>> symbols = client.get_option_symbols('SPY', '2025-01-15', 'ALL', strikes_below=10, strikes_above=10)
            >>> print(f"Call strikes: {symbols['strikes']['calls']}")
            >>> print(f"Put strikes: {symbols['strikes']['puts']}")
            Call strikes: [644.0, 645.0, 646.0, 647.0, 648.0, 649.0, 650.0, 651.0, 652.0, 653.0, 654.0, 655.0, 656.0, 657.0, 658.0, 659.0, 660.0, 661.0, 662.0, 663.0]
            Put strikes: [644.0, 645.0, 646.0, 647.0, 648.0, 649.0, 650.0, 651.0, 652.0, 653.0, 654.0, 655.0, 656.0, 657.0, 658.0, 659.0, 660.0, 661.0, 662.0, 663.0]
        """
        try:
            # Get all option chains in one call
            all_chains = self.get_all_option_chains(symbol, expiration_date, contract_type)
            
            option_symbols = {
                'calls': [],
                'puts': [],
                'strikes': {
                    'calls': [],
                    'puts': []
                }
            }
            
            # Get regular trading hours price instead of current option chain price
            underlying_price = self.get_symbol_price(symbol)
            
            if underlying_price <= 0:
                # Fallback to option chain price if regular hours price fails
                underlying_price = all_chains.get('underlyingPrice', 0)
                print(f"⚠️ Fallback to option chain price for {symbol}: ${underlying_price:.2f}")
            
            print(f"🎯 Strike selection for {symbol} based on underlying price: ${underlying_price:.2f}")
            
            # Collect all available strikes for calls and puts
            call_strikes = []
            put_strikes = []
            
            # Extract all call strikes
            if 'callExpDateMap' in all_chains:
                for _, strikes in all_chains['callExpDateMap'].items():
                    for strike, options in strikes.items():
                        strike_price = float(strike)
                        call_strikes.append(strike_price)
                        # Get the first call option for this strike
                        for option in options:
                            if option['putCall'] == 'CALL':
                                option_symbols['calls'].append(option['symbol'])
                                break
            
            # Extract all put strikes
            if 'putExpDateMap' in all_chains:
                for _, strikes in all_chains['putExpDateMap'].items():
                    for strike, options in strikes.items():
                        strike_price = float(strike)
                        put_strikes.append(strike_price)
                        # Get the first put option for this strike
                        for option in options:
                            if option['putCall'] == 'PUT':
                                option_symbols['puts'].append(option['symbol'])
                                break
            
            # Sort strikes
            call_strikes.sort()
            put_strikes.sort()
            
            # Calculate target strikes: both calls and puts get strikes below AND above current price
            round_down_strike = int(underlying_price)  # Floor of current price
            round_up_strike = round_down_strike + 1    # Ceiling of current price
            
            # Get strikes below current price (round down, then strikes_below - 1 more below)
            # Example: price 653.43, strikes_below=10 → [653, 652, 651, 650, 649, 648, 647, 646, 645, 644]
            strikes_below_price = [
                round_down_strike - i for i in range(strikes_below)
            ]
            
            # Get strikes above current price (round up, then strikes_above - 1 more above)
            # Example: price 653.43, strikes_above=10 → [654, 655, 656, 657, 658, 659, 660, 661, 662, 663]
            strikes_above_price = [
                round_up_strike + i for i in range(strikes_above)
            ]
            
            # Both calls and puts get the same set of strikes: below + above
            target_call_strikes = strikes_below_price + strikes_above_price
            target_put_strikes = strikes_below_price + strikes_above_price
            
            print(f"🎯 Price ${underlying_price:.2f}")
            print(f"   Strikes below: {strikes_below_price}")
            print(f"   Strikes above: {strikes_above_price}")
            print(f"   Total target strikes: {target_call_strikes}")
            
            # Filter to only include strikes that actually exist in the option chain
            # Calls and puts will get the same strikes (strikes_below below + strikes_above above)
            selected_call_strikes = [strike for strike in target_call_strikes if strike in call_strikes]
            selected_put_strikes = [strike for strike in target_put_strikes if strike in put_strikes]
            
            # Sort both in ascending order (lowest to highest) for consistency
            selected_call_strikes.sort()
            selected_put_strikes.sort()
            
            print(f"📈 Available call strikes ({len(selected_call_strikes)}): {selected_call_strikes}")
            print(f"📉 Available put strikes ({len(selected_put_strikes)}): {selected_put_strikes}")
            
            # Store the selected strikes for reference
            option_symbols['strikes']['calls'] = selected_call_strikes
            option_symbols['strikes']['puts'] = selected_put_strikes
            
            # Clear and rebuild the option symbols lists with only the selected strikes
            option_symbols['calls'] = []
            option_symbols['puts'] = []
            
            # Get call symbols for selected strikes
            if 'callExpDateMap' in all_chains:
                for _, strikes in all_chains['callExpDateMap'].items():
                    for strike, options in strikes.items():
                        strike_price = float(strike)
                        if strike_price in selected_call_strikes:
                            for option in options:
                                if option['putCall'] == 'CALL':
                                    option_symbols['calls'].append(option['symbol'])
                                    break
            
            # Get put symbols for selected strikes
            if 'putExpDateMap' in all_chains:
                for _, strikes in all_chains['putExpDateMap'].items():
                    for strike, options in strikes.items():
                        strike_price = float(strike)
                        if strike_price in selected_put_strikes:
                            for option in options:
                                if option['putCall'] == 'PUT':
                                    option_symbols['puts'].append(option['symbol'])
                                    break
            
            print(f"🎯 Option symbols for {symbol} at {expiration_date}: {option_symbols}")
            return option_symbols
            
        except Exception as e:
            print(f"❌ Error getting option symbols: {e}")
            return {'calls': [], 'puts': []}

    def get_option_symbols_for_multiple_symbols(self, symbols: List[str], days_to_expiration: List[int], contract_type: str, strikes_below: int, strikes_above: int) -> Dict[str, Dict[str, List[str]]]:
        """
        Batch process multiple symbols, pairing each symbol with its corresponding DTE value by index.
        
        This method processes symbols and days-to-expiration in a paired fashion:
        - SYMBOL[0] is paired with DAYS_TO_EXPIRATION[0]
        - SYMBOL[1] is paired with DAYS_TO_EXPIRATION[1]
        - etc.
        
        For each symbol-DTE pair, it finds the appropriate expiration date that meets the
        minimum days-to-expiration requirement, then retrieves option symbols for that combination.
        
        The results are organized by composite keys in the format: "{symbol}_{expiration_date}",
        allowing you to easily identify which symbols and expiration dates each result set
        corresponds to.
        
        Args:
            symbols (List[str]): List of stock ticker symbols to process.
                               Example: ['SPY', 'QQQ']
            days_to_expiration (List[int]): List of minimum days-to-expiration requirements.
                                          Each value is paired with the symbol at the same index.
                                          Must have the same length as symbols.
                                          Example: [2, 3] pairs with ['SPY', 'QQQ'] means
                                          SPY uses 2 DTE and QQQ uses 3 DTE.
            contract_type (str): Filter for contract type:
                - 'CALL': Retrieve only call option symbols
                - 'PUT': Retrieve only put option symbols
                - 'ALL': Retrieve both calls and puts
            strikes_below (int): Number of strikes below current price (passed to get_option_symbols).
            strikes_above (int): Number of strikes above current price (passed to get_option_symbols).
        
        Returns:
            Dict[str, Dict[str, List[str]]]: A dictionary where each key is a composite string
            in the format "{symbol}_{expiration_date}" (e.g., "SPY_2025-01-15"), and each value
            is a dictionary containing:
                - 'calls' (List[str]): List of call option symbols
                - 'puts' (List[str]): List of put option symbols
                - 'strikes' (Dict): Dictionary with 'calls' and 'puts' strike price lists
            Returns an empty dictionary if no valid combinations are found.
            
        Example:
            >>> symbols = ['SPY', 'QQQ']
            >>> dte_list = [2, 3]
            >>> results = client.get_option_symbols_for_multiple_symbols(symbols, dte_list, 'ALL', 2, 2)
            >>> for key, data in results.items():
            ...     print(f"{key}: {len(data['calls'])} calls, {len(data['puts'])} puts")
            SPY_2025-01-15: 2 calls, 2 puts  # SPY with 2 DTE
            QQQ_2025-01-17: 2 calls, 2 puts  # QQQ with 3 DTE
        """
        all_option_symbols = {}
        
        # Validate that lists have the same length
        if len(symbols) != len(days_to_expiration):
            print(f"❌ Error: symbols and days_to_expiration must have the same length. Got {len(symbols)} symbols and {len(days_to_expiration)} DTE values.")
            return all_option_symbols
        
        # Pair each symbol with its corresponding DTE value by index
        for symbol, dte in zip(symbols, days_to_expiration):
            print(f"🔍 Processing {symbol} with {dte} DTE...")
            
            # Fetch expiration chain for this symbol
            expiration_chain = self.get_expiration_chain(symbol)
            if not expiration_chain:
                print(f"❌ No expiration chain found for {symbol}")
                continue
            
            # Find expiration date for this symbol's DTE requirement
            expiration_date = self.find_next_expiration_date_greater_than_or_equal_to(expiration_chain, dte)
            if not expiration_date:
                print(f"❌ No suitable expiration date found for {symbol} with {dte} DTE")
                continue
            
            print(f"📅 {symbol} expiration date: {expiration_date}")
            
            # Get option symbols for this symbol
            option_symbols = self.get_option_symbols(symbol, expiration_date, contract_type=contract_type, strikes_below=strikes_below, strikes_above=strikes_above)
            print(f"🎯 {symbol}: {len(option_symbols['calls'])} calls, {len(option_symbols['puts'])} puts")
            
            # Store results in the dictionary with a composite key
            key = f"{symbol}_{expiration_date}"
            all_option_symbols[key] = option_symbols
                
        return all_option_symbols

def main():
    # Example usage
    ACCESS_TOKEN_FILE_PATH = 'schwab_access_token.txt'
    DAYS_TO_EXPIRATION = [2, 3]
    SYMBOLS = ['SPY', 'QQQ']
    STRIKES_BELOW = 3
    STRIKES_ABOVE = 3
    CONTRACT_TYPE = "ALL"
    all_option_symbols = SchwabOptionsApiClient(ACCESS_TOKEN_FILE_PATH).get_option_symbols_for_multiple_symbols(SYMBOLS, DAYS_TO_EXPIRATION, CONTRACT_TYPE, STRIKES_BELOW, STRIKES_ABOVE)
    
    # Print formatted results
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    for key, option_data in all_option_symbols.items():
        symbol, expiration_date = key.split('_')
        print(f"\n{symbol} - {expiration_date}")
        print(f"  Calls ({len(option_data['calls'])}): {option_data['calls']}")
        print(f"  Puts ({len(option_data['puts'])}): {option_data['puts']}")
        if 'strikes' in option_data:
            print(f"  Call strikes: {option_data['strikes']['calls']}")
            print(f"  Put strikes: {option_data['strikes']['puts']}")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
