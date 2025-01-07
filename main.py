from alpaca.data.timeframe import TimeFrame
from CryptoDataFetcher import CryptoDataFetcher
from Strategies.MeanReversion import MeanReversion
import pandas as pd

start, end = "2023-01-01", '2024-11-26'
dataFetcher = CryptoDataFetcher('BTC/USD', TimeFrame.Hour, start, end) # symbol, timeframe, startDate, endDate

BTC_df = dataFetcher.fetch_data()

BTC_df.index = pd.to_datetime([x[1] for x in BTC_df.index]) # this for hour
BTC_df["lagged_close"] = BTC_df['close'].shift(1)
features = BTC_df[['lagged_close', 'high', 'low', 'open', 'volume', 'vwap']].iloc[:-1]
print(BTC_df)

# include a class to save & fetch the data so we dont have to fetch it every single time.

dataFetcher = CryptoDataFetcher('ETH/USD', TimeFrame.Hour, start, end) # symbol, timeframe, startDate, endDate

ETH_df = dataFetcher.fetch_data()
ETH_df.index = pd.to_datetime([x[1] for x in ETH_df.index]) # this for hour
ETH_df["lagged_close"] = ETH_df['close'].shift(1)
features = ETH_df[['lagged_close', 'high', 'low', 'open', 'volume', 'vwap']].iloc[:-1]
print(ETH_df)


merged_df = pd.merge(BTC_df['close'], ETH_df['close'], left_index=True, right_index=True, how ="inner")
merged_df.dropna()
merged_df.rename(columns = {'close_x' : 'BTC', 'close_y' : 'ETH'}, inplace=True)

midpoint = len(merged_df) // 2
train_data = merged_df.iloc[:midpoint].copy()
test_data = merged_df.iloc[midpoint:].copy()

mean_reversion = MeanReversion(train_data)
mean_reversion.is_conintegrated('BTC', 'ETH')
