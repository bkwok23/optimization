import datetime as dt
import pandas as pd
import numpy as np
import os.path

class equity_returns():
    def __init__(self, stock_ticker:str, start_date:dt.datetime=None, end_date:dt.datetime=dt.datetime.now()):
        """
        This class calculates the equity returns using the securities pricing and dvd

        :param stock_ticker: Bloomberg ticker of the security: ie. AAPL US
        :param start_date: the date where we want to begin looking at the training data. by default we go as far back as possible
        :param end_date: the date where we want to end looking at the training data. by default we look at data until today

        Last Updated June 03, 2024
        """

        self.ticker_exch = stock_ticker
        self.ticker = stock_ticker.split(" ")[0]

        # Retrieve dividends data
        dvd_file = self.retrieve_dvd_data(start_date, end_date)

        # Retrieve market data
        df_stock_returns = self.retrieve_market_data(start_date, end_date)

        # merge dividend rate with stock returns dataset
        df_stock_returns["dvd_amount"] = df_stock_returns["Dates"].map(dict(zip(dvd_file["ex_date"], dvd_file["dvd_amount"])))

        # calculate the total return
        self.total_return = self.total_return_calc(df_stock_returns, "PX_LAST", "dvd_amount")


    def retrieve_market_data(self, _start_date:dt.datetime, _end_date:dt.datetime) -> pd.DataFrame:
        """
        Retrieve market data
        :param _start_date: the date where we want to begin looking at the training data. by default we go as far back as possible
        :param _end_date: the date where we want to end looking at the training data. by default we look at data until today
        :return: market data for the security with the relevant timeframe
        """

        mkt_data_fname = f"market_data\\{self.ticker}.csv"
        if not os.path.isfile(mkt_data_fname):
            raise ValueError(f"Erorr: No Market Data available for: {self.ticker}")
        else:
            market_data = pd.read_csv(f"market_data\\{self.ticker}.csv")
            # filter data so that it is within the specified range start_date/end_date
            market_data = market_data[pd.to_datetime(market_data["Dates"]) <= _end_date]
            if not _start_date is None:
                market_data = market_data[pd.to_datetime(market_data["Dates"]) >= _start_date]
        return market_data


    def retrieve_dvd_data(self, _start_date:dt.datetime, _end_date:dt.datetime) -> pd.DataFrame:
        """
        Retrieve dividends data
        :param _start_date: the date where we want to begin looking at the training data. by default we go as far back as possible
        :param _end_date: the date where we want to end looking at the training data. by default we look at data until today
        :return: dividend rates for the security with the relevant timeframe
        """

        dvd_data_fname = f"market_data\\dividends.csv"
        if not os.path.isfile(dvd_data_fname):
            raise ValueError(f"Error: Dividend File does not exist.")
        else:
            dvd_data = pd.read_csv(dvd_data_fname)
            # filter by ticker
            dvd_data = dvd_data[dvd_data["ticker"] == self.ticker_exch]
            if dvd_data.empty:
                print(f"No Dividend Data for: {self.ticker_exch}")
            else:
                # filter data so that it is within the specified range start_date/end_date
                dvd_data["ex_date"] = pd.to_datetime(dvd_data["ex_date"]).dt.strftime("%Y-%m-%d")
                dvd_data = dvd_data[pd.to_datetime(dvd_data["ex_date"]) <= _end_date]
                if not _start_date is None:
                    dvd_data = dvd_data[pd.to_datetime(dvd_data["ex_date"]) >= _start_date]
        return dvd_data


    def total_return_calc(self, data: pd.DataFrame, price_col: str, dvd_col: str):
        """
        This function calculates the Total Return of a security. Includes dividend reinvestments

        :param data: dataset of prices and dividends
        :param price_col: name of the price column
        :param dvd_col: name of the dividend column
        :return: adds a column called total_return_price which is the price of the security with reinvestment

        Last Updated June 03, 2024
        """

        data = data.reset_index(drop=True)

        # format the dvd col
        data[dvd_col] = data[dvd_col].fillna(0)
        data[dvd_col] = np.where(data[dvd_col] == str(""), 0, data[dvd_col])

        # add placeholder column for dvd reinvestments
        data["dvd_reinvestment"] = None

        # calculate the dividend reinvestment returns
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
    # May need to add a parameter to indicate the relevant timeframe

    """
    This function calculates a return matrix for a list of securities
    :param sec_list: provide a list of securities
    :return: function returns that list of securities total returns matrix
    """

    #initiate the total returns matrix
    total_returns_matrix = pd.DataFrame()
    count = 0

    #ensure that cash is not the first asset. otherwise there will be an error since cash defaults every day to 0, there is no date range.
    if "cash" in sec_list:
        sec_list.remove("cash")
        sec_list += ["cash"]

    for sec in sec_list:
        count += 1
        print(f"Calculating data for {sec}: {count}/{len(sec_list)}")
        if sec == "cash":
            total_returns_matrix['cash'] = 0
        else:
            # calculate the total return of the security
            sec_data = equity_returns(sec)
            security_tr = sec_data.total_return

            # calculate the daily returns
            security_tr[sec] = security_tr['total_return_price'].diff(1)/security_tr['total_return_price']

            if total_returns_matrix.empty:
                total_returns_matrix = security_tr[['Dates']] # can be a potential flaw. data goes as far back as the first security
                total_returns_matrix[sec] = total_returns_matrix['Dates'].map(dict(zip(security_tr['Dates'], security_tr[sec])))
            else:
                total_returns_matrix[sec] = total_returns_matrix['Dates'].map(dict(zip(security_tr['Dates'], security_tr[sec])))

    #forward fill and back fill returns
    for col in total_returns_matrix.columns:
        total_returns_matrix[col] = total_returns_matrix[col].ffill()
        total_returns_matrix[col] = total_returns_matrix[col].bfill()

    return total_returns_matrix.set_index('Dates').iloc[1:]

