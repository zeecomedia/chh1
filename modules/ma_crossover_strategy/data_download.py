import os
import pickle
import yfinance as yf
#bugfix for yfinance
#yf.cache_off()


# Define base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def download_ticker_data(tickers, start_date, end_date):
    # Determine the environment
    pickle_path = os.path.join(BASE_DIR, 'ohlc_data.pickle')

    ohlc_data = {}

    try:
        # Try to download data from the internet
        for ticker in tickers:
            ohlc_data[ticker] = yf.download(ticker, start_date, end_date)
            print("Data downloaded from yfinance for ticker: ", ticker)
        with open(pickle_path, "wb") as f:
            pickle.dump(ohlc_data, f)
            print("Pickle dump succeeded")
    except Exception as e:
        print("Failed to download data from internet: {}".format(str(e)))
        # Try to load data from the pickle file
        try:
            with open(pickle_path, "rb") as f:
                ohlc_data = pickle.load(f)
        except Exception as e:
            print("Failed to load data from pickle file: {}".format(str(e)))

    return ohlc_data
