"""
Portfolio Risk Analytics Engine.

Calculates theoretical portfolio value and aggregate analytical
Greeks for portfolios of European call and put options.

The engine reuses the existing vectorized Black-Scholes-Merton
implementation rather than duplicating option-pricing formulas.

Supported features:
- Long and short option positions.
- European calls and puts.
- Configurable contract multipliers.
- Vectorized portfolio valuation.
- Position-level theoretical values.
- Position-level Greek contributions.
- Aggregate portfolio Greeks.
- Input validation.
- Expired and zero-volatility contracts.
- Explicit handling of undefined analytical Greeks.

This first implementation supports portfolios containing options
on one underlying asset.

All position prices and Greeks use the conventions of the
existing vectorized Black-Scholes-Merton engine.
"""

import math
from dataclasses import dataclass

import numpy as np

from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
)

# ============================================================
# SUPPORTED OPTION TYPES
# ============================================================

# The portfolio engine currently supports European calls
# and European puts.
VALID_OPTION_TYPES = {"call", "put"}


# ============================================================
# PORTFOLIO POSITION MODEL
# ============================================================

@dataclass(frozen=True)
class OptionPosition:
    """
    Represent one European option position.

    Parameters
    ----------
    option_type : str
        Either "call" or "put".

    quantity : int
        Signed number of option contracts.

        Positive = long position.
        Negative = short position.

    S : float
        Current underlying asset price.

    K : float
        Option strike price.

    T : float
        Time to expiration in years.

    r : float
        Annual continuously compounded risk-free interest rate.

    sigma : float
        Annualized volatility.

    q : float
        Continuous dividend yield.

    multiplier : int
        Number of underlying units represented by one contract.

        Defaults to 100 for standard U.S. equity options.

    Notes
    -----
    This is a frozen dataclass.

    Frozen means the position's fields cannot be reassigned
    after the object has been created.

    This helps prevent accidental changes to positions
    during portfolio calculations.
    """

    option_type: str
    quantity: int

    S: float
    K: float
    T: float
    r: float
    sigma: float

    q: float = 0.0
    multiplier: int = 100

    def __post_init__(self):
        """
        Validate the position immediately after creation.

        The dataclass automatically generates __init__.

        Python calls __post_init__ after the fields have
        been assigned.
        """

        # ====================================================
        # VALIDATE OPTION TYPE
        # ====================================================

        if (
            not isinstance(self.option_type, str)
            or self.option_type not in VALID_OPTION_TYPES
        ):
            raise ValueError(
                "option_type must be 'call' or 'put'."
            )

        # ====================================================
        # VALIDATE QUANTITY
        # ====================================================

        # bool is a subclass of int in Python.
        #
        # Therefore, explicitly reject True and False
        # before checking whether quantity is an integer.
        if (
            isinstance(self.quantity, bool)
            or not isinstance(self.quantity, int)
        ):
            raise ValueError(
                "quantity must be an integer."
            )

        # A quantity of zero does not represent an
        # active position.
        if self.quantity == 0:
            raise ValueError(
                "quantity cannot be zero."
            )

        # ====================================================
        # VALIDATE CONTRACT MULTIPLIER
        # ====================================================

        if (
            isinstance(self.multiplier, bool)
            or not isinstance(self.multiplier, int)
        ):
            raise ValueError(
                "multiplier must be an integer."
            )

        if self.multiplier <= 0:
            raise ValueError(
                "multiplier must be greater than zero."
            )

        # ====================================================
        # VALIDATE FINANCIAL PARAMETERS
        # ====================================================

        parameters = {
            "S": self.S,
            "K": self.K,
            "T": self.T,
            "r": self.r,
            "sigma": self.sigma,
            "q": self.q,
        }

        # Every financial parameter must be a finite
        # real number.
        #
        # Reject booleans because Python treats them
        # as numeric values.
        for name, value in parameters.items():

            if isinstance(value, (bool, np.bool_)):
                raise ValueError(
                    f"{name} must be a finite number."
                )

            try:
                numeric_value = float(value)

            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(
                    f"{name} must be a finite number."
                ) from exc

            if not math.isfinite(numeric_value):
                raise ValueError(
                    f"{name} must be a finite number."
                )

        # Stock prices must be positive.
        if self.S <= 0:
            raise ValueError(
                "S must be greater than zero."
            )

        # Strike prices must be positive.
        if self.K <= 0:
            raise ValueError(
                "K must be greater than zero."
            )

        # Time to expiration cannot be negative.
        if self.T < 0:
            raise ValueError(
                "T cannot be negative."
            )

        # Volatility cannot be negative.
        if self.sigma < 0:
            raise ValueError(
                "sigma cannot be negative."
            )


