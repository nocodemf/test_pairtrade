from ib_insync import *
import numpy as np
import logging
import time

# Logging configuration
logging.basicConfig(
    filename='pair_trading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Connect to Interactive Brokers (Paper Trading)
ib = IB()
try:
    ib.connect('127.0.0.1', 7497, clientId=1)  # Use the appropriate port for paper trading
    logging.info("Connected to IB")
except Exception as e:
    logging.error(f"Connection failed: {e}")
    raise

# Define pair of stocks
stock1 = Stock('MSFT', 'SMART', 'USD')
stock2 = Stock('AAPL', 'SMART', 'USD')

# Qualify contracts
try:
    ib.qualifyContracts(stock1, stock2)
except Exception as e:
    logging.error(f"Contract qualification failed: {e}")
    raise

# Parameters
lookback_period = 20  # Number of days for spread mean calculation
zscore_threshold = 2  # Z-score threshold for trade signal
capital_allocation = 10000  # Amount to allocate per stock

# Fetch historical data
def fetch_data(contract, days):
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=f'{days} D',
        barSizeSetting='1 day',
        whatToShow='MIDPOINT',
        useRTH=True
    )
    return [bar.close for bar in bars]

# Calculate Z-score
def calculate_zscore(spread):
    mean = np.mean(spread)
    std = np.std(spread)
    return (spread[-1] - mean) / std if std > 0 else 0

# Main trading logic
def pair_trading():
    try:
        # Fetch historical prices
        prices1 = fetch_data(stock1, lookback_period + 1)
        prices2 = fetch_data(stock2, lookback_period + 1)

        if len(prices1) < lookback_period or len(prices2) < lookback_period:
            logging.warning("Not enough data to calculate spread")
            return

        # Calculate spread
        spread = np.array(prices1) - np.array(prices2)
        zscore = calculate_zscore(spread)

        logging.info(f"Spread: {spread[-1]}, Z-score: {zscore}")

        # Trading signals
        if zscore > zscore_threshold:
            # Short stock1, long stock2
            qty1 = int(capital_allocation / prices1[-1])
            qty2 = int(capital_allocation / prices2[-1])
            place_order('SELL', stock1, qty1)
            place_order('BUY', stock2, qty2)
            logging.info(f"Short {stock1.symbol}, long {stock2.symbol}")

        elif zscore < -zscore_threshold:
            # Long stock1, short stock2
            qty1 = int(capital_allocation / prices1[-1])
            qty2 = int(capital_allocation / prices2[-1])
            place_order('BUY', stock1, qty1)
            place_order('SELL', stock2, qty2)
            logging.info(f"Long {stock1.symbol}, short {stock2.symbol}")

        else:
            logging.info("No trading signal")
    except Exception as e:
        logging.error(f"Error in pair trading logic: {e}")

# Place market orders
def place_order(action, contract, quantity):
    order = MarketOrder(action, quantity)
    trade = ib.placeOrder(contract, order)
    logging.info(f"Placed {action} order for {contract.symbol} with quantity {quantity}")
    return trade

# Run the strategy
try:
    while True:
        pair_trading()
        time.sleep(60 * 5)  # Run every 5 minutes
except KeyboardInterrupt:
    print("Stopping pair trading bot.")
finally:
    ib.disconnect()
    logging.info("Disconnected from IB")
