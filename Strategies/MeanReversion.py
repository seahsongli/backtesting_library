import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import coint
from Strategies.Strategy import Strategy
class MeanReversion(Strategy):
    def __init__(self, data):
        super().__init__(data)
        
    def is_conintegrated(self, symbol1, symbol2, signfiance_level=0.05):
        x = sm.add_constant(self.data[symbol1]) # add constant for regression, so that we dont force the model to go through origin, which can lead to poor fit.
        y = self.data[symbol2]
        model = sm.OLS(y,x).fit() # Orinary least squares. Trying to explain dependent variable based on x

        self.data.loc[:, "residuals"] = model.resid # difference between the MSTR and values predicted by model. i.e. error
        self.hedge_ratio = model.params[1]
        # Adf test tests the null hypothesis that series has a unit root, which would imply non-stationarity 
        adf_test = adfuller(self.data['residuals'])

        # Print results => If two series are cointegrated, it means that residuals from the regression should be stationary.
        print("ADF Statistic:", adf_test[0])
        print("p-value:", adf_test[1])
        print("Critical Values:", adf_test[4])

        # Check if p-value < 0.05 (or chosen significance level)
        if adf_test[1] < signfiance_level:
            print("The series are cointegrated.")
            return True
        else:
            print("The series are not cointegrated.")
            return False
        
    def execute_strategy(self, symbol1, symbol2, spread_df, rolling_window=10, initial_balance=100000):
        # spread_df = pd.merge(BTC_df['lagged_close'], ETH_df['lagged_close'], left_index=True, right_index=True, how ="inner")
        spread_df['lagged_spread'] = spread_df[symbol1] - self.hedge_ratio * spread_df[symbol2]
        spread = spread_df['lagged_spread'].copy()
        rolling_mean = spread.rolling(window=rolling_window).mean()
        rolling_std = spread.rolling(window=rolling_window).std()
        z_score = (spread-rolling_mean) / rolling_std

        entry_threshold = 2 # spread is 2 std deivation above mean
        exit_threshold = 0 # Neutral zone to avoid overtrading, gives us some lienecy 

        self.data['long_signal'] = z_score < -entry_threshold # long signal means u long BTC and short ETH
        self.data['short_signal'] = z_score > entry_threshold # short signal means u short BTC and long ETH
        self.data['exit_long_signal'] = z_score < exit_threshold 
        self.data['exit_short_signal'] = z_score > -exit_threshold

        # Simulate the trading signals
        position = 0
        trade_log = []
        cash_balance = initial_balance # this is used to keep track of final amount

        pnl = []
        balance_history = [] # This is to calculate sharpe ratio
        daily_returns = [] # This is to calculate sharpe ratio
        position_history = []
        entry_history = []
        exit_history = []
        symbol1_entry_price = None 
        symbol2_entry_price = None

        for i in range(len(self.data)):
            symbol1_price, symbol2_price = self.data[symbol1].iloc[i], self.data[symbol2].iloc[i]
            timestamp = self.data.index[i]
            current_value = 0
            if position == 1 and self.data['exit_long_signal'].iloc[i]: # to close long position
                profit_loss = (symbol1_price - symbol1_entry_price) + (symbol2_entry_price - symbol2_price) 
                pnl.append(profit_loss)
                position = 0
                symbol1_entry_price = symbol2_entry_price = None
                cash_balance+=profit_loss
                trade_log.append(f"Exit long position for {symbol1} at price: {symbol1_price} and exit short position for {symbol2}: {symbol2_price} on day {i}") 
            elif position == -1 and self.data['exit_short_signal'].iloc[i]: # to close short position
                profit_loss = (symbol1_entry_price - symbol1_price) + (symbol2_price - symbol2_entry_price)
                pnl.append(profit_loss)
                position = 0
                btc_entry_price = eth_entry_price = None
                cash_balance+=profit_loss
                trade_log.append(f"Exit short position for {symbol1} at price: {symbol1_price} and exit long position for {symbol2}: {symbol2_price} on day {i}") 
            # If there are no current positions
            elif position == 0:
                if self.data['long_signal'].iloc[i] == 1: # if we have no positon and there is a long signal
                    symbol1_entry_price = symbol1_price
                    symbol2_entry_price = symbol2_price
                    position = 1
                if self.data['short_signal'].iloc[i] == 1:
                    symbol1_entry_price = symbol1_price
                    symbol2_entry_price = symbol2_price
                    position = -1
                
            if position == 1:
                current_value =  (symbol1_price - symbol1_entry_price) + (symbol2_entry_price - symbol2_price) 
            elif position == -1:
                current_value = (symbol1_entry_price - symbol1_entry_price) + (symbol2_price - symbol2_entry_price)
            total_balance = current_value + cash_balance # including today's pnl
            balance_history.append(total_balance)

            if i > 0: # if we are not on the first day
                daily_return = (total_balance - balance_history[-2]) / balance_history[-2]
            else:
                daily_return = 0
            daily_returns.append(daily_return)
            position_history.append((position, timestamp))
            balance_history.append(cash_balance)
        final_balance = cash_balance
        total_pnl = sum(pnl)

        print("Number of long signals", self.data['long_signal'].sum())
        print("Number of sell signals", self.data['short_signal'].sum())
        # print("Number of exit signals", train_data['exit_signal'].sum())
        # print(pnl)
        print("Total pnl for the entire period: ", total_pnl)