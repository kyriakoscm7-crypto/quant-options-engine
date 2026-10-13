"""
Portfolio Scenario Analysis Engine.

Reprices an options portfolio under hypothetical market conditions
to estimate changes in theoretical portfolio value.

The engine supports:
- Multiple market scenarios.
- Percentage changes in the underlying stock price.
- Absolute changes in annualized volatility.
- Calendar-day time advancement.
- European calls and puts.
- Long and short positions.
- Configurable contract multipliers.
- Position-level scenario profit and loss.
- Aggregate portfolio scenario profit and loss.
- Vectorized pricing across scenarios and positions.
- Expired and zero-volatility options.
- Strict scenario input validation.

All calculations reuse the existing vectorized
Black-Scholes-Merton pricing engine.

IMPORTANT
---------
Scenario P&L represents the change in theoretical portfolio
value relative to the current model valuation.

It does not represent realized trading profit, actual
execution prices, or a forecast of future market prices.

This version assumes:
- One underlying asset.
- A common percentage price shock across all positions.
- A common absolute volatility shock across all positions.
- Constant risk-free rates and dividend yields.
- European exercise.
"""

import math
from dataclasses import dataclass

import numpy as np

from app.pricing.portfolio import PortfolioAnalytics
from app.pricing.vectorized_black_scholes import (
    price_options_vectorized,
)

# ============================================================
# SCENARIO MODEL
# ============================================================


@dataclass(frozen=True)
class MarketScenario:
    """
    Represent one hypothetical market scenario.

    Parameters
    ----------
    name : str
        Descriptive name identifying the scenario.

    price_change_pct : float
        Percentage change in the underlying asset price.

        Examples:
            -5.0 = underlying decreases by 5%.
             2.0 = underlying increases by 2%.
             0.0 = underlying price remains unchanged.

        This value is expressed in percentage units,
        not decimal returns.

    volatility_change : float
        Absolute change in annualized volatility.

        Examples:
            0.05 = volatility increases by 5 percentage points.
           -0.03 = volatility decreases by 3 percentage points.
            0.00 = volatility remains unchanged.

        If original volatility is 0.20, adding 0.05
        produces a scenario volatility of 0.25.

    days_forward : float
        Number of calendar days to advance.

        Time to expiration decreases by days_forward / 365.

        Options that reach expiration have T = 0.

    Notes
    -----
    Negative volatility after applying the shock is not allowed.

    A stock-price shock of -100% or less is not allowed,
    because the Black-Scholes engine requires S > 0.
    """

    name: str
    price_change_pct: float = 0.0
    volatility_change: float = 0.0
    days_forward: float = 0.0

    def __post_init__(self):
        """
        Validate scenario parameters immediately after creation.
        """

        # ====================================================
        # VALIDATE SCENARIO NAME
        # ====================================================

        # Require a meaningful scenario name.
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "Scenario name must be a non-empty string."
            )

        # ====================================================
        # VALIDATE NUMERIC PARAMETERS
        # ====================================================

        parameters = {
            "price_change_pct": self.price_change_pct,
            "volatility_change": self.volatility_change,
            "days_forward": self.days_forward,
        }

        for parameter_name, value in parameters.items():

            # Reject boolean values explicitly.
            #
            # In Python, bool is a subclass of int,
            # so True and False would otherwise be
            # accepted as numerical values.
            if isinstance(value, (bool, np.bool_)):
                raise ValueError(
                    f"{parameter_name} must be a finite number."
                )

            try:
                numeric_value = float(value)

            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(
                    f"{parameter_name} must be a finite number."
                ) from exc

            # Reject NaN and positive/negative infinity.
            if not math.isfinite(numeric_value):
                raise ValueError(
                    f"{parameter_name} must be a finite number."
                )

        # ====================================================
        # VALIDATE PRICE CHANGE
        # ====================================================

        # A -100% shock would produce a stock price of zero.
        #
        # Black-Scholes requires a strictly positive
        # underlying price.
        if self.price_change_pct <= -100:
            raise ValueError(
                "price_change_pct must be greater than -100."
            )

        # ====================================================
        # VALIDATE TIME ADVANCEMENT
        # ====================================================

        # Scenario analysis models time moving forward.
        #
        # Negative values would imply traveling backward
        # in time, which is not supported.
        if self.days_forward < 0:
            raise ValueError(
                "days_forward cannot be negative."
            )


