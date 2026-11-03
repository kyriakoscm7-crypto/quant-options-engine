# QUANT INTELLIGENCE
## Master Project Handoff, Technical Context & AI Development Instructions

**Prepared:** November 2, 2026  
**Repository:** https://github.com/kyriakoscm7-crypto/quant-options-engine  
**Live application:** https://quant-intelligence-km.streamlit.app/  
**Project name:** Quant Intelligence  
**Original repository name:** Quant Options Engine  
**Development environment:** macOS, VS Code, Python, GitHub  
**Audience:** New human contributors and AI coding assistants, including Claude and Codex

---

# 1. READ THIS FIRST — INSTRUCTIONS TO CLAUDE

You are joining an established quantitative finance software project, not starting a new project.

The repository already contains a substantial Python application, quantitative models, frontend modules, tests, automation, and prior development work.

Your responsibility is to:

1. Understand the existing architecture before editing.
2. Preserve all working functionality.
3. Respect the existing visual and product direction.
4. Develop within the established codebase instead of unnecessarily rebuilding it.
5. Collaborate safely with another developer and AI assistant.
6. Improve the application's financial, engineering, and product quality.
7. Submit changes through GitHub Pull Requests.
8. Never modify production or deploy without authorization.

**Critical:** This handoff describes prior development work and known project intentions. It is not a live inspection of the current repository.

Some recent changes were tested locally but may not have been pushed, merged, or deployed.

Always inspect the repository and its current branches before concluding which features are implemented.

Do not treat planned functionality as completed functionality.

---

# 2. EXECUTIVE SUMMARY

Quant Intelligence is an interactive quantitative finance research platform built primarily in Python.

Its foundations include:

- Black–Scholes–Merton options pricing.
- Analytical options Greeks.
- Implied volatility calculations.
- Portfolio and options risk analysis.
- Scenario modeling.
- Financial market exploration.
- Interactive data visualizations.
- Educational explanations of financial concepts.
- A FastAPI REST interface.
- Automated tests and development tooling.

The interface is primarily built with Streamlit and Plotly.

The backend is modular and designed to keep quantitative calculations separate from presentation components.

The application began as an options pricing engine and has progressively evolved into a broader financial research environment.

## Long-term product vision

Build an intelligent quantitative research workspace that allows users to:

- Understand financial markets.
- Analyze options and risk.
- Explore hypothetical outcomes.
- Research potential trading strategies.
- Visualize financial relationships.
- Learn quantitative finance.
- Eventually test and track paper-trading ideas.
- Obtain transparent, evidence-based insights.

The platform should be useful, credible, technically sophisticated, and visually polished.

It should not become a collection of unrelated pages simply because new features are interesting.

**Product principle: depth and integration are more important than feature count.**

---

# 3. WHAT SUCCESS LOOKS LIKE

The project's goals are threefold.

## A. Engineering quality

The application should demonstrate professional software engineering practices:

- Modular, understandable code.
- Reusable financial calculations.
- Robust error handling.
- Reproducible results.
- Automated tests.
- Secure environment configuration.
- Version-controlled development.
- Reliable deployment.
- Documented architectural decisions.
- Performance-conscious numerical computation.

## B. Product quality

The application should feel like a serious, modern research product.

Important qualities include:

- Clear hierarchy.
- Professional typography.
- Responsive layouts.
- Intuitive navigation.
- Fast interactions.
- Excellent data visualization.
- Consistent design.
- Transparent assumptions.
- Minimal clutter.

It must not feel like a collection of disconnected student assignments.

## C. Practical usefulness

Features should solve recognizable problems.

Examples:

- How does an option's value respond to changes in volatility?
- How do Greeks explain exposure to market movements?
- What could happen to a portfolio after a market shock?
- How does a hypothetical strategy behave under alternative assumptions?
- What makes one risk scenario materially different from another?

Every major feature should answer a specific user question.

---

# 4. REPOSITORY AND ENVIRONMENT

## Canonical repository

https://github.com/kyriakoscm7-crypto/quant-options-engine

The original owner controls the central GitHub repository.

The cousin is joining as a collaborator.

## Live application

https://quant-intelligence-km.streamlit.app/

The historical production frontend has been deployed through Streamlit Community Cloud.

Do not assume that a successful GitHub push automatically means every environment is safely configured.

Inspect the current deployment settings before making changes.

