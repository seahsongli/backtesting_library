from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
class CryptoDataFetcher:
    def __init__(self, symbol, timeframe, startDate, endDate):
        self.client = CryptoHistoricalDataClient()
        self.request_params =  CryptoBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=timeframe,
            start=startDate, # MSTR started buying bitcon since Aug 2020
            end=endDate,
        )

    def fetch_data(self):
        try:
            data = self.client.get_crypto_bars(self.request_params)
            df = data.df  # Assuming the API returns a DataFrame
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
   