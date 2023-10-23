import pandas as pd
import numpy as np
from modules.ma_crossover_strategy.hedge_functions import (
    CAGR,
    total_return_multiple,
    volatility,
    sharpe,
    max_dd,
)
from flask_table import Table, Col
import jinja2


class KPIs(Table):
    kpi = Col("KPI")
    long_only = Col("Long only with signal")
    long_only_no_signal = Col("Long only (no signal)")


def calculate_kpis(strat_returns):
    """
    Calculates the key performance indicators (KPIs) for a given set of strategy returns.
    Parameters:
    strat_returns (pandas DataFrame): DataFrame containing strategy returns.
    Returns:
    data (list): List of KPI data.
    """
    # Calculating long-only strategy KPIs with signal
    strategy_df = pd.DataFrame()
    strategy_df["Returns"] = strat_returns["Returns"]
    strategy_df["Returns"] = strategy_df.mean(axis=1)
    strategy_df["cum_return"] = (1 + strategy_df["Returns"]).cumprod()
    strategy_df["Position"] = strat_returns["Position"]

    # Calculating long-only strategy KPIs without signal
    strategy_df_2 = pd.DataFrame()
    strategy_df_2["Returns_T"] = strat_returns["All Returns"]
    strategy_df_2["Returns_T"] = strategy_df_2.mean(axis=1)
    strategy_df_2["Position"] = strategy_df["Position"]
    idx = strategy_df_2["Position"].eq(1).idxmax()
    strategy_df_2.loc[idx:, "Position"] = 1
    strategy_df_2["Returns"] = strategy_df_2["Returns_T"] * strategy_df_2["Position"]
    strategy_df_2["cum_return"] = (1 + strategy_df_2["Returns"]).cumprod()

    # calculate number of trades
    strat_returns["Trades"] = strat_returns["Signal"].diff().fillna(0).abs()
    number_of_trades = int(strat_returns["Trades"].sum())
    #print("Number of trades: ", number_of_trades)

    data = [
        {
            "kpi": "CAGR",
            "Strategy": "{:.1%}".format(CAGR(strategy_df)),
            "Stock": "{:.1%}".format(CAGR(strategy_df_2)),
        },
        {
            "kpi": "Sharpe ratio",
            "Strategy": "{:.2f}".format(sharpe(strategy_df, 0.025)),
            "Stock": "{:.2f}".format(sharpe(strategy_df_2, 0.025)),
        },
        {
            "kpi": "Max Drawdown",
            "Strategy": "{:.0%}".format(max_dd(strategy_df)),
            "Stock": "{:.0%}".format(max_dd(strategy_df_2)),
        },
        {
            "kpi": "Total return multiple",
            "Strategy": "{:.1f}x".format(total_return_multiple(strategy_df)),
            "Stock": "{:.1f}x".format(total_return_multiple(strategy_df_2)),
        },
    ]

    data_df = pd.DataFrame(data).set_index('kpi').T

    # HTML template
    template = """
    <div class="mt-8 overflow-x-auto">
        <div class="align-middle inline-block min-w-full shadow sm:rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-sm font-medium text-gray-900"></th>
                        <th scope="col" class="px-6 py-3 text-center text-sm font-medium text-gray-900">CAGR</th>
                        <th scope="col" class="px-6 py-3 text-center text-sm font-medium text-gray-900">Sharpe Ratio</th>
                        <th scope="col" class="px-6 py-3 text-center text-sm font-medium text-gray-900">Max Drawdown</th>
                        <th scope="col" class="px-6 py-3 text-center text-sm font-medium text-gray-900">Total Return</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {% for index, row in data_df.iterrows() %}
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-left font-medium text-gray-900">{{ index }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center text-gray-500">{{ row['CAGR'] }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center text-gray-500">{{ row['Sharpe ratio'] }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center text-gray-500">{{ row['Max Drawdown'] }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center text-gray-500">{{ row['Total return multiple'] }}</td>
                    </tr>
                    {% endfor %}
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-left font-medium text-gray-900">Number of trades</td>
                        <td class="px-6 py-4 whitespace-nowrap text-center text-gray-500">{{ number_of_trades }}</td>
                        <td colspan="3"></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """

    # Render the template with the data
    table_html = jinja2.Template(template).render(data_df=data_df, number_of_trades=number_of_trades)

    return table_html