## Known technologies

| Area | Technology |
|---|---|
| Primary language | Python |
| Web dashboard | Streamlit |
| Visualization | Plotly |
| Backend API | FastAPI |
| Testing | pytest |
| Code quality | Ruff; earlier tooling also included flake8 and isort |
| Source control | Git and GitHub |
| Automation | GitHub Actions |
| Packaging/deployment | Docker support |
| Quantitative computations | Python numerical ecosystem |
| Development | VS Code on macOS |

The original developer has worked with a local `.venv` Python virtual environment, including a Python 3.15 environment in recent development.

**Do not assume the exact current Python version, supported dependency range, or package manager without reading the repository configuration.**

Inspect the Python requirements, project configuration, workflow files, and deployment runtime settings.

---

# 5. KNOWN ARCHITECTURE

The project was structured to separate four broad concerns:

1. Financial modeling.
2. Market data and analysis.
3. Application/backend services.
4. User interface and visualization.

The FastAPI application was previously located at:

`app/api/main.py`

The primary Streamlit application has been worked on at:

`dashboard/main.py`

Additional files previously used include:

- `dashboard/premium_home.py`
- `dashboard/portfolio_page.py`
- `dashboard/premium_theme.css`
- `.streamlit/config.toml`

A branded favicon asset named `qi_favicon.png` was integrated.

There is an existing Black–Scholes implementation that other modules import and reuse.

The application has included an options research workflow, Greeks calculations, scenario analysis, and portfolio-related functionality.

**Important:** These are historically observed paths and modules, not an exhaustive or guaranteed current directory tree.

Before coding, inspect the actual file structure.

Do not invent module names or assume imports work based solely on this document.

## Architecture rules

- Keep financial mathematics separate from interface rendering.
- Reuse existing pricing and risk functions.
- Avoid duplicating Black–Scholes or Greeks implementations.
- Avoid calculations that run unnecessarily on each Streamlit rerender.
- Keep API logic and frontend state management appropriately separated.
- Preserve the existing testable calculation layer.
- Keep visualization code maintainable.
- Avoid introducing circular dependencies.
- Introduce new services only when they solve a genuine architectural problem.

---

# 6. QUANTITATIVE ENGINE — EXISTING FOUNDATIONS

## 6.1 Black–Scholes–Merton

The project has implemented European options pricing.

The standard pricing model is:

Call:

C = S·N(d₁) − K·e^(−rT)·N(d₂)

Put:

P = K·e^(−rT)·N(−d₂) − S·N(−d₁)

Where:

d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T)

d₂ = d₁ − σ√T

Variables:

- S = underlying asset price.
- K = strike price.
- T = time to expiration in years.
- r = continuously compounded risk-free interest rate.
- σ = annualized volatility.
- N = standard normal cumulative distribution.

These are the standard no-dividend formulas. The implementation must be checked for its actual dividend assumptions and conventions.

### Numerical concerns

Be careful with:

- Zero time to expiration.
- Zero or near-zero volatility.
- Extremely deep in-the-money or out-of-the-money options.
- Invalid prices or negative inputs.
- Floating-point precision.
- Calendar-day versus trading-day conventions.
- Volatility representation as decimal versus percentage.

Never silently change a financial convention.

Any model modification requires appropriate numerical regression tests.

---

## 6.2 Options Greeks

The project includes analytical Greeks.

Core Greeks include:

**Delta:** Sensitivity of option value to the underlying asset price.

**Gamma:** Sensitivity of delta to the underlying asset price.

**Theta:** Sensitivity of option value to the passage of time.

**Vega:** Sensitivity of option value to implied volatility.

**Rho:** Sensitivity of option value to interest rates.

The Greeks should be presented in a manner that makes them understandable and useful.

They should not be displayed merely as unexplained numerical outputs.

### Important implementation conventions

Clarify:

- Whether Theta is annual or daily.
- Whether Vega is quoted per unit volatility or per one percentage-point change.
- Whether Rho is quoted per unit interest-rate change or one percentage-point change.
- The sign conventions used.
- The model assumptions.

When changing these conventions, update frontend labels, explanatory text, and tests together.

### Recent development history

A significant Greeks Risk Intelligence upgrade was completed and tested locally in a prior development session.

The reported validation included Ruff and 1,725 passing tests.

