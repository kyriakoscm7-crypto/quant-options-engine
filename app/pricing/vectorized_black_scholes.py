"""
Vectorized Black-Scholes-Merton Pricing and Greeks Engine.

Calculates European call and put prices, along with analytical
risk sensitivities, for entire arrays of options.

Unlike the original BlackScholes class, this implementation
avoids constructing a separate Python object for each contract.

Supports:
- Multiple underlying stock prices
- Multiple strike prices
- Multiple expiration times
- Multiple volatility values
- Risk-free interest rates
- Continuous dividend yields
- Expired options
- Zero-volatility options
- Vectorized analytical Greeks

All calculations follow the conventions used by the original
BlackScholes class.
"""

import numpy as np
from scipy.stats import norm

# ============================================================
# VECTORIZED EUROPEAN OPTION PRICING
# ============================================================

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


# ============================================================
# VECTORIZED ANALYTICAL GREEKS
# ============================================================

def greeks_options_vectorized(
    S,
    K,
    T,
    r,
    sigma,
    q=0.0,
):
    """
    Calculate European option prices and Greeks using NumPy.

    This function calculates risk sensitivities for multiple
    option contracts simultaneously.

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
    dict
        Dictionary containing NumPy arrays for:

        call_price
        put_price
        call_delta
        put_delta
        gamma
        vega
        call_theta
        put_theta
        call_rho
        put_rho

    Conventions
    -----------
    Delta:
        Sensitivity to a $1 underlying price movement.

    Gamma:
        Change in delta per $1 underlying price movement.

    Vega:
        Sensitivity to a 1-percentage-point volatility change.

    Theta:
        Calendar-day time decay.

    Rho:
        Sensitivity to a 1-percentage-point interest-rate change.

    Notes
    -----
    All returned arrays follow NumPy broadcasting rules.

    Greeks are represented by NaN when T == 0 or sigma == 0.

    NaN is used internally because NumPy floating-point arrays
    cannot represent Python None directly without using object
    arrays.

    Applications can convert NaN into None when generating
    JSON responses.
    """

    # ========================================================
    # CONVERT AND BROADCAST INPUTS
    # ========================================================

    # Convert each input into a NumPy floating-point array.
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.asarray(T, dtype=float)
    r = np.asarray(r, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    q = np.asarray(q, dtype=float)

    # Ensure every parameter has a compatible shape.
    #
    # Example:
    # S = 100
    # K = [90, 100, 110]
    #
    # NumPy broadcasts S across all three strikes.
    S, K, T, r, sigma, q = np.broadcast_arrays(
        S, K, T, r, sigma, q
    )

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    # Reject NaN and infinite input parameters.
    for parameter in (S, K, T, r, sigma, q):

        if not np.all(np.isfinite(parameter)):

            raise ValueError(
                "All parameters must be finite numbers."
            )

    # Underlying prices must be positive.
    if np.any(S <= 0):

        raise ValueError(
            "Stock price must be greater than zero."
        )

    # Strike prices must be positive.
    if np.any(K <= 0):

        raise ValueError(
            "Strike price must be greater than zero."
        )

    # Time to expiration cannot be negative.
    if np.any(T < 0):

        raise ValueError(
            "Time to expiration cannot be negative."
        )

    # Volatility cannot be negative.
    if np.any(sigma < 0):

        raise ValueError(
            "Volatility cannot be negative."
        )

    # ========================================================
    # CALCULATE OPTION PRICES
    # ========================================================

    # Reuse the existing vectorized pricing function.
    #
    # This ensures the Greeks function produces the same
    # option prices as the original vectorized engine.
    calls, puts = price_options_vectorized(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q,
    )

    # ========================================================
    # INITIALIZE GREEK ARRAYS
    # ========================================================

    # Create one array for each Greek.
    #
    # Arrays initially contain NaN, representing undefined
    # Greeks for expired or zero-volatility contracts.
    #
    # NumPy's np.full creates an array of the requested shape
    # and fills every position with the specified value.
    greek_names = (
        "call_delta",
        "put_delta",
        "gamma",
        "vega",
        "call_theta",
        "put_theta",
        "call_rho",
        "put_rho",
    )

    greeks = {
        name: np.full(
            S.shape,
            np.nan,
            dtype=float,
        )
        for name in greek_names
    }

    # ========================================================
    # IDENTIFY VALID ANALYTICAL CASES
    # ========================================================

    # Standard analytical Greeks require:
    #
    # 1. Positive time to expiration.
    # 2. Positive volatility.
    #
    # Expired or zero-volatility contracts retain NaN.
    standard = (T > 0) & (sigma > 0)

    # Skip analytical calculations when no contracts
    # satisfy the standard Black-Scholes conditions.
    if np.any(standard):

        # Extract only valid contracts.
        stock = S[standard]
        strike = K[standard]
        time = T[standard]
        rate = r[standard]
        volatility = sigma[standard]
        dividend = q[standard]

        # ====================================================
        # CALCULATE d1 AND d2
        # ====================================================

        # Square root of time to expiration.
        sqrt_time = np.sqrt(time)

        # Standard Black-Scholes-Merton d1.
        d1 = (
            np.log(stock / strike)
            + (
                rate
                - dividend
                + 0.5 * volatility**2
            ) * time
        ) / (volatility * sqrt_time)

        # Standard Black-Scholes-Merton d2.
        d2 = d1 - volatility * sqrt_time

        # ====================================================
        # DISCOUNT FACTORS
        # ====================================================

        # Discount factor for continuous dividends.
        discount_q = np.exp(-dividend * time)

        # Discount factor for the risk-free rate.
        discount_r = np.exp(-rate * time)

        # Standard normal probability density at d1.
        pdf_d1 = norm.pdf(d1)

        # ====================================================
        # DELTA
        # ====================================================

        # Call delta:
        # e^(-qT) * N(d1)
        call_delta = discount_q * norm.cdf(d1)

        # Put delta:
        # e^(-qT) * (N(d1) - 1)
        put_delta = discount_q * (
            norm.cdf(d1) - 1.0
        )

        # ====================================================
        # GAMMA
        # ====================================================

        # Gamma is identical for European calls and puts.
        #
        # Gamma measures the rate of change of delta
        # relative to the underlying stock price.
        gamma = (
            discount_q
            * pdf_d1
            / (stock * volatility * sqrt_time)
        )

        # ====================================================
        # VEGA
        # ====================================================

        # Vega is identical for European calls and puts.
        #
        # Divide by 100 to match the scalar engine:
        # sensitivity to a 1-percentage-point volatility move.
        vega = (
            stock
            * discount_q
            * pdf_d1
            * sqrt_time
        ) / 100.0

        # ====================================================
        # THETA
        # ====================================================

        # Common component shared by call and put theta.
        common_theta = (
            -stock
            * discount_q
            * pdf_d1
            * volatility
            / (2.0 * sqrt_time)
        )

        # Call theta, converted to daily time decay.
        call_theta = (
            common_theta
            - rate
            * strike
            * discount_r
            * norm.cdf(d2)
            + dividend
            * stock
            * discount_q
            * norm.cdf(d1)
        ) / 365.0

        # Put theta, converted to daily time decay.
        put_theta = (
            common_theta
            + rate
            * strike
            * discount_r
            * norm.cdf(-d2)
            - dividend
            * stock
            * discount_q
            * norm.cdf(-d1)
        ) / 365.0

        # ====================================================
        # RHO
        # ====================================================

        # Call rho:
        # sensitivity to a 1-percentage-point rate move.
        call_rho = (
            strike
            * time
            * discount_r
            * norm.cdf(d2)
        ) / 100.0

        # Put rho:
        # sensitivity to a 1-percentage-point rate move.
        put_rho = (
            -strike
            * time
            * discount_r
            * norm.cdf(-d2)
        ) / 100.0

        # ====================================================
        # STORE RESULTS
        # ====================================================

        # Assign the calculated values only to valid
        # contracts using the boolean mask.
        #
        # Expired and zero-volatility contracts remain NaN.
        greeks["call_delta"][standard] = call_delta
        greeks["put_delta"][standard] = put_delta
        greeks["gamma"][standard] = gamma
        greeks["vega"][standard] = vega
        greeks["call_theta"][standard] = call_theta
        greeks["put_theta"][standard] = put_theta
        greeks["call_rho"][standard] = call_rho
        greeks["put_rho"][standard] = put_rho

    # ========================================================
    # RETURN COMPLETE RESULTS
    # ========================================================

    # Include option prices and all analytical Greeks.
    #
    # Prices remain valid even when analytical Greeks
    # are undefined.
    return {
        "call_price": calls,
        "put_price": puts,
        **greeks,
    }