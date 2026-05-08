# Market Simulator

An agent-based financial market simulator built in Python and Dash that
models how prices emerge from the interactions of traders with different
strategies. Built as a hands-on way to internalize concepts in quantitative
finance — stochastic processes, market microstructure, portfolio theory,
and information asymmetry.

## What it does

The simulator runs a market with four trader personality types, each using
a different mathematical strategy to place buy/sell orders each round.
The price updates based on net order pressure, market impact (lambda),
and a stochastic shock term modelling real world randomness.

Two correlated assets run simultaneously with tunable correlation,
allowing exploration of portfolio theory and diversification effects.
All parameters are adjustable via live sliders and the simulation
animates in real time.

## Trader personalities

| Personality | Strategy | Formula |
|---|---|---|
| Fundamentalist | Trades toward true value | order = 0.5 * (true_value - price) |
| Momentum | Chases trends | order = 0.8 * (price - last_price) |
| Contrarian | Fades trends | order = -0.8 * (price - last_price) |
| Noise | Random trading | order ~ N(0, 2) |

## Price update mechanism

$$P_{t+1} = P_t + \lambda D_t + \epsilon_t$$

Where:
- $\lambda$ = market impact (how sensitive price is to order flow)
- $D_t$ = net order pressure from all traders that round
- $\epsilon_t$ ~ N(0, σ²) = stochastic shock term

## Correlated assets

Two stocks run simultaneously with shocks generated using:

$$\epsilon_B = \sigma(\rho Z_1 + \sqrt{1-\rho^2} Z_2)$$

This preserves unit variance across both assets regardless of correlation,
allowing clean exploration of diversification effects.

## Key findings

- Fundamentalists outperform in most market conditions — knowing
  roughly what something is worth beats every other strategy long term
- Momentum traders lose systematically in mean-reverting markets —
  they buy high and sell low by design
- Contrarians outperform momentum by doing the opposite —
  they accidentally replicate value investing without knowing true value
- Noise traders sometimes beat momentum — random losses are less
  damaging than systematic ones
- At high trader counts, momentum can temporarily dominate by
  creating self-reinforcing bubbles — until the reversal hits

## Tunable parameters

- Number of traders
- Volatility (σ)
- Lambda (market impact)
- Number of rounds
- Information asymmetry (noise in fundamentalists' true value estimate)
- Correlation between the two assets

## Tech stack

- Python 3
- Dash + Plotly (real time animated UI)
- NumPy

## How to run

### Prerequisites
- Python 3.8 or higher — download from [python.org](https://python.org)
- Git — download from [git-scm.com](https://git-scm.com)

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/an1kens/market-simulator.git
cd market-simulator
```

**2. Install dependencies**
```bash
pip install dash plotly numpy
```

> On Mac you may need to use `pip3` instead of `pip`

**3. Run the app**
```bash
python app.py
```

> On Mac you may need to use `python3` instead of `python`

**4. Open in browser**

Go to `http://127.0.0.1:8050`

**5. Use the simulator**
- Adjust the sliders to configure market parameters
- Click **RUN SIMULATION** to start
- Watch the price chart animate in real time
- Observe the wealth cards to see which trader type is winning

### Troubleshooting

If you see `command not found: pip`, try `pip3`.  
If you see `command not found: python`, try `python3`.  
If the browser doesn't open automatically, manually go to `http://127.0.0.1:8050`.

---

Built with AI assistance as part of a self-directed exploration of
quantitative finance concepts.