# ============================================================
# PORTFOLIO ANALYTICS ENGINE
# ============================================================

class PortfolioAnalytics:
    """
    Calculate theoretical values and risk for option portfolios.

    The engine processes every position through the existing
    vectorized Black-Scholes-Merton Greeks function.

    Parameters
    ----------
    positions : list[OptionPosition]
        List of European option positions.

    Returns
    -------
    PortfolioAnalytics
        An object capable of calculating portfolio analytics.
    """

    def __init__(self, positions):
        """
        Initialize the portfolio analytics engine.
        """

        # Convert the supplied positions into a list.
        #
        # This allows callers to provide a tuple or
        # another iterable containing OptionPosition objects.
        try:
            self.positions = list(positions)

        except TypeError as exc:
            raise ValueError(
                "positions must be an iterable."
            ) from exc

        # Require at least one position.
        if not self.positions:
            raise ValueError(
                "Portfolio must contain at least one position."
            )

        # Verify that every item is an OptionPosition.
        for position in self.positions:

            if not isinstance(position, OptionPosition):
                raise ValueError(
                    "Every portfolio item must be an "
                    "OptionPosition."
                )

        # ====================================================
        # SINGLE-UNDERLYING VALIDATION
        # ====================================================

        # This first version models positions on one
        # underlying asset.
        #
        # Therefore, every position must use the same
        # current underlying price.
        #
        # Future versions can introduce an explicit
        # underlying symbol for multi-asset portfolios.
        first_stock_price = self.positions[0].S

        for position in self.positions[1:]:

            if position.S != first_stock_price:
                raise ValueError(
                    "All positions must use the same "
                    "underlying price S."
                )

    # ========================================================
    # CALCULATE PORTFOLIO ANALYTICS
    # ========================================================

    def calculate(self):
        """
        Calculate portfolio values and aggregate Greeks.

        Returns
        -------
        dict
            Dictionary containing:

            position_count
            total_contracts
            net_contracts
            portfolio_value
            portfolio_delta
            portfolio_gamma
            portfolio_vega
            portfolio_theta
            portfolio_rho
            positions

        Notes
        -----
        Position values and Greeks account for signed
        quantities and contract multipliers.

        Undefined analytical Greeks are returned as None.

        Portfolio Greek totals are also None when any
        contributing position has an undefined Greek.
        """

        # ====================================================
        # EXTRACT PORTFOLIO INPUTS
        # ====================================================

        # Convert each financial parameter into a NumPy array.
        #
        # Each array contains one value per position.
        S = np.asarray(
            [position.S for position in self.positions],
            dtype=float,
        )

        K = np.asarray(
            [position.K for position in self.positions],
            dtype=float,
        )

        T = np.asarray(
            [position.T for position in self.positions],
            dtype=float,
        )

        r = np.asarray(
            [position.r for position in self.positions],
            dtype=float,
        )

        sigma = np.asarray(
            [position.sigma for position in self.positions],
            dtype=float,
        )

        q = np.asarray(
            [position.q for position in self.positions],
            dtype=float,
        )

        # Signed contract quantities.
        quantities = np.asarray(
            [position.quantity for position in self.positions],
            dtype=float,
        )

        # Contract multipliers.
        multipliers = np.asarray(
            [position.multiplier for position in self.positions],
            dtype=float,
        )

        # ====================================================
        # CALCULATE POSITION EXPOSURE
        # ====================================================

        # Exposure represents the signed number of
        # underlying units controlled by each position.
        #
        # Example:
        #
        # 10 long contracts * 100 multiplier = +1000
        #
        # 5 short contracts * 100 multiplier = -500
        exposures = quantities * multipliers

        # ====================================================
        # RUN VECTORIZED BLACK-SCHOLES
        # ====================================================

        # Calculate all option prices and Greeks in
        # one vectorized operation.
        #
        # This avoids creating individual BlackScholes
        # objects for every position.
        results = greeks_options_vectorized(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            q=q,
        )

        # ====================================================
        # SELECT CALL OR PUT RESULTS
        # ====================================================

        # Create a boolean mask identifying call positions.
        is_call = np.asarray(
            [
                position.option_type == "call"
                for position in self.positions
            ],
            dtype=bool,
        )

        # np.where selects call values where the condition
        # is True and put values where it is False.
        prices = np.where(
            is_call,
            results["call_price"],
            results["put_price"],
        )

        deltas = np.where(
            is_call,
            results["call_delta"],
            results["put_delta"],
        )

        # Gamma and vega are the same for European
        # calls and puts under Black-Scholes-Merton.
        gammas = results["gamma"]
        vegas = results["vega"]

        thetas = np.where(
            is_call,
            results["call_theta"],
            results["put_theta"],
        )

        rhos = np.where(
            is_call,
            results["call_rho"],
            results["put_rho"],
        )

        # ====================================================
        # CALCULATE POSITION-LEVEL VALUES AND GREEKS
        # ====================================================

        # Multiply each theoretical option price
        # by its signed exposure.
        #
        # A short option position produces a
        # negative position value.
        position_values = prices * exposures

        # Apply the same signed exposure to each Greek.
        position_deltas = deltas * exposures
        position_gammas = gammas * exposures
        position_vegas = vegas * exposures
        position_thetas = thetas * exposures
        position_rhos = rhos * exposures

        # ====================================================
        # BUILD POSITION BREAKDOWN
        # ====================================================

        position_results = []

        # Convert a NumPy value into a standard Python float.
        #
        # Undefined values become None so they can be
        # serialized as JSON null in a future API endpoint.
        def optional_float(value):

            if np.isnan(value):
                return None

            return float(value)

        for index, position in enumerate(self.positions):

            position_results.append(
                {
                    "position_index": index,
                    "option_type": position.option_type,
                    "quantity": position.quantity,
                    "multiplier": position.multiplier,
                    "S": float(position.S),
                    "K": float(position.K),
                    "T": float(position.T),
                    "r": float(position.r),
                    "sigma": float(position.sigma),
                    "q": float(position.q),
                    "option_price": float(prices[index]),
                    "position_value": float(
                        position_values[index]
                    ),
                    "delta": optional_float(
                        position_deltas[index]
                    ),
                    "gamma": optional_float(
                        position_gammas[index]
                    ),
                    "vega": optional_float(
                        position_vegas[index]
                    ),
                    "theta": optional_float(
                        position_thetas[index]
                    ),
                    "rho": optional_float(
                        position_rhos[index]
                    ),
                }
            )

        # ====================================================
        # CALCULATE AGGREGATE PORTFOLIO GREEKS
        # ====================================================

        # If any position has an undefined Greek,
        # the aggregate Greek is also undefined.
        #
        # This prevents silently treating missing
        # sensitivities as zero.
        def aggregate_greek(values):

            if np.any(np.isnan(values)):
                return None

            return float(np.sum(values))

        # Calculate the signed total theoretical value.
        portfolio_value = float(
            np.sum(position_values)
        )

        # Aggregate risk sensitivities.
        portfolio_delta = aggregate_greek(
            position_deltas
        )

        portfolio_gamma = aggregate_greek(
            position_gammas
        )

        portfolio_vega = aggregate_greek(
            position_vegas
        )

        portfolio_theta = aggregate_greek(
            position_thetas
        )

        portfolio_rho = aggregate_greek(
            position_rhos
        )

        # ====================================================
        # PORTFOLIO CONTRACT STATISTICS
        # ====================================================

        # Gross number of contracts, ignoring long/short sign.
        total_contracts = sum(
            abs(position.quantity)
            for position in self.positions
        )

        # Net signed number of contracts.
        net_contracts = sum(
            position.quantity
            for position in self.positions
        )

        # ====================================================
        # RETURN COMPLETE PORTFOLIO REPORT
        # ====================================================

        return {
            "position_count": len(self.positions),
            "total_contracts": total_contracts,
            "net_contracts": net_contracts,
            "portfolio_value": portfolio_value,
            "portfolio_delta": portfolio_delta,
            "portfolio_gamma": portfolio_gamma,
            "portfolio_vega": portfolio_vega,
            "portfolio_theta": portfolio_theta,
            "portfolio_rho": portfolio_rho,
            "positions": position_results,
        }