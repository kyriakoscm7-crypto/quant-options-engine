"""Quant Learn curriculum metadata, independent of Streamlit."""

PATHWAYS = (
    {
        "id": "everyday",
        "icon": "credit-card",
        "title": "Everyday Money",
        "description": "Paycheques, debt, saving, and the decisions you make every week.",
        "lessons": (
            ("paycheque", "Why is my paycheque smaller than my salary?"),
            ("credit", "How credit card interest works"),
            ("growth", "How savings can grow over time"),
            ("emergency", "Why an emergency fund matters"),
        ),
    },
    {
        "id": "taxes",
        "icon": "landmark",
        "title": "Taxes & Canadian Accounts",
        "description": "Tax brackets, TFSAs, RRSPs, FHSAs, and retirement accounts.",
        "lessons": (
            ("tax_brackets", "How do tax brackets actually work?"),
            ("tfsa", "What is a TFSA, really?"),
            ("rrsp", "TFSA vs RRSP: what changes?"),
            ("fhsa", "What is an FHSA?"),
        ),
    },
    {
        "id": "investing",
        "icon": "chart-pie",
        "title": "Investing 101",
        "description": "Stocks, ETFs, bonds, dividends, and managing investment risk.",
        "lessons": (
            ("diversification", "Why diversification matters"),
            ("etfs", "What is an ETF?"),
            ("dividends", "How dividends work"),
        ),
    },
    {
        "id": "markets",
        "icon": "activity",
        "title": "How Markets Work",
        "description": "Why prices change and what drives buying and selling.",
        "lessons": (
            ("prices", "Why can stock prices move so quickly?"),
            ("orders", "Market orders vs limit orders"),
            ("crashes", "What happens during a market crash?"),
        ),
    },
    {
        "id": "economy",
        "icon": "globe",
        "title": "The Economy",
        "description": "Interest rates, inflation, employment, and monetary policy.",
        "lessons": (
            ("interest", "Why do interest rates matter?"),
            ("inflation", "How inflation affects your money"),
            ("jobs", "Why do employment reports move markets?"),
        ),
    },
    {
        "id": "companies",
        "icon": "building",
        "title": "Inside Companies",
        "description": "Earnings calls, IPOs, profits, and how businesses are valued.",
        "lessons": (
            ("earnings", "Why do stocks fall after good earnings?"),
            ("ipos", "What happens when a company goes public?"),
            ("profit", "Revenue vs profit: what's the difference?"),
        ),
    },
    {
        "id": "news",
        "icon": "newspaper",
        "title": "News to Markets",
        "description": "Connect real-world events to businesses and market expectations.",
        "lessons": (
            ("oil", "How oil prices affect everyday businesses"),
            ("consumers", "How your purchases connect to the economy"),
            ("supply", "Why supply chains matter to investors"),
        ),
    },
    {
        "id": "advanced",
        "icon": "flask",
        "title": "Advanced Finance",
        "description": "Options, risk models, backtesting, and research methods.",
        "lessons": (
            ("options_premium", "Why do option premiums change?"),
            ("options", "What are options and the Greeks?"),
            ("backtesting", "What makes a backtest trustworthy?"),
            ("valuation", "How analysts think about valuation"),
        ),
    },
)


READY_LESSONS = frozenset({
    "inflation",
    "options_premium",
    "etfs",
    "rrsp",
    "paycheque",
    "tax_brackets", "tfsa", "diversification", "prices", "interest", "earnings", "growth", "credit"
})


LESSON_SUMMARIES = {
    "options_premium": "An eight-chapter guided course with large visual explanations, interactive theoretical option pricing, time-decay diagrams and real risk lessons.",
    "inflation": "Learn how inflation changes prices, savings and purchasing power through interactive examples.",
    "etfs": "Understand ETF holdings, fund overlap, diversification and costs with fictional portfolios.",
    "rrsp": "Compare TFSA and RRSP tax treatment, growth and withdrawals using equal after-tax savings.",
    "paycheque": "Understand gross pay, payroll deductions, and take-home pay through a guided Canadian example.",
    "growth": "Explore how contributions and a hypothetical return affect savings over time.",
    "credit": "Explore how credit card interest and monthly payments affect repayment.",
    "tax_brackets": "See why moving into a higher tax bracket doesn't tax all your income at the higher rate.",
    "tfsa": "Learn what a TFSA can hold and when a withdrawal restores contribution room.",
    "diversification": "Explore how a single-company decline affects a concentrated portfolio.",
    "prices": "Learn why expectations and new information can move stock prices.",
    "interest": "Follow how changing rates can affect borrowing costs and the economy.",
    "earnings": "Understand why an earnings beat doesn't guarantee that a stock rises.",
}
