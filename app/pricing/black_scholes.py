import math

from scipy.stats import norm


class BlackScholes:
    """
    Black-Scholes-Merton pricing engine for European options.

    Parameters
    ----------
    S : float
        Current underlying asset price.

    K : float
        Option strike price.

    T : float
        Time until expiration, expressed in years.

    r : float
        Continuously compounded annual risk-free interest rate.

    sigma : float
        Annualized volatility, expressed as a decimal.

    q : float
        Continuously compounded annual dividend yield.
        Defaults to zero.

    Notes
    -----
    Assumes constant volatility, interest rates, and dividend yield.

    Does not model early exercise, so it is not an American
    options pricing model.
    """

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0.0
    ):

        # Convert all inputs to standard Python floating-point numbers.
        self.S = float(S)
        self.K = float(K)
        self.T = float(T)
        self.r = float(r)
        self.sigma = float(sigma)
        self.q = float(q)

        # Reject non-finite values such as NaN and infinity.
        parameters = (
            self.S,
            self.K,
            self.T,
            self.r,
            self.sigma,
            self.q
        )

        if not all(math.isfinite(value) for value in parameters):
            raise ValueError("All parameters must be finite numbers.")

        # Stock prices and strike prices must be positive.
        if self.S <= 0:
            raise ValueError("Stock price must be greater than zero.")

        if self.K <= 0:
            raise ValueError("Strike price must be greater than zero.")

        # Time cannot be negative.
        if self.T < 0:
            raise ValueError("Time to expiration cannot be negative.")

        # Volatility cannot be negative.
        if self.sigma < 0:
            raise ValueError("Volatility cannot be negative.")

        # Calculate d1 and d2 only when their formulas are valid.
        if self.T > 0 and self.sigma > 0:

            sqrt_T = math.sqrt(self.T)

            self.d1 = (
                math.log(self.S / self.K)
                + (
                    self.r
                    - self.q
                    + 0.5 * self.sigma ** 2
                ) * self.T
            ) / (self.sigma * sqrt_T)

            self.d2 = self.d1 - self.sigma * sqrt_T

        else:
            self.d1 = None
            self.d2 = None

    def call_price(self) -> float:
        """Calculate the European call option price."""

        # At expiration, the option is worth its intrinsic value.
        if self.T == 0:
            return max(self.S - self.K, 0.0)

        # With zero volatility, the terminal stock price is deterministic.
        if self.sigma == 0:

            discounted_stock = self.S * math.exp(-self.q * self.T)
            discounted_strike = self.K * math.exp(-self.r * self.T)

            return max(discounted_stock - discounted_strike, 0.0)

        # Standard Black-Scholes-Merton call pricing formula.
        call = (
            self.S
            * math.exp(-self.q * self.T)
            * norm.cdf(self.d1)
            -
            self.K
            * math.exp(-self.r * self.T)
            * norm.cdf(self.d2)
        )

        return float(call)

    def put_price(self) -> float:
        """Calculate the European put option price."""

        if self.T == 0:
            return max(self.K - self.S, 0.0)

        if self.sigma == 0:

            discounted_stock = self.S * math.exp(-self.q * self.T)
            discounted_strike = self.K * math.exp(-self.r * self.T)

            return max(discounted_strike - discounted_stock, 0.0)

        put = (
            self.K
            * math.exp(-self.r * self.T)
            * norm.cdf(-self.d2)
            -
            self.S
            * math.exp(-self.q * self.T)
            * norm.cdf(-self.d1)
        )

        return float(put)

    def greeks(self) -> dict:
        """
        Calculate European option prices and analytical Greeks.

        Conventions
        -----------
        Delta: Price sensitivity to a $1 underlying move.
        Gamma: Change in delta per $1 underlying move.
        Vega: Price sensitivity to a 1 percentage-point volatility move.
        Theta: Calendar-day time decay, annual theta divided by 365.
        Rho: Price sensitivity to a 1 percentage-point rate move.

        At expiration or zero volatility, Greeks are returned as
        None because standard analytical formulas are undefined
        or may be discontinuous.
        """

        call = self.call_price()
        put = self.put_price()

        if self.T == 0 or self.sigma == 0:

            return {
                "call_price": round(call, 4),
                "put_price": round(put, 4),
                "call_delta": None,
                "put_delta": None,
                "gamma": None,
                "vega": None,
                "call_theta": None,
                "put_theta": None,
                "call_rho": None,
                "put_rho": None
            }

        sqrt_T = math.sqrt(self.T)

        discount_q = math.exp(-self.q * self.T)
        discount_r = math.exp(-self.r * self.T)

        pdf_d1 = norm.pdf(self.d1)

        # Delta measures option price sensitivity to stock price.
        call_delta = discount_q * norm.cdf(self.d1)

        put_delta = discount_q * (norm.cdf(self.d1) - 1.0)

        # Gamma measures how quickly delta changes.
        gamma = (
            discount_q * pdf_d1
            / (self.S * self.sigma * sqrt_T)
        )

        # Vega measures sensitivity to implied volatility.
        # Divide by 100 for a one percentage-point volatility change.
        vega = (
            self.S * discount_q * pdf_d1 * sqrt_T
        ) / 100.0

        # Theta measures sensitivity to the passage of time.
        # Divide annual theta by 365 for calendar-day theta.
        common_theta = (
            -self.S
            * discount_q
            * pdf_d1
            * self.sigma
            / (2.0 * sqrt_T)
        )

        call_theta = (
            common_theta
            - self.r * self.K * discount_r * norm.cdf(self.d2)
            + self.q * self.S * discount_q * norm.cdf(self.d1)
        ) / 365.0

        put_theta = (
            common_theta
            + self.r * self.K * discount_r * norm.cdf(-self.d2)
            - self.q * self.S * discount_q * norm.cdf(-self.d1)
        ) / 365.0

        # Rho measures sensitivity to the risk-free interest rate.
        # Divide by 100 for a one percentage-point rate change.
        call_rho = (
            self.K * self.T * discount_r * norm.cdf(self.d2)
        ) / 100.0

        put_rho = (
            -self.K * self.T * discount_r * norm.cdf(-self.d2)
        ) / 100.0

        return {
            "call_price": round(float(call), 4),
            "put_price": round(float(put), 4),
            "call_delta": round(float(call_delta), 4),
            "put_delta": round(float(put_delta), 4),
            "gamma": round(float(gamma), 4),
            "vega": round(float(vega), 4),
            "call_theta": round(float(call_theta), 4),
            "put_theta": round(float(put_theta), 4),
            "call_rho": round(float(call_rho), 4),
            "put_rho": round(float(put_rho), 4)
        }


if __name__ == "__main__":

    engine = BlackScholes(
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        sigma=0.20,
        q=0.0
    )

    print("--- Black-Scholes Test ---")
    print(engine.greeks())