This is a historical local test snapshot, **not proof that the changes are currently committed, merged, or deployed**.

Inspect the relevant branch and commits before attempting to recreate this feature.

---

## 6.3 Implied volatility

The project has included implied volatility estimation.

This is the numerical process of finding the volatility that makes a pricing model reproduce a supplied option price.

Important considerations:

- Solver convergence.
- Valid option price bounds.
- No-arbitrage constraints.
- Reasonable volatility search intervals.
- Numerical stability.
- Error reporting when a solution cannot be found.

Do not replace the existing solver without understanding and comparing its tested behavior.

---

## 6.4 Vectorized numerical operations

Performance optimization is an established part of the project.

Earlier project documentation reported approximate benchmark results including:

| Operation | Previously reported performance |
|---|---:|
| Vectorized options pricing | 3.62 million options/second |
| Vectorized Greeks | 3.87 million/second |
| Scenario analysis | 1.41 million combinations/second |
| Pricing speedup | 262.89× |

These are historical benchmark claims.

They are not guarantees about current performance or every machine.

The original benchmark methodology, input sizes, machine specifications, and timing conventions must be verified before presenting these numbers publicly as current results.

Maintain vectorization where it produces meaningful benefits without sacrificing accuracy or maintainability.

---

# 7. OPTIONS RESEARCH WORKSPACE

Options analytics is one of the main product pillars.

Historical interface development has included user-controlled parameters such as:

- Underlying price.
- Strike price.
- Days to expiration.
- Volatility.
- Risk-free rate.

The application has visualized call and put price curves and explored relationships between model assumptions and option values.

An earlier overview visualization used a reference asset price of S = 100 with a vertical reference line.

## Intended user experience

The Options Research Workspace should allow users to:

1. Enter or adjust option parameters.
2. Calculate theoretical values.
3. Understand Greeks.
4. Inspect charts.
5. Change assumptions interactively.
6. Compare model outputs.
7. Understand risk exposures.

## Design requirements

- Do not overwhelm users with dozens of controls.
- Show clearly which parameters drive each output.
- Keep mathematical units consistent.
- Use responsive Plotly charts.
- Label axes meaningfully.
- Explain why a metric matters.
- Maintain consistency across modules.

Do not build a second, competing options pricing interface without a compelling reason.

Prefer improving the existing research workflow.

---

# 8. RISK INTELLIGENCE

Risk Intelligence has been part of the premium dashboard.

Previously discussed and implemented capabilities include historical analysis of a selected stock against the SPY market benchmark.

The implementation used independent one-year daily price histories.

The intention was to deliver reproducible risk and return metrics, rather than arbitrary or unexplained scores.

## Important rules

- Clearly identify historical periods.
- Explain how returns are calculated.
- Distinguish annualized versus period-specific metrics.
- Account for missing or nonaligned data.
- Do not imply historical statistics predict future returns.
- Define volatility and Sharpe ratio conventions.
- Document benchmark assumptions.

If the frontend or API uses real financial market data, inspect the source, licensing, caching, and data quality assumptions.

Avoid displaying stale data as current market information.

---

# 9. SCENARIO EXPLORER / MARKET STRESS TESTING

Scenario Explorer is an especially important area of ongoing development.

A redesign of the existing Scenario Explorer was being investigated.

A previous repository inspection script searched for a Streamlit page condition similar to:

`elif page == "📈 Scenario Explorer":`

That is a historical code-location clue, not a guarantee of the current navigation structure.

## Intended evolution

The feature should become a serious **Market Stress Testing Lab**.

Users should be able to examine hypothetical scenarios such as:

- Underlying price increases or decreases.
- Volatility shocks.
- Time decay.
- Interest-rate changes.
- Combinations of multiple risk factors.

## Long-term desired outputs

- Scenario-adjusted option values.
- Profit and loss visualizations.
- Exposure sensitivity.
- Interactive scenario comparisons.
- Risk summaries.
- Carefully labeled assumptions.

Potential advanced capabilities include multi-variable surfaces, scenario matrices, and portfolio stress testing.

## Financial rigor

Separate:

- Model-based hypothetical P&L.
- Historical observations.
- Realized trading P&L.
- Estimated transaction costs.
- Mark-to-market valuation.

Never imply a model scenario is a predicted market outcome.

Scenario Explorer should share the tested financial calculation layer with Options Research and Portfolio Manager.