# ============================================================
# PORTFOLIO SCENARIO ANALYTICS ENGINE
# ============================================================


class PortfolioScenarioAnalysis:
    """
    Calculate theoretical portfolio P&L under market scenarios.

    Parameters
    ----------
    portfolio : PortfolioAnalytics
        Existing validated portfolio analytics object.

    scenarios : iterable[MarketScenario]
        Collection of hypothetical market scenarios.

    Notes
    -----
    This class does not modify the original portfolio
    or its underlying positions.

    All scenario prices are calculated using the existing
    vectorized Black-Scholes-Merton pricing function.
    """

    def __init__(self, portfolio, scenarios):
        """
        Initialize the portfolio scenario analysis engine.
        """

        # ====================================================
        # VALIDATE PORTFOLIO
        # ====================================================

        # Require the existing PortfolioAnalytics class.
        #
        # This ensures the input portfolio has already
        # passed position-level validation.
        if not isinstance(portfolio, PortfolioAnalytics):
            raise ValueError(
                "portfolio must be a PortfolioAnalytics instance."
            )

        self.portfolio = portfolio

        # ====================================================
        # VALIDATE SCENARIO COLLECTION
        # ====================================================

        # Convert scenarios into a list so they can
        # be processed repeatedly.
        try:
            self.scenarios = list(scenarios)

        except TypeError as exc:
            raise ValueError(
                "scenarios must be an iterable."
            ) from exc

        # At least one scenario is required.
        if not self.scenarios:
            raise ValueError(
                "At least one market scenario is required."
            )

        # Verify every item is a MarketScenario.
        for scenario in self.scenarios:

            if not isinstance(scenario, MarketScenario):
                raise ValueError(
                    "Every scenario must be a MarketScenario."
                )

        # ====================================================
        # VALIDATE SCENARIO NAMES
        # ====================================================

        # Unique names make it easier to identify
        # scenario results in future API responses.
        scenario_names = [
            scenario.name
            for scenario in self.scenarios
        ]

        if len(scenario_names) != len(set(scenario_names)):
            raise ValueError(
                "Scenario names must be unique."
            )

    # ========================================================
    # CALCULATE SCENARIO RESULTS
    # ========================================================

    def calculate(self):
        """
        Calculate theoretical portfolio values under all scenarios.

        Returns
        -------
        dict
            Dictionary containing:

            original_portfolio_value
            scenario_count
            position_count
            scenarios

        Each scenario includes:

            name
            price_change_pct
            volatility_change
            days_forward
            scenario_portfolio_value
            scenario_pnl
            scenario_return_pct
            positions

        Each position includes:

            position_index
            option_type
            quantity
            multiplier
            original_option_price
            scenario_option_price
            original_position_value
            scenario_position_value
            position_pnl

        Notes
        -----
        Scenario return percentage is calculated relative
        to the absolute original portfolio value.

        This is a normalized theoretical value change,
        not an investment return on capital.
        """

        # ====================================================
        # EXTRACT ORIGINAL PORTFOLIO POSITIONS
        # ====================================================

        positions = self.portfolio.positions

        position_count = len(positions)
        scenario_count = len(self.scenarios)

        # Extract each original position's model inputs.
        #
        # All arrays have one entry per position.
        S = np.asarray(
            [position.S for position in positions],
            dtype=float,
        )

        K = np.asarray(
            [position.K for position in positions],
            dtype=float,
        )

        T = np.asarray(
            [position.T for position in positions],
            dtype=float,
        )

        r = np.asarray(
            [position.r for position in positions],
            dtype=float,
        )

        sigma = np.asarray(
            [position.sigma for position in positions],
            dtype=float,
        )

        q = np.asarray(
            [position.q for position in positions],
            dtype=float,
        )

        # Signed quantities and contract multipliers.
        quantities = np.asarray(
            [position.quantity for position in positions],
            dtype=float,
        )

        multipliers = np.asarray(
            [position.multiplier for position in positions],
            dtype=float,
        )

        # Signed exposure for each position.
        #
        # Example:
        #
        # +10 contracts * 100 = +1000
        #  -5 contracts * 100 = -500
        exposures = quantities * multipliers

        # Identify call and put positions.
        is_call = np.asarray(
            [
                position.option_type == "call"
                for position in positions
            ],
            dtype=bool,
        )

        # ====================================================
        # CALCULATE ORIGINAL PORTFOLIO VALUE
        # ====================================================

        # Reprice the original positions using the
        # existing vectorized pricing function.
        original_calls, original_puts = price_options_vectorized(
            S=S,
            K=K,
            T=T,
            r=r,
            sigma=sigma,
            q=q,
        )

        # Select the appropriate call or put price.
        original_prices = np.where(
            is_call,
            original_calls,
            original_puts,
        )

        # Multiply by signed contract exposure.
        original_position_values = (
            original_prices * exposures
        )

        # Total original theoretical portfolio value.
        original_portfolio_value = float(
            np.sum(original_position_values)
        )

        # ====================================================
        # EXTRACT MARKET SCENARIO SHOCKS
        # ====================================================

        # Build one NumPy array per scenario parameter.
        #
        # Each array has shape:
        #
        # (number_of_scenarios,)
        price_changes = np.asarray(
            [
                scenario.price_change_pct
                for scenario in self.scenarios
            ],
            dtype=float,
        )

        volatility_changes = np.asarray(
            [
                scenario.volatility_change
                for scenario in self.scenarios
            ],
            dtype=float,
        )

        days_forward = np.asarray(
            [
                scenario.days_forward
                for scenario in self.scenarios
            ],
            dtype=float,
        )

        # ====================================================
        # CREATE TWO-DIMENSIONAL INPUT ARRAYS
        # ====================================================

        # We want one row per scenario and one column
        # per portfolio position.
        #
        # Example:
        #
        # 3 scenarios and 4 positions:
        #
        #       Position 1  Position 2  Position 3  Position 4
        #
        # S1       ...         ...         ...         ...
        # S2       ...         ...         ...         ...
        # S3       ...         ...         ...         ...
        #
        # Final shape:
        #
        # (scenario_count, position_count)

        # [:, None] converts a one-dimensional scenario
        # array into a column vector.
        #
        # [None, :] converts a one-dimensional position
        # array into a row vector.
        #
        # NumPy broadcasts these together automatically.

        # Apply the same percentage price shock
        # to every position in each scenario.
        scenario_S = (
            S[None, :]
            * (
                1.0
                + price_changes[:, None] / 100.0
            )
        )

        # Apply absolute volatility changes.
        #
        # Example:
        #
        # Original volatility = 0.20
        # Scenario change     = 0.05
        # Scenario volatility = 0.25
        scenario_sigma = (
            sigma[None, :]
            + volatility_changes[:, None]
        )

        # Move expiration times forward.
        #
        # Time is expressed in years, so convert
        # calendar days into years using 365 days.
        #
        # np.maximum prevents negative time to
        # expiration after an option expires.
        scenario_T = np.maximum(
            T[None, :]
            - days_forward[:, None] / 365.0,
            0.0,
        )

        # ====================================================
        # VALIDATE SHOCKED MARKET PARAMETERS
        # ====================================================

        # Every shocked underlying price must be positive.
        if np.any(scenario_S <= 0):
            raise ValueError(
                "Scenario underlying prices must be "
                "greater than zero."
            )

        # Volatility cannot become negative.
        #
        # This validation happens here because a
        # volatility shock may be valid for one
        # position but invalid for another.
        if np.any(scenario_sigma < 0):
            raise ValueError(
                "Scenario volatility cannot be negative."
            )

        # Reject non-finite shocked values.
        #
        # Even finite original inputs can produce
        # overflow under extreme hypothetical shocks.
        for parameter in (
            scenario_S,
            scenario_sigma,
            scenario_T,
        ):
            if not np.all(np.isfinite(parameter)):
                raise ValueError(
                    "Scenario parameters must remain finite."
                )

        # ====================================================
        # REPRICE ALL SCENARIOS IN ONE VECTORIZED CALL
        # ====================================================

        # The vectorized pricing function accepts arrays
        # with multiple dimensions.
        #
        # NumPy broadcasts:
        #
        # scenario_S:     (scenario_count, position_count)
        # K:              (position_count,)
        # scenario_T:     (scenario_count, position_count)
        # r:              (position_count,)
        # scenario_sigma: (scenario_count, position_count)
        # q:              (position_count,)
        #
        # This calculates every scenario-position
        # combination without Python pricing loops.
        scenario_calls, scenario_puts = price_options_vectorized(
            S=scenario_S,
            K=K[None, :],
            T=scenario_T,
            r=r[None, :],
            sigma=scenario_sigma,
            q=q[None, :],
        )

        # Select call or put prices across every row.
        scenario_prices = np.where(
            is_call[None, :],
            scenario_calls,
            scenario_puts,
        )

        # Multiply each scenario price by the signed
        # position exposure.
        scenario_position_values = (
            scenario_prices * exposures[None, :]
        )

        # ====================================================
        # CALCULATE SCENARIO P&L
        # ====================================================

        # Calculate the change in theoretical value
        # for every position under every scenario.
        position_pnl = (
            scenario_position_values
            - original_position_values[None, :]
        )

        # Sum all position values across each scenario.
        scenario_portfolio_values = np.sum(
            scenario_position_values,
            axis=1,
        )

        # Sum position-level P&L for each scenario.
        #
        # This makes the aggregate P&L consistent
        # with the position breakdown.
        scenario_pnl = np.sum(
            position_pnl,
            axis=1,
        )

        # ====================================================
        # BUILD SCENARIO REPORT
        # ====================================================

        scenario_results = []

        for scenario_index, scenario in enumerate(
            self.scenarios
        ):

            # Build the individual position breakdown.
            position_results = []

            for position_index, position in enumerate(
                positions
            ):

                position_results.append(
                    {
                        "position_index": position_index,
                        "option_type": position.option_type,
                        "quantity": position.quantity,
                        "multiplier": position.multiplier,
                        "original_option_price": float(
                            original_prices[position_index]
                        ),
                        "scenario_option_price": float(
                            scenario_prices[
                                scenario_index,
                                position_index,
                            ]
                        ),
                        "original_position_value": float(
                            original_position_values[
                                position_index
                            ]
                        ),
                        "scenario_position_value": float(
                            scenario_position_values[
                                scenario_index,
                                position_index,
                            ]
                        ),
                        "position_pnl": float(
                            position_pnl[
                                scenario_index,
                                position_index,
                            ]
                        ),
                    }
                )

            # Scenario-level theoretical portfolio value.
            scenario_value = float(
                scenario_portfolio_values[scenario_index]
            )

            # Scenario-level theoretical profit or loss.
            pnl = float(
                scenario_pnl[scenario_index]
            )

            # =================================================
            # CALCULATE NORMALIZED SCENARIO RETURN
            # =================================================

            # Divide by the absolute starting portfolio value.
            #
            # This allows negative original portfolio values
            # to produce a consistently signed normalized
            # value change.
            #
            # This is NOT a return on invested capital.
            if original_portfolio_value != 0.0:

                scenario_return_pct = (
                    pnl
                    / abs(original_portfolio_value)
                    * 100.0
                )

            else:

                # A zero starting value makes the
                # percentage change undefined.
                scenario_return_pct = None

            # =================================================
            # STORE SCENARIO RESULT
            # =================================================

            scenario_results.append(
                {
                    "name": scenario.name,
                    "price_change_pct": float(
                        scenario.price_change_pct
                    ),
                    "volatility_change": float(
                        scenario.volatility_change
                    ),
                    "days_forward": float(
                        scenario.days_forward
                    ),
                    "scenario_portfolio_value": scenario_value,
                    "scenario_pnl": pnl,
                    "scenario_return_pct": scenario_return_pct,
                    "positions": position_results,
                }
            )

        # ====================================================
        # RETURN COMPLETE SCENARIO ANALYSIS
        # ====================================================

        return {
            "original_portfolio_value": original_portfolio_value,
            "scenario_count": scenario_count,
            "position_count": position_count,
            "scenarios": scenario_results,
        }