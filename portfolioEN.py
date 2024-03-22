import os
import requests
import pandas as pd
import json
import plotly.graph_objs as go

# This code provides basic management of harmonization between different types of products (forex, stocks, commodities, crypto, index);
# regarding market closing and non-closing.
# No known issues between products with the same trading hours.

# Time reference
# hours = ['15min', '30min', '1h', '4h', '1day'] variant with for loop
hourly_interval = '1day'

period = 180

# Specify desired trading pairs as portfolio
portfolio = [
    # forex
    {'symbol': 'EUR/USD', 'quantity': 100, 'type': 'long'},
    {'symbol': '', 'quantity': 100, 'type': 'long'},
    # commodity
    {'symbol': '', 'quantity': 1, 'type': 'long'},
    # crypto
    {'symbol': 'BTC/USD', 'quantity': 1, 'type': 'long'},
    # index
    {'symbol': '', 'quantity': 1, 'type': 'short'},
    # stocks
    # {'symbol': '/', 'quantity': 1, 'type': 'long'},
    # {'symbol': '/', 'quantity': 1, 'type': 'long'},
]


# International market consultation
def buy_sell_portfolio(period, portfolio, hourly_interval):
    """
    Calculate the portfolio values and dates based on historical price data.

    Args:
        period (int): The number of historical data points to retrieve.
        portfolio (list): A list of dictionaries representing the portfolio.
            Each dictionary should contain the following keys:
            - 'symbol': The symbol of the instrument.
            - 'quantity': The quantity of the instrument.
            - 'type': The type of the instrument ('long' or 'short').
        hourly_interval (str): The time interval for retrieving historical data.

    Returns:
        tuple: A tuple containing two lists:
            - portfolio_values: A list of portfolio values over time.
            - portfolio_dates: A list of corresponding dates.
    """
    #export key=key
    # Load variable for API key
    sec_key = os.getenv('key')

    # Twelve Data API URL
    API_BASE_URL = 'https://api.twelvedata.com/time_series'
    # Historical price data for the portfolio
    portfolio_data = {}
    portfolio_values = []  # Portfolio values over time
    portfolio_dates = []  # Corresponding dates

    for instrument in portfolio:
        symbol = instrument['symbol']
        instrument_url = f'{API_BASE_URL}?apikey={sec_key}&interval={hourly_interval}&symbol={symbol}&outputsize={period}&timezone=Europe/Rome'

        # Call the API to get data
        response = requests.get(instrument_url)
        data = json.loads(response.text)
        portfolio_data[symbol] = data  # Save complete historical data in the portfolio_data dictionary

    # Find all available timestamps in the portfolio_data dictionary
    all_timestamps = set()
    for data in portfolio_data.values():
        timestamps = [value['datetime'] for value in data['values']]
        all_timestamps.update(timestamps)

    # Dictionary to keep track of the last known price for each symbol
    last_known_prices = {instrument['symbol']: None for instrument in portfolio}

    # Iterate over all timestamps
    for timestamp in all_timestamps:
        value = 0
        is_forex_open = True  # Indicates whether the forex market is open for this date

        for instrument in portfolio:
            symbol = instrument['symbol']
            quantity = instrument['quantity']
            type_ = instrument['type']
            data = portfolio_data[symbol]['values']

            # Initialize the data_datetime variable
            data_datetime = None

            # Find the closing price corresponding to the timestamp
            last_price = None

            for value_data in data:
                if value_data['datetime'] == timestamp:
                    last_price = float(value_data['close'])
                    data_datetime = value_data['datetime']
                    break

            # Check if the price is missing or negative
            if last_price is None or last_price <= 0:
                # Use the last known price for this symbol
                last_price = last_known_prices[symbol]
            else:
                # Update the last known price for this symbol only if the price is valid
                last_known_prices[symbol] = last_price

            # If the price is missing for the symbol or is negative, skip the calculation for this date
            if last_price is None or last_price <= 0:
                is_forex_open = False
                break

            # Convert the correct date to a datetime object
            date_object = pd.to_datetime(data_datetime)
            # Manage long and short positions
            if type_ == 'long':
                instrument_value = last_price * quantity
            elif type_ == 'short':
                instrument_value = -last_price * quantity

            value += instrument_value
        if is_forex_open:
            # Add portfolio values
            portfolio_values.append(value)
            portfolio_dates.append(date_object)

    return portfolio_values, portfolio_dates


def simple_portfolio_graph(portfolio_values, portfolio_dates):
    # Create DataFrame for data manipulation
    data_df = pd.DataFrame({'date': portfolio_dates, 'close': portfolio_values})
    # Sort the DataFrame by date in ascending order
    data_df = data_df.sort_values('date')
    # Plot portfolio value over time
    fig = go.Figure(data=go.Scatter(x=data_df['date'], y=data_df['close']))
    fig.update_layout(
        title="Portfolio Performance Over Time",
        xaxis_title="Time",
        yaxis_title="Portfolio Value"
    )
    fig.update_traces(
        hovertemplate='<b>Date:</b> %{x}<br><b>Portfolio Value:</b> $%{y:.2f}'
    )

    fig.show()


# Run
portfolio_values, portfolio_dates = buy_sell_portfolio(period, portfolio, hourly_interval)
simple_portfolio_graph(portfolio_values, portfolio_dates)