---

# 10. PORTFOLIO MANAGER

A Portfolio Manager module existed in the project.

It has previously been treated as an important existing feature that should not be disturbed during unrelated redesigns.

The project historically included portfolio scenario analysis and risk calculations.

Earlier reports listed very high test coverage in some portfolio calculation modules.

## Instructions

Inspect the existing Portfolio Manager before making changes.

Identify:

- Its current supported instruments.
- Position representation.
- Valuation logic.
- Portfolio aggregation rules.
- Risk metrics.
- Dependencies.
- Test coverage.

Do not assume the existing Portfolio Manager is already a full paper-trading system.

Portfolio analytics and paper-trading execution are different concerns.

**Preserve Portfolio Manager functionality unless a specific, approved task requires changing it.**

---

# 11. STOCK EXPLORER / MARKET RESEARCH

The project has also included stock-oriented research functionality.

Earlier development reorganized Stock Explorer into a structure resembling:

- At-a-Glance.
- Primary chart.
- Performance.
- Risk.
- News.
- Data.

The intention was to make research easier to navigate and avoid presenting every metric simultaneously.

## Design principles

- Give the user a clear starting summary.
- Make historical chart periods explicit.
- Distinguish price return from total return where appropriate.
- Use consistent units.
- Communicate source availability.
- Avoid excessive charts that repeat the same information.
- Provide useful insights without overstating certainty.

Inspect the actual application to determine what remains implemented.

---

# 12. QUANT LEARN

Quant Learn was developed as an educational capability.

The idea is to help people who are new to quantitative finance understand the tools they are using.

Potential topics include:

- Calls and puts.
- Strike prices.
- Expiration.
- Volatility.
- Black–Scholes.
- The Greeks.
- Portfolio risk.
- Scenario analysis.

The educational experience should feel integrated into the research platform rather than like a separate generic textbook.

Explanations should be concise, accurate, and easy to understand.

Interactive examples are preferable when they materially improve understanding.

## Historical deployment milestone

On October 31, 2026, a project update reported that GitHub `main` and a branch called `quant-intelligence-automation` were updated to release commit:

`b0b7d07`

The live Streamlit deployment was reported to display Quant Learn at that point.

This is a useful historical release reference.

Verify the current production commit rather than assuming that release is still the latest deployment.

---

# 13. FASTAPI BACKEND

The project includes a FastAPI REST application.

Earlier project documentation reported approximately ten REST endpoints and support for batch computation.

One historical documented batch API limit was 10,000 option contracts.

The backend is important because it demonstrates a separation between financial computation and user interface rendering.

It also provides a foundation for potential future clients beyond Streamlit.

## Backend priorities

- Typed and documented request/response schemas.
- Correct validation of numerical inputs.
- Predictable error responses.
- Reusable calculation services.
- Testable business logic.
- Stable endpoint contracts.
- Reasonable batch-size and computational limits.
- Secure configuration.

Do not break existing API behavior casually.

A frontend redesign should not require replacing the backend.

---

# 14. PREMIUM BRANDING AND DESIGN SYSTEM

The project has undergone significant visual redesign.

The established direction is:

**Premium dark financial technology platform.**

## Known palette

| Role | Color |
|---|---|
| Primary accent | `#FF78B7` |
| Deep background | `#080D1D` |
| Secondary dark background | `#0D1424` |
| Elevated surface | `#121D35` |
| Plot background | `#111B30` |
| Primary text | `#FFFFFF` |
| Secondary text | `#E5E7EB` |
| Alternative light text | `#DCE5F6` |

The design uses deep navy, white, black-toned surfaces, and bubblegum pink accents.

## Visual principles

1. Professional, modern, and restrained.
2. Strong layout hierarchy.
3. Limited decorative elements.
4. Good contrast and legibility.
5. Consistent spacing.
6. Purposeful use of pink.
7. Responsive desktop and mobile layouts.
8. Clearly labeled charts.
9. Consistent interactive controls.
10. Minimal unnecessary emojis.

The original developer strongly prefers a polished visual style rather than Streamlit's default appearance.

## Historical improvements

Previous work included:

- Custom Streamlit styling.
- `premium_theme.css`.
- `premium_home.py`.
- Dark Streamlit theme configuration.
- Logo and favicon integration.
- Two-column dashboard layouts.
- Improved metric card presentation.
- Mobile responsiveness.
- Fixes for large numerical values overflowing their containers.

