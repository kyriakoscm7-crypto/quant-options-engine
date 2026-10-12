import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import brentq
from black_scholes import BlackScholes

def implied_volatility(market_price, S, K, T, r, option_type='call'):
    """
    Uses Brent's root-finding method to back out the Implied Volatility 
    from a real market option price.
    """
    def objective_function(sigma):
        if sigma <= 0:
            return -market_price
        bs = BlackScholes(S=S, K=K, T=T, r=r, sigma=sigma)
        price = bs.call_price() if option_type == 'call' else bs.put_price()
        return price - market_price

    try:
        # Search for volatility between 1% (0.01) and 500% (5.0)
        iv = brentq(objective_function, 0.01, 5.0, xtol=1e-6, maxiter=100)
        return iv
    except ValueError:
        # Return NaN if the option price violates no-arbitrage bounds
        return np.nan

def fetch_live_option_chain(ticker_symbol="SPY", risk_free_rate=0.045):
    """
    Fetches real-time option chains from Yahoo Finance and computes Implied Volatility.
    """
    print(f"Fetching live market data for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    # Get current stock price
    todays_data = ticker.history(period="1d")
    if todays_data.empty:
        print("Could not fetch stock data. Check your internet connection.")
        return None
    S = todays_data['Close'].iloc[-1]
    print(f"Current {ticker_symbol} Stock Price: ${S:.2f}")

    # Get expiration dates
    expirations = ticker.options
    if not expirations:
        print("No options data available.")
        return None
    
    # Pick the first available expiration date
    expiry_date = expirations[0]
    opt_chain = ticker.option_chain(expiry_date)
    calls = opt_chain.calls
    
    print(f"Analyzing Call options for expiry: {expiry_date}...")
    
    # Calculate time to expiration in years (assuming 365 days)
    # Note: In production, use exact datetime differences. Here we approximate for simplicity.
    T = 30.0 / 365.0 

    results = []
    for _, row in calls.iterrows():
        K = row['strike']
        market_price = (row['bid'] + row['ask']) / 2.0  # Mid price
        if market_price <= 0 or np.isnan(market_price):
            continue
            
        iv = implied_volatility(market_price, S, K, T, risk_free_rate, option_type='call')
        if not np.isnan(iv):
            results.append({
                "Strike": K,
                "MarketPrice": market_price,
                "ImpliedVolatility": round(iv * 100, 2) # Expressed as a percentage
            })
            
    df = pd.DataFrame(results)
    return df

if __name__ == "__main__":
    # Run the live data extraction and IV calculation for SPY
    iv_df = fetch_live_option_chain("SPY")
    if iv_df is not None and not iv_df.empty:
        print("\n--- Sample Implied Volatility Results (SPY) ---")
        print(iv_df.head(10).to_string(index=False))