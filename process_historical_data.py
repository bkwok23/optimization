import datetime as dt
import pandas as pd
import numpy as np

class equity_returns():
    def __init__(self, stock_ticker:str):
        """
        This class calculates the equity returns using the securities pricing and dvd

        :param stock_ticker: Bloomberg ticker of the security: ie. AAPL US

        Last Updated June 03, 2024
        """

        self.ticker_exch = stock_ticker
        self.ticker = stock_ticker.split(" ")[0]

        dvd_file = pd.read_csv(f"market_data\\dividends.csv")
        dvd_file["ex_date"] = pd.to_datetime(dvd_file["ex_date"]).dt.strftime("%Y-%m-%d")
        dvd_file = dvd_file[dvd_file["ticker"] == self.ticker_exch]

        df_stock_returns = pd.read_csv(f"market_data\\{self.ticker}.csv")
        df_stock_returns["ex_date"] = df_stock_returns["Dates"].map(dict(zip(dvd_file["ex_date"], dvd_file["dvd_amount"])))

        self.total_return = self.total_return_calc(df_stock_returns, "PX_LAST", "ex_date")

    def total_return_calc(self, input_data: pd.DataFrame, price_col: str, dvd_col: str):
        """
        This function calculates the Total Return of a security

        :param data: DataFrame of prices and dividends
        :param price_col: name of the price column
        :param dvd_col: name of the dividend column
        :return: adds a column called total_return_price which is the price of the security with reinvestment

        Last Updated June 03, 2024
        """

        data = input_data.copy(deep=True).reset_index(drop=True)
        data[dvd_col] = data[dvd_col].fillna(0)
        data[dvd_col] = np.where(data[dvd_col] == str(""), 0, data[dvd_col])
        data["dvd_reinvestment"] = None

        for row in data.itertuples():
            if row.Index == 0:
                if (data.loc[row.Index, dvd_col] > 0):
                    raise Exception("There cannot be a dividend on the first day otherwise we cannot properly calculate the reinvestment.")
                else:
                    data.loc[row.Index, "dvd_reinvestment"] = 0
            else:
                if (data.loc[row.Index, dvd_col] > 0):
                    daily_return = data.loc[row.Index, price_col] / (data.loc[row.Index - 1, price_col] - data.loc[row.Index, dvd_col])
                    data.loc[row.Index, "dvd_reinvestment"] = (data.loc[row.Index - 1, "dvd_reinvestment"] + data.loc[row.Index, dvd_col]) * daily_return
                else:
                    daily_return = data.loc[row.Index, price_col] / data.loc[row.Index - 1, price_col]
                    data.loc[row.Index, "dvd_reinvestment"] = data.loc[row.Index - 1, "dvd_reinvestment"] * daily_return

        data['total_return_price'] = data['dvd_reinvestment'] + data[price_col]
        return data

def calc_returns_matrix(sec_list:list):
    output = pd.DataFrame()
    count = 0
    for sec in sec_list:
        count += 1
        print(f"Calculating data for security: {count}/{len(sec_list)}")
        sec_data = equity_returns(sec)
        df_returns = sec_data.total_return
        df_returns[sec] = df_returns['total_return_price'].diff(1)/df_returns['total_return_price']
        if output.empty:
            output = df_returns[['Dates']]
            output[sec] = output['Dates'].map(dict(zip(df_returns['Dates'], df_returns[sec])))
        else:
            output[sec] = output['Dates'].map(dict(zip(df_returns['Dates'], df_returns[sec])))

    output['cash'] = 0
    return output.set_index('Dates').iloc[1:]

if __name__ == '__main__':
    banks_list = ["BNS CN", "BMO CN", "TD CN", "CM CN", "RY CN", "NA CN"]
    ret = calc_returns_matrix(banks_list)
    cov_matrix = ret.cov()
    print(sec)