These changes took effort and should be preserved.

Do not replace the established palette with a different branding scheme.

Do not casually introduce new accent colors or visual conventions.

---

# 15. HOMEPAGE DESIGN PHILOSOPHY

The homepage went through multiple iterations.

A major recurring concern was feature overload.

Earlier ideas involved many separate modules or pages, including:

- Market Scanner.
- Quant Discovery.
- Portfolio Manager.
- Forecast Intelligence.

The original developer felt that too many disconnected modules made the product seem bloated.

The preferred direction became a focused flagship research dashboard.

## Product rule

The homepage should answer:

- What is this platform?
- What can I investigate?
- Where should I begin?
- Why is the analysis useful?

It should not attempt to present every feature in equal detail.

A recent homepage cleanup was reported to have passed Ruff and 1,709 tests in a prior local development session.

Again, verify branch and commit status before assuming the cleanup is already in the cloned repository.

---

# 16. CURRENT AND FUTURE PRODUCT ROADMAP

The roadmap has evolved across multiple sessions.

The latest known product direction prioritized the following sequence.

## Priority 1 — Options Research Workspace

Build on existing options pricing and analytical tools.

The goal is to make the workspace accurate, useful, integrated, and visually excellent.

Some of this work has already been completed.

Verify current implementation before planning changes.

## Priority 2 — Greeks Risk Intelligence

Provide meaningful analysis of sensitivities and exposure.

The aim is to help users interpret and compare risks instead of just seeing numbers.

A substantial upgrade was reported completed locally.

Verify its actual Git status.

## Priority 3 — Scenario Explorer / Market Stress Testing Lab

This is a particularly relevant upcoming workstream.

Build an interactive environment for evaluating hypothetical market shocks and their effects.

Prefer extending the existing scenario engine rather than rebuilding calculations.

## Priority 4 — Strategy Research

Explore hypothetical options strategies in a structured and reproducible manner.

Potential future capabilities:

- Strategy payoff diagrams.
- Break-even calculations.
- Risk/reward summaries.
- Scenario comparisons.
- Strategy screening.
- Historical testing where adequate market data exists.

All strategy analysis must distinguish theoretical payoff from realistic execution.

Include costs, spreads, slippage, and data limitations when relevant.

## Longer-term — Information Diffusion Intelligence

An exploratory concept involving how information propagates through markets.

Potential applications might include tracking attention, announcements, and subsequent market reactions.

This remains exploratory, not an established finished product.

## Longer-term — Kalshi / Prediction Market Intelligence

An exploratory opportunity to research event-based market probabilities and related analytics.

No production-ready integration should be assumed.

Any implementation would require careful review of:

- Provider APIs.
- Jurisdictional restrictions.
- Data usage terms.
- Reliability.
- Financial interpretation.

## Additional explored opportunity — Paper Trading

The original developer also wants to explore paper trading.

Historically discussed architecture:

- FastAPI backend.
- PostgreSQL database.
- Virtual cash accounts.
- Position tracking.
- Transaction history.
- Order simulation.
- Portfolio analysis.
- Performance metrics.

Potential performance metrics include:

- Cumulative returns.
- Sharpe ratio.
- Asset allocation.
- Drawdowns.
- Risk exposure.

This is a proposed future capability, not a confirmed complete implementation.

### Important paper-trading design issues

- Virtual account persistence.
- User authentication.
- Order validation.
- Cash balance checks.
- Position consistency.
- Transaction atomicity.
- Market data timestamps.
- Fill simulation.
- Fees and slippage.
- Audit logs.
- Concurrency.
- Clear separation of simulation and real-money trading.

Do not add database or authentication infrastructure before the architecture is agreed upon.

---

# 17. HISTORICAL TESTING AND QUALITY

This project already has substantial automated tests.

Different milestones reported different test counts.

| Historical stage | Reported passing tests |
|---|---:|
| Earlier documented baseline | 638 |
| Premium redesign stage | 1,582 |
| Intermediate development | Approximately 1,621 |
| Homepage cleanup | 1,709 |
| Greeks upgrade | 1,725 |

These numbers represent different points in development.

**Do not describe 1,725 as the current passing total without running the current test suite.**

Earlier documentation reported approximately 93% overall coverage, with stronger coverage for certain core quantitative modules.

