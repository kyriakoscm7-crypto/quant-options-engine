"""
Vectorized Black-Scholes-Merton Pricing Engine.

Calculates European call and put prices for entire arrays
of options using NumPy and SciPy.

Unlike the original BlackScholes class, this implementation
avoids constructing a separate Python object for each option.

Supports:
- Multiple strike prices
- Multiple expiration times
- Multiple volatility values
- Risk-free interest rates
- Continuous dividend yields
- Expired options
- Zero-volatility options
"""

import numpy as np
from scipy.stats import norm


def price_options_vectorized(
    S,
    K,
    T,
    r,
    sigma,
    q=0.0,
):
    """
    Calculate European call and put prices using vectorization.

    Parameters
    ----------
    S : float or array-like
        Underlying stock prices.

    K : float or array-like
        Strike prices.

    T : float or array-like
        Time to expiration in years.

    r : float or array-like
        Annual risk-free interest rates.

    sigma : float or array-like
        Annualized volatility.

    q : float or array-like
        Annual dividend yields.

    Returns
    -------
    tuple
        (call_prices, put_prices), as NumPy arrays.

    Notes
    -----
    Inputs follow NumPy broadcasting rules.

    For example, one stock price can be combined with
    thousands of strike prices.
    """

    # Convert inputs into NumPy floating-point arrays.
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    r = np.asarray(r, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    q = np.asarray(q, dtype=float)

    # Broadcast inputs to a common shape.
    S, K, T, r, sigma, q = np.broadcast_arrays(
        S, K, T, r, sigma, q
    )

    # Reject NaN and infinity.
    for parameter in (S, K, T, r, sigma, q):
        if not np.all(np.isfinite(parameter)):
            raise ValueError(
                "All parameters must be finite numbers."
            )

    # Validate financial inputs.
    if np.any(S <= 0):
        raise ValueError(
            "Stock price must be greater than zero."
        )

    if np.any(K <= 0):
        raise ValueError(
            "Strike price must be greater than zero."
        )

    if np.any(T < 0):
        raise ValueError(
            "Time to expiration cannot be negative."
        )

    if np.any(sigma < 0):
        raise ValueError(
            "Volatility cannot be negative."
        )

    # Create arrays for the output prices.
    calls = np.zeros(S.shape, dtype=float)
    puts = np.zeros(S.shape, dtype=float)

    # Identify options that have already reached expiration.
    expired = T == 0

    # At expiration, options are worth their intrinsic value.
    calls[expired] = np.maximum(
        S[expired] - K[expired], 0.0
    )

    puts[expired] = np.maximum(
        K[expired] - S[expired], 0.0
    )

    # Identify options with zero volatility but positive time.
    zero_volatility = (sigma == 0) & (T > 0)

    # With zero volatility, the terminal stock price
    # is deterministic under the model.
    if np.any(zero_volatility):

        discounted_stock = (
            S[zero_volatility]
            * np.exp(
                -q[zero_volatility] * T[zero_volatility]
            )
        )

        discounted_strike = (
            K[zero_volatility]
            * np.exp(
                -r[zero_volatility] * T[zero_volatility]
            )
        )

        calls[zero_volatility] = np.maximum(
            discounted_stock - discounted_strike,
            0.0,
        )

        puts[zero_volatility] = np.maximum(
            discounted_strike - discounted_stock,
            0.0,
        )

    # Standard Black-Scholes applies when both
    # time and volatility are positive.
    standard = (T > 0) & (sigma > 0)

    if np.any(standard):

        stock = S[standard]
        strike = K[standard]
        time = T[standard]
        rate = r[standard]
        volatility = sigma[standard]
        dividend = q[standard]

        sqrt_time = np.sqrt(time)

        d1 = (
            np.log(stock / strike)
            + (
                rate
                - dividend
                + 0.5 * volatility**2
            ) * time
        ) / (volatility * sqrt_time)

        d2 = d1 - volatility * sqrt_time

        discounted_stock = (
            stock * np.exp(-dividend * time)
        )

        discounted_strike = (
            strike * np.exp(-rate * time)
        )

        calls[standard] = (
            discounted_stock * norm.cdf(d1)
            - discounted_strike * norm.cdf(d2)
        )

        puts[standard] = (
            discounted_strike * norm.cdf(-d2)
            - discounted_stock * norm.cdf(-d1)
        )

    return calls, puts