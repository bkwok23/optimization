import statistics_lib as stat

import datetime as dt
import pandas as pd

def run_backtest():
    # cash drag
    _cash = 50 / 1e5
    initial_portfolio_wt = {"BNS CN": (1 - _cash) / 6, "BMO CN": (1 - _cash) / 6, "TD CN": (1 - _cash) / 6,
                            "CM CN": (1 - _cash) / 6, "RY CN": (1 - _cash) / 6, "NA CN": (1 - _cash) / 6, "cash": _cash}

    # retrieve the total returns matrix for each security
    df_returns_matrix = stat.calc_returns_matrix(sec_list=list(initial_portfolio_wt.keys()))

    x = stat.calc_port_return(dates_list=pd.to_datetime(df_returns_matrix.index), initial_ticker_weights=initial_portfolio_wt, tr_matrix=df_returns_matrix)
    x.to_csv("backtest_results.csv", index=False)

def load_results():
    return pd.read_csv("backtest_results.csv")

if __name__ == '__main__':
    # run_backtest()
    print(load_results())


