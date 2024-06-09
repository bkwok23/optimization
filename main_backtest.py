import statistics_lib as stat
import optimization_lib as opt

import datetime as dt
import pandas as pd

if __name__ == '__main__':
    benchmark_wt = {"BNS CN": 1/6, "BMO CN": 1/6, "TD CN": 1/6, "CM CN": 1/6, "RY CN": 1/6, "NA CN": 1/6, "cash": 0}

    _cash = 500/1e4
    default_portfolio_wt = {"BNS CN": (1-_cash)/6, "BMO CN": (1-_cash)/6, "TD CN": (1-_cash)/6, "CM CN": (1-_cash)/6, "RY CN": (1-_cash)/6, "NA CN": (1-_cash)/6, "cash": _cash}
    df_returns_matrix = stat.calc_returns_matrix(sec_list=list(benchmark_wt.keys()), start_date=dt.datetime(2023, 1, 4))

    # Find the optimized portfolio to replicate the benchmark given the cash drag
    sol = opt.minimize_active_risk(benchmark_portfolio=benchmark_wt, cash_drag=_cash, tr_matrix=df_returns_matrix.loc[:"2023-12-29"])

    # backtest portfolios
    optimized = stat.calc_port_return(dates_list=pd.to_datetime(df_returns_matrix.loc["2024-01-02":].index), initial_ticker_weights=sol, tr_matrix=df_returns_matrix)
    bench = stat.calc_port_return(dates_list=pd.to_datetime(df_returns_matrix.loc["2024-01-02":].index), initial_ticker_weights=benchmark_wt, tr_matrix=df_returns_matrix)
    default = stat.calc_port_return(dates_list=pd.to_datetime(df_returns_matrix.loc["2024-01-02":].index), initial_ticker_weights=default_portfolio_wt, tr_matrix=df_returns_matrix)

    # sum optimized portfolio return
    optimized["weighted_return"] = optimized["start_wt"]*optimized["period_return"]
    optimized_port_returns = optimized.groupby(by=["start_date", "end_date"], group_keys=True)[["weighted_return"]].apply(sum).reset_index()

    # sum benchmark portfolio return
    bench["weighted_return"] = bench["start_wt"]*bench["period_return"]
    bench_port_returns = bench.groupby(by=["start_date", "end_date"], group_keys=True)[["weighted_return"]].apply(sum).reset_index()

    # sum default portfolio return
    default["weighted_return"] = default["start_wt"]*default["period_return"]
    default_port_returns = default.groupby(by=["start_date", "end_date"], group_keys=True)[["weighted_return"]].apply(sum).reset_index()

    # Consolidate and summarize the different portfolios
    comparison = bench_port_returns[["start_date", "end_date"]]
    comparison["bench"] = comparison["start_date"].map(dict(zip(bench_port_returns["start_date"], bench_port_returns["weighted_return"])))
    comparison["bench_cumprod"] = (1+comparison["bench"]).cumprod()-1
    comparison["optimized"] = comparison["start_date"].map(dict(zip(optimized_port_returns["start_date"], optimized_port_returns["weighted_return"])))
    comparison["optimized_cumprod"] = (1 + comparison["optimized"]).cumprod() - 1
    comparison["default"] = comparison["start_date"].map(dict(zip(default_port_returns["start_date"], default_port_returns["weighted_return"])))
    comparison["default_cumprod"] = (1 + comparison["default"]).cumprod() - 1

    # Analysis Statistics
    print(f"Bench - Optimized Daily Std Dev: {1e4*(comparison['bench']-comparison['optimized']).std()}bps")
    print(f"Bench - Default Daily Std Dev: {1e4*(comparison['bench'] - comparison['default']).std()}bps")


    # Graph Results
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))

    plt.plot(pd.to_datetime(comparison["start_date"]), comparison["bench_cumprod"], label="bench")
    plt.plot(pd.to_datetime(comparison["start_date"]), comparison["optimized_cumprod"], label="optimized")
    plt.plot(pd.to_datetime(comparison["start_date"]), comparison["default_cumprod"], label="default")

    plt.title('Portfolio Returns Optimization Vs. Default')
    plt.xlabel('Date')
    plt.ylabel('Return')
    plt.legend(loc='upper left')

    plt.show()


