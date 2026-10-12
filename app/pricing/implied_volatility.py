import math

from scipy.optimize import brentq

from app.pricing.black_scholes import BlackScholes


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    q: float = 0.0
) -> float:
    """
    Calculate implied volatility using Brent's root-finding method.

    Implied volatility is the volatility that makes the theoretical
    Black-Scholes-Merton price equal to the observed market price.

    Parameters
    ----------
    market_price : float
        Observed option market price.

    S : float
        Current underlying asset price.

    K : float
        Option strike price.

    T : float
        Time remaining until expiration in years.

    r : float
        Continuously compounded annual risk-free interest rate.

    option_type : str
        Either "call" or "put".

    q : float
        Continuously compounded annual dividend yield.

    Returns
    -------
    float
        Annualized implied volatility as a decimal.

        Returns math.nan when no valid solution exists within
        the configured volatility range.
    """

    # Validate the option type.
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'.")

    # Convert inputs into standard Python floats.
    market_price = float(market_price)
    S = float(S)
    K = float(K)
    T = float(T)
    r = float(r)
    q = float(q)

    # Reject invalid or non-finite inputs.
    parameters = (market_price, S, K, T, r, q)

    if not all(math.isfinite(value) for value in parameters):
        raise ValueError("All inputs must be finite numbers.")

    if market_price < 0:
        raise ValueError("Market price cannot be negative.")

    if S <= 0 or K <= 0:
        raise ValueError("Stock price and strike must be positive.")

    if T <= 0:
        raise ValueError("Time to expiration must be positive.")

    # Discount factors for dividends and interest rates.
    discounted_stock = S * math.exp(-q * T)
    discounted_strike = K * math.exp(-r * T)

    # Calculate theoretical no-arbitrage price bounds.
    if option_type == "call":

        lower_bound = max(
            discounted_stock - discounted_strike,
            0.0
        )

        upper_bound = discounted_stock

    else:

        lower_bound = max(
            discounted_strike - discounted_stock,
            0.0
        )

        upper_bound = discounted_strike

    # Market prices outside these bounds are inconsistent
    # with the European Black-Scholes-Merton assumptions.
    if not lower_bound <= market_price <= upper_bound:
        return math.nan

    # Objective function: theoretical price minus market price.
    # Brent's method searches for the volatility that makes
    # this difference equal to zero.
    def objective(sigma: float) -> float:

        engine = BlackScholes(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            q=q
        )

        if option_type == "call":
            theoretical_price = engine.call_price()
        else:
            theoretical_price = engine.put_price()

        return theoretical_price - market_price

    # Search for implied volatility between 0.0001% and 500%.
    minimum_volatility = 1e-6
    maximum_volatility = 5.0

    # Brent's method requires a root bracket.
    lower_error = objective(minimum_volatility)
    upper_error = objective(maximum_volatility)

    # If the market price matches a bracket endpoint,
    # return that volatility directly.
    if abs(lower_error) < 1e-12:
        return minimum_volatility

    if abs(upper_error) < 1e-12:
        return maximum_volatility

    # No sign change means no root was bracketed.
    if lower_error * upper_error > 0:
        return math.nan

    try:

        result = brentq(
            objective,
            minimum_volatility,
            maximum_volatility,
            xtol=1e-10,
            maxiter=200
        )

        return float(result)

    except ValueError:
        return math.nan


if __name__ == "__main__":

    # Example: Recover 20% volatility from a known option price.
    engine = BlackScholes(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20
    )

    market_price = engine.call_price()

    recovered_iv = implied_volatility(
        market_price=market_price,
        S=100,
        K=100,
        T=1,
        r=0.05,
        option_type="call"
    )

    print("--- Implied Volatility Test ---")
    print(f"Market Price: ${market_price:.4f}")
    print(f"Recovered IV: {recovered_iv * 100:.4f}%")