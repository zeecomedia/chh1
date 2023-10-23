import pandas as pd
import numpy as np


def generate_charts(
    ohlc_dict, ticker_signal, short, long, ind, ticker_strat, strat_returns, buys, sells
):
    try:
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
        strategy_df_2["Returns"] = (
            strategy_df_2["Returns_T"] * strategy_df_2["Position"]
        )
        strategy_df_2["cum_return"] = (1 + strategy_df_2["Returns"]).cumprod()

        """
        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(10, 10))
        ax[0].set_title('Crossover signal: {a} {b}/{c} {d} '.format(a=ticker_signal, b=short, c=long, d=ind))
        ax[1].set_title('Cumulative return')
        ax[0].grid()
        ax[1].grid()

        # Chart 1
        ax[0].plot(ohlc_dict[ticker_signal]['Adj Close'], color='black', label='Adj Close')
        ax[0].plot(ohlc_dict[ticker_signal]['Short {}'.format(ind)], color='blue', label='Short {}'.format(ind))
        ax[0].plot(ohlc_dict[ticker_signal]['Long {}'.format(ind)], color='g', label='Long {}'.format(ind))
        ax[0].plot_date(buys,
                        ohlc_dict[ticker_signal]['Short {}'.format(ind)][ohlc_dict[ticker_signal]['Position'] == 1], \
                        '^', markersize=5, color='g', label='buy')
        ax[0].plot_date(sells,
                        ohlc_dict[ticker_signal]['Short {}'.format(ind)][ohlc_dict[ticker_signal]['Position'] == -1], \
                        'v', markersize=5, color='r', label='sell')
        ax[0].legend()

        # Chart 2
        ax[1].plot(strategy_df["cum_return"], color="teal", label="Strategy w/ signal")
        ax[1].plot(strategy_df_2["cum_return"], color="black", label="Strategy w/o signal")
        ax[1].legend()
        ax[1].yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        """

        #print("buys and sells are ", buys, sells)

        # Convert ohlc_dict to pandas dataframe
        data_df = pd.DataFrame(ohlc_dict[ticker_signal])
        data_df["indexedstockreturn"] = strategy_df["cum_return"]
        data_df["normalised stock return"] = strategy_df_2["cum_return"]
        data_df.reset_index(level=0, inplace=True)

        # Convert 'Date' column back to datetime
        data_df["Date"] = pd.to_datetime(data_df["Date"], unit="ms")

        # Add 'buys' and 'sells' columns
        data_df["buys"] = data_df["Date"].apply(
            lambda x: 1 if x.strftime("%Y-%m-%d") in buys else None
        )
        data_df["sells"] = data_df["Date"].apply(
            lambda x: 1 if x.strftime("%Y-%m-%d") in sells else None
        )

        # Convert 'Date' column back to milliseconds
        data_df = data_df.reset_index().assign(
            Date=lambda x: (x["Date"] - pd.Timestamp("1970-01-01"))
            // pd.Timedelta("1ms")
        )

        data_df.replace({np.nan: None})

        # print('data_df =',data_df)
        # print('data_df[indexedstockreturn]',data_df['indexedstockreturn'])
        # print("Original buy dates:", buys)
        # print("Original sell dates:", sells)

        return data_df

    except Exception as e:
        import traceback

        print("Error generating chart in charts.py:", e)
        print(traceback.format_exc())
        return None