Coverage percentages must also be remeasured before publication.

## Mandatory development rules

Before editing:

- Inspect Git status.
- Identify the active branch.
- Inspect existing tests.
- Identify affected modules.
- Establish a baseline test result.

During development:

- Keep changes focused.
- Write or update relevant tests.
- Preserve mathematical behavior.
- Avoid unrelated refactoring.
- Maintain code-quality conventions.

Before opening a Pull Request:

- Run relevant focused tests.
- Run the appropriate linting checks.
- Run the full suite where practical.
- Review the diff.
- Check for leaked credentials.
- Confirm no unrelated files were changed.

Do not remove tests to achieve a passing build.

Do not change correct financial calculations just to satisfy an incorrect new test.

Do not claim tests passed unless they were actually executed.

---

# 18. GITHUB WORKFLOW FOR TWO DEVELOPERS

Two developers will collaborate using GitHub.

One may use ChatGPT/Codex, while the other uses Claude.

The AI assistants do not need shared accounts or shared conversations.

GitHub is the shared source of truth.

## Roles

### Original owner

- Owns the canonical repository.
- Controls production deployment.
- Maintains final product direction.
- Reviews proposed changes.
- Controls production credentials.
- Approves releases.

### Cousin / collaborator

- Works on assigned features.
- Uses their own GitHub account.
- Develops on separate branches.
- Runs local tests.
- Opens Pull Requests.
- Explains implementation decisions.
- Responds to review feedback.

Both developers can contribute ideas, review code, and discuss technical direction.

## Branch strategy

Use:

`main`

for the stable, deployable version.

Use feature branches for development.

Examples:

`feature/scenario-stress-testing`

`feature/greeks-explanations`

`feature/paper-trading-api`

`fix/mobile-chart-overflow`

Keep branch names descriptive.

## Standard workflow

1. Start from an up-to-date, clean development baseline.
2. Create a feature branch.
3. Make scoped changes.
4. Run tests.
5. Commit the changes.
6. Push the branch.
7. Create a Pull Request.
8. Obtain required checks and reviews.
9. Merge only when approved.
10. Verify behavior after merging.

Do not work directly on `main`.

Do not force-push shared branches.

Do not overwrite someone else's uncommitted work.

Do not delete or reset unfamiliar branches.

If changes already exist locally, inspect and preserve them before switching branches or updating the repository.

---

# 19. BRANCH PROTECTION AND APPROVALS

The desired security model is:

**The original owner controls what reaches the main application.**

Configure appropriate GitHub protection for `main`.

Desired controls:

- Require Pull Requests.
- Require at least one approval.
- Dismiss stale approvals when relevant.
- Require passing automated checks.
- Block force pushes.
- Block branch deletion.
- Restrict bypasses where supported.
- Maintain a stable deployment branch.

### Important GitHub limitation

A generic requirement for one approval does not automatically mean the original owner personally must approve.

Repository type, plan, permissions, and GitHub configuration affect what can be enforced.

For stricter ownership control, investigate code owners, review requirements, organizational permissions, and repository rulesets.

Do not assume that giving someone collaborator access to a personal repository is equivalent to granting them feature-branch-only access.

Inspect the actual settings before relying on protection behavior.

---

# 20. CONTINUOUS INTEGRATION

GitHub Actions has been part of the project.

The desired CI pipeline should validate Pull Requests before merging.

Recommended stages include:

1. Checkout.
2. Configure the supported Python runtime.
3. Install project dependencies.
4. Run linting.
5. Run relevant formatting checks.
6. Run automated tests.
7. Optionally measure coverage.
8. Report clear pass/fail results.

Check existing workflows first.

Do not duplicate working CI infrastructure.

### Required-status-check considerations

Required GitHub checks must correspond to real, functioning workflow jobs.

Avoid making a job mandatory before confirming it triggers successfully for the target branches.

Check whether external contributors or forked Pull Requests have different execution permissions.

Avoid exposing production credentials to untrusted Pull Request code.

---

# 21. DEPLOYMENT SECURITY

The original developer should retain control of production.

The collaborator should not require production deployment credentials to build or test most features.

## Required separation

### Development

Local environment with test inputs and nonproduction configuration.

### Testing

Automated checks and, where feasible, a staging deployment.

### Production

Stable application available to users.