def calc_portfolio_period_return(start_date:dt.datetime, end_date:dt.datetime, ticker_weights: dict, tr_matrix:pd.DataFrame) -> dict:
    """
    Calculates the portfolios total return and its ending weights.

    :param start_date: start date which returns are anchored to.
    :param end_date: end date.
    :param ticker_weights: dictionary with the ticker and its initial weights
    :param tr_matrix: total returns matrix
    :return: dataframe of each securities period return and its drifted weight. Can derive the total portfolio return by taking the sumproduct of the initial weights and the (1 + period returns)

    Last Updated June 08 2024
    """

    return_attribution = pd.DataFrame(data=list(ticker_weights.keys()), columns=["ticker"])
    return_attribution["start_wt"] = return_attribution["ticker"].map(ticker_weights)
    return_attribution["start_date"] = start_date
    return_attribution["end_date"] = end_date

    tr_matrix = tr_matrix.reset_index()
    tr_matrix["Dates"] = pd.to_datetime(tr_matrix["Dates"])

    # only take the relevant returns in the timeframe
    tr_matrix_subset = tr_matrix[(tr_matrix["Dates"] > start_date) & (tr_matrix["Dates"] <= end_date)]

    period_return = {}
    for col in tr_matrix_subset.columns:
        if col in list(ticker_weights.keys()):
            period_return[col] = (1+tr_matrix_subset[col]).prod()-1

    return_attribution["period_return"] = return_attribution["ticker"].map(period_return)
    return_attribution["end_wt"] = (1+return_attribution["period_return"])*return_attribution["start_wt"] / ((1+return_attribution["period_return"])*return_attribution["start_wt"]).sum()
    return return_attribution

def calc_port_return(dates_list:list, initial_ticker_weights: dict, tr_matrix:pd.DataFrame) -> dict:
    """
    Calculates the portfolios total return and its ending weights.

    :param dates_list: list of dates to calculate returns off of. the minimum date is the start date which returns are anchored to.
    :param ticker_weights: dictionary with the ticker and its initial weights
    :param tr_matrix: total returns matrix
    :return: dataframe of each securities period return and its drifted weight. Can derive the total portfolio return by taking the sumproduct of the initial weights and the (1 + period returns)

    Last Updated June 08 2024
    """

    all_port_returns = pd.DataFrame()
    sorted_dates = sorted(dates_list)
    for idx, _start_d in enumerate(sorted_dates):
        if _start_d == max(dates_list):
            break

        if _start_d == min(dates_list):
            period_return = calc_portfolio_period_return(start_date=_start_d, end_date=sorted_dates[idx+1], ticker_weights=initial_ticker_weights, tr_matrix=tr_matrix)
        else:
            prior_portfolio = period_return
            prior_port_weights = dict(zip(prior_portfolio["ticker"], prior_portfolio["end_wt"]))
            period_return = calc_portfolio_period_return(start_date=_start_d, end_date=sorted_dates[idx+1], ticker_weights=prior_port_weights, tr_matrix=tr_matrix)

        if all_port_returns.empty:
            all_port_returns = period_return
        else:
            all_port_returns = pd.concat([all_port_returns, period_return])

    return all_port_returns

if __name__ == '__main__':
    #initial portfolio weights
    benchmark_portfolio = {"BNS CN": 1/6, "BMO CN": 1/6, "TD CN": 1/6, "CM CN": 1/6, "RY CN": 1/6, "NA CN": 1/6, "cash": 0}
    _cash = 50/10000
    cash_drag_portfolio = {"BNS CN": (1-_cash)/6, "BMO CN": (1-_cash)/6, "TD CN": (1-_cash)/6, "CM CN": (1-_cash)/6, "RY CN": (1-_cash)/6, "NA CN": (1-_cash)/6, "cash": _cash}

    # retrieve the total returns matrix for each security
    df_returns_matrix = calc_returns_matrix(sec_list=list(benchmark_portfolio.keys()))

    benchmark = calc_port_return(dates_list=[dt.datetime(2023, 11, 30), dt.datetime(2023, 12, 1), dt.datetime(2023, 12, 4)], ticker_weights=benchmark_portfolio, tr_matrix=df_returns_matrix)

    banks_list = ["BNS CN", "BMO CN", "TD CN", "CM CN", "RY CN", "NA CN"]
    ret = calc_returns_matrix(banks_list)
    cov_matrix = ret.cov()
    print(sec)