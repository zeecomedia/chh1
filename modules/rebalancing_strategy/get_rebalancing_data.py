import pandas as pd
import yfinance as yf
import numpy as np


def get_rebalancing_data(
    stock1: str,
    stock2: str,
    weight1: float,
    rebalancing_period: int,
    start_date: str,
    end_date: str,
):
    print("get_rebalancing_data() called")
    # capitalize stock1
    stock1 = stock1.upper()
    stock2 = stock2.upper()
    weight1 = weight1
    rebalancing_period = int(rebalancing_period)
    start_date = start_date
    end_date = end_date

    weight2 = 1 - float(weight1)

    tickers = [stock1, stock2]
    portfolio_weights = {stock1: weight1, stock2: weight2}

    # Download historical data for tickers
    ohlc_data = yf.download(tickers, start_date, end_date)["Close"]
    ohlc_data = ohlc_data.dropna()  # Remove any rows with missing data

    initial_value = 1000
    portfolio_value = [initial_value]

    # Initialize the starting weights based on the initial portfolio value
    current_weights = {
        ticker: (float(initial_value) * float(portfolio_weights[ticker]))
        / float(ohlc_data[ticker][0])
        for ticker in tickers
    }

    # Create a list of rebalancing dates
    rebalance_dates = pd.date_range(
        start_date, end_date, freq=pd.offsets.BusinessDay(rebalancing_period)
    )

    for i in range(1, len(ohlc_data)):
        row = ohlc_data.iloc[i]

        # Calculate the new portfolio value
        total_value = sum([row[ticker] * current_weights[ticker] for ticker in tickers])
        portfolio_value.append(total_value)

        # Rebalance the portfolio based on the rebalance_dates
        if row.name in rebalance_dates:
            for ticker in tickers:
                current_weights[ticker] = (
                    float(total_value) * float(portfolio_weights[ticker])
                ) / float(row[ticker])

    # Create a DataFrame with the portfolio value
    portfolio_value_df = pd.DataFrame(
        portfolio_value, index=ohlc_data.index, columns=["Portfolio Value"]
    )

    # Calculate stock1 returns and normalize it to start at 100
    stock1_returns = (1 + ohlc_data[stock1].pct_change()).cumprod()
    stock1_normalized = initial_value * stock1_returns

    # Calculate Stock1 stats
    stock1_normalized = stock1_normalized.iloc[
        1:
    ]  # Drop the first row to avoid division by zero

    # CAGR
    stock1_years = (stock1_normalized.index[-1] - stock1_normalized.index[0]).days / 365
    stock1_CAGR = (stock1_normalized.iloc[-1] / stock1_normalized.iloc[0]) ** (
        1 / stock1_years
    ) - 1

    # Max Drawdown
    stock1_normalized_df = pd.DataFrame(stock1_normalized)
    stock1_normalized_df["max"] = stock1_normalized_df[stock1].cummax()
    stock1_normalized_df["drawdown"] = (
        stock1_normalized_df[stock1] - stock1_normalized_df["max"]
    ) / stock1_normalized_df["max"]
    stock1_max_drawdown = stock1_normalized_df["drawdown"].min()

    # Volatility (annualized)
    stock1_normalized_df["daily_return"] = stock1_normalized_df[stock1].pct_change()
    stock1_volatility = stock1_normalized_df["daily_return"].std() * np.sqrt(252)

    # normalized price change of stock1 as a column in the portfolio_value_df
    stock1_normalized_df["stock1_normalized"] = stock1_normalized_df[stock1]

    # Sharpe Ratio (assuming risk-free rate of 0)
    stock1_sharpe_ratio = (stock1_CAGR - 0) / stock1_volatility

    # Calculate total return for stock1
    initial_stock1_value = stock1_normalized.iloc[0]
    ending_stock1_value = stock1_normalized.iloc[-1]
    stock1_total_return = (ending_stock1_value / initial_stock1_value) - 1

    # Calculate stats for the portfolio

    # Calculate total return for the portfolio
    initial_portfolio_value = portfolio_value_df.iloc[0, 0]
    ending_portfolio_value = portfolio_value_df.iloc[-1, 0]
    total_return = (ending_portfolio_value / initial_portfolio_value) - 1
    # CAGR
    years = (portfolio_value_df.index[-1] - portfolio_value_df.index[0]).days / 365
    CAGR = (portfolio_value_df.iloc[-1] / portfolio_value_df.iloc[0]) ** (1 / years) - 1

    # Max Drawdown
    portfolio_value_df["max"] = portfolio_value_df["Portfolio Value"].cummax()
    portfolio_value_df["drawdown"] = (
        portfolio_value_df["Portfolio Value"] - portfolio_value_df["max"]
    ) / portfolio_value_df["max"]
    max_drawdown = portfolio_value_df["drawdown"].min()

    # Volatility (annualized)
    portfolio_value_df["daily_return"] = portfolio_value_df[
        "Portfolio Value"
    ].pct_change()
    volatility = portfolio_value_df["daily_return"].std() * np.sqrt(252)

    # Sharpe Ratio (assuming risk-free rate of 0)
    sharpe_ratio = (CAGR - 0) / volatility

    data = {
        "Total Return": [stock1_total_return, total_return],
        "CAGR": [stock1_CAGR, CAGR[0]],
        "Max Drawdown": [stock1_max_drawdown, max_drawdown],
        "Volatility": [stock1_volatility, volatility],
        "Sharpe Ratio": [stock1_sharpe_ratio, sharpe_ratio.values[0]],
    }

    index = ["Stock", "Strategy"]
    return_data_df = pd.DataFrame(data, index=index)

    formats = {
        "Total Return": "{:.0f}x",
        "CAGR": "{:.0%}",
        "Max Drawdown": "{:.0%}",
        "Volatility": "{:.0%}",
        "Sharpe Ratio": "{:.0f}%",
    }

    # apply the formats to the DataFrame
    styled_return_data_df = return_data_df.style.format(formats)

    # display the styled DataFrame
    styled_return_data_df

    portfolio_value_df["stock1"] = stock1_normalized_df["stock1_normalized"]

    # Save portfolio_value_df as a CSV string
    portfolio_value_csv = portfolio_value_df.to_csv()

    # Export stock1_normalized to a CSV file named 'stock1_normalized.csv'
    stock1_normalized_df.to_csv("stock1_normalized.csv")

    # print(return_data_df)

    portfolio_value_df.index = portfolio_value_df.index.strftime("%Y-%m-%d")
    portfolio_value_df.reset_index(inplace=True)
    portfolio_value_df.rename(columns={"index": "Date"}, inplace=True)

    return portfolio_value_df.to_json(orient="split", index=False), return_data_df