Production should be connected to an intentionally selected branch and deployment configuration.

### Secrets

Never commit:

- API keys.
- Database passwords.
- Cloud credentials.
- Private tokens.
- User secrets.
- `.env` files containing credentials.

Maintain an appropriate `.gitignore`.

Use secure environment-variable or platform-secret mechanisms.

Be cautious with logs, screenshots, error messages, and AI prompts that could expose secrets.

### Streamlit specifics

Inspect the current Streamlit Community Cloud settings:

- Repository.
- Branch.
- Entrypoint.
- Python version.
- Dependencies.
- App secrets.
- Deployment permissions.

A collaborator with GitHub access should not automatically be treated as authorized to access the hosting account.

---

# 22. HOW TO HANDLE MISTAKES

Mistakes are expected in collaborative software development.

The workflow should make them recoverable.

## Bug in a feature branch

Fix it on the branch before merging.

## Failed automated tests

Inspect the failure.

Determine whether it reflects an implementation issue, environment mismatch, or test issue.

Do not bypass checks just to merge.

## Merge conflict

Understand both sets of changes.

Resolve conflicts deliberately.

Retest after resolution.

## Broken production release

Identify the release commit.

Use GitHub history to prepare a revert or corrective release.

Verify that the prior state can be restored.

## Incorrect numerical result

Treat this as a high-priority defect.

Compare against independent analytical results, known reference cases, or verified financial identities.

Add regression tests.

Do not merely hide the failing output.

---

# 23. INTERACTION BETWEEN CLAUDE AND CODEX

Both AI assistants should follow the same fundamental standards.

## No assumptions about shared context

Claude cannot see previous Codex discussions unless the relevant context is supplied.

Codex cannot automatically see Claude's unpublished local edits.

## Source of truth

Use this priority order:

1. Actual repository code and configuration.
2. Passing tests and validated runtime behavior.
3. Git history and Pull Requests.
4. Current project documentation.
5. This historical handoff.
6. Unverified assumptions.

When sources conflict, investigate rather than guessing.

## Handoff requirements between developers

Each significant Pull Request should explain:

- What changed.
- Why it changed.
- Which files were modified.
- What tests were run.
- Any known limitations.
- Screenshots for visual changes.
- Whether there are migration or deployment implications.

AI assistants should prepare changes that another human or AI can understand and review.

---

# 24. USER EXPERIENCE AND WORKING STYLE

The original developer prefers clear, controlled development steps.

Particularly important preferences:

- Work through implementation logically.
- Explain changes in straightforward language.
- Prefer terminal-based commands when practical.
- Avoid huge unexplained code replacements.
- Preserve existing functionality.
- Test changes before moving on.
- Keep the design polished.
- Make the interface useful rather than decorative.
- Avoid unnecessary feature bloat.
- Maintain responsiveness on mobile.
- Keep quantitative calculations correct.

When the original developer is directly following implementation instructions, one command or small step at a time is preferred.

When an AI assistant has access to a coding environment and has been explicitly asked to implement something, it should inspect the relevant code and perform appropriately scoped work rather than producing speculative patches.

---

# 25. WHAT NOT TO DO

Do not:

1. Rebuild the project from scratch.
2. Replace Streamlit with React without an explicit architectural decision.
3. Replace FastAPI merely for convenience.
4. Rewrite tested financial models unnecessarily.
5. Remove existing tools to simplify a new implementation.
6. Rename large portions of the repository without an agreed plan.
7. Change the design palette.
8. Add dozens of unfinished pages.
9. Introduce unnecessary cloud costs.
10. Expose secrets.
11. Make unauthorized production changes.
12. Circumvent required reviews.
13. Ignore failing tests.
14. Claim performance benchmarks without verification.
15. Claim financial predictions are reliable without evidence.
16. Make significant dependency upgrades without testing.
17. Mix unrelated refactors into feature Pull Requests.
18. Assume an AI-generated implementation is correct because it looks polished.

Preserve the engineering investment already made.

---

# 26. NEXT DEVELOPMENT PRIORITIES

The immediate priority is not creating more unrelated features.

It is making the existing platform an integrated, impressive research product.

Recommended sequence:

## Phase 1 — Repository inspection and stabilization

- Establish current commit and branch.
- Understand active modules.
- Identify unfinished development work.
- Run the full test suite.
- Inspect CI.
- Verify branch protections.
- Confirm production deployment configuration.

