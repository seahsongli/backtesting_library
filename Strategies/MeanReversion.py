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