## Phase 2 — Collaboration infrastructure

- Invite collaborator.
- Define branch workflow.
- Configure protected `main`.
- Set up required checks.
- Establish a Pull Request template.
- Document code ownership and review rules.
- Protect production credentials.

## Phase 3 — Core product refinement

- Review Options Research.
- Verify Greeks Risk Intelligence.
- Assess Scenario Explorer.
- Confirm premium dashboard consistency.
- Resolve major responsiveness issues.
- Improve user-facing explanation of quantitative outputs.

## Phase 4 — Flagship capability

Develop a cohesive Market Stress Testing Lab.

Integrate option pricing, Greeks, and scenario analysis.

Build an experience that is meaningfully more useful than a basic calculator.

## Phase 5 — Expansion

Evaluate Strategy Research, paper trading, and other new opportunities against product value, complexity, data availability, and maintenance cost.

Only advance features that justify their complexity.

---

# 27. FIRST ACTIONS FOR CLAUDE

Before writing new code, perform a read-only repository audit.

Identify:

1. Current Git branch and commit.
2. Working tree cleanliness.
3. Available branches and open development work.
4. Top-level project structure.
5. Frontend entrypoint.
6. FastAPI entrypoint.
7. Financial calculation modules.
8. Existing tests.
9. CI workflows.
10. Dependency configuration.
11. Current navigation structure.
12. Production configuration documented in the repository.
13. Existing feature completeness.
14. Risks from pending changes or merge conflicts.

Then provide a concise architectural report.

Do not make modifications in the same step unless the developer explicitly requests implementation.

### Suggested initial read-only commands

```bash
git status --short
git branch --show-current
git log -5 --oneline
git branch -a
git remote -v
ls -la
find .github/workflows -maxdepth 2 -type f
```

The `.github/workflows` inspection should be skipped gracefully if that directory does not exist.

Inspect project configuration, README, and source structure next.

Avoid printing secrets, environment files, or sensitive credentials.

---

# 28. DEVELOPMENT ACCEPTANCE CRITERIA

A feature is complete when:

- Its intended behavior is clearly defined.
- Its implementation uses the existing architecture appropriately.
- Correctness is validated.
- Regression tests pass.
- Relevant edge cases are covered.
- The UI is consistent with the design system.
- The change is usable on appropriate screen sizes.
- Security and configuration implications are addressed.
- Documentation is updated when needed.
- A reviewer can understand the changes.
- No unrelated functionality is broken.

For financial features, mathematical validity is nonnegotiable.

For data-related features, source quality and timestamp transparency are essential.

For AI-assisted features, generated descriptions must not present unsupported conclusions as facts.

---

# 29. STRATEGIC PRODUCT DIRECTION

Quant Intelligence should gradually move toward a sophisticated financial research environment.

A compelling future user experience might be:

1. The user selects a financial instrument.
2. The platform presents relevant market context.
3. The user opens an options analysis workspace.
4. They adjust assumptions and investigate Greeks.
5. They test hypothetical market scenarios.
6. They compare risk profiles.
7. They examine a possible strategy.
8. They learn the underlying financial concepts as needed.
9. They optionally save or simulate the idea in a future paper-trading system.

This creates a coherent workflow rather than a collection of independent features.

That integrated experience is a major long-term differentiator.

The platform should prioritize analytical transparency, correctness, and useful interactivity over artificial claims of predictive power.

---

# 30. FINAL INSTRUCTIONS TO CLAUDE

You are collaborating on a project with an established technical foundation and a clear product direction.

Your role is to help improve it professionally.

Start by understanding what exists.

Do not duplicate previous work.

Do not make large architecture changes without agreement.

Preserve tested calculations.

Follow the established dark navy, white, and pink design language.

Respect GitHub review and branch protection requirements.

Make narrowly scoped, testable contributions.

Explain important design and engineering decisions.

Treat mathematical correctness, security, and maintainability as priorities.

When faced with uncertainty, inspect the code and report the evidence.

**The objective is to build the best version of Quant Intelligence together, not to make the largest number of changes.**

---

## END OF MASTER HANDOFF

**Document status:** Historical project handoff based on previous development discussions, recorded test results, and documented project intentions. Current repository contents, deployment state, credentials, and permissions must be independently verified before implementation.****
