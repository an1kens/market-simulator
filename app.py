import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as np

# ── Trader class ──────────────────────────────────────────────
class Trader:
    def __init__(self, personality, true_value=100):
        self.personality = personality
        self.true_value = true_value

    def get_order(self, current_price, last_price):
        if self.personality == "fundamentalist":
            return 0.5 * (self.true_value - current_price)
        elif self.personality == "momentum":
            return 0.8 * (current_price - last_price)
        elif self.personality == "contrarian":
            return -0.8 * (current_price - last_price)
        elif self.personality == "noise":
            return np.random.normal(0, 2)

# ── App layout ────────────────────────────────────────────────
app = dash.Dash(__name__)

app.layout = html.Div(style={"backgroundColor": "#0a0a0a", "minHeight": "100vh", "padding": "20px", "fontFamily": "monospace"}, children=[

    html.H1("Market Simulator", style={"textAlign": "center", "color": "#00ff88"}),

    # sliders row
    html.Div(style={"display": "flex", "gap": "40px", "justifyContent": "center", "flexWrap": "wrap", "marginBottom": "20px"}, children=[

        html.Div([html.Label("Traders", style={"color": "#aaa"}), dcc.Slider(id="num-traders", min=4, max=100, step=4, value=20, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label("Volatility", style={"color": "#aaa"}), dcc.Slider(id="volatility", min=0.1, max=10.0, step=0.1, value=1.0, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label("Lambda", style={"color": "#aaa"}), dcc.Slider(id="lam", min=0.01, max=0.5, step=0.01, value=0.1, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label("Rounds", style={"color": "#aaa"}), dcc.Slider(id="num-rounds", min=50, max=500, step=50, value=200, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label("Info Noise", style={"color": "#aaa"}), dcc.Slider(id="info-noise", min=0.0, max=20.0, step=0.5, value=5.0, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label("Correlation", style={"color": "#aaa"}), dcc.Slider(id="correlation", min=-1.0, max=1.0, step=0.1, value=0.5, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),

    ]),

    # run button
    html.Div(html.Button("RUN SIMULATION", id="run-btn", n_clicks=0, style={"backgroundColor": "#00ff88", "color": "#0a0a0a", "border": "none", "padding": "12px 40px", "fontSize": "16px", "fontFamily": "monospace", "fontWeight": "bold", "cursor": "pointer", "borderRadius": "4px"}), style={"textAlign": "center", "marginBottom": "30px"}),

    dcc.Store(id="sim-state"),
    dcc.Interval(id="interval", interval=50, n_intervals=0, disabled=True),

    # price chart
    dcc.Graph(id="price-chart"),

    # wealth display
   html.Div(id="wealth-display", style={"display": "flex", "justifyContent": "center", "gap": "20px", "marginTop": "20px", "flexWrap": "wrap"}),

])

# callback 1 — button click initializes simulation state and starts interval
@app.callback(
    Output("sim-state", "data"),
    Output("interval", "disabled"),
    Output("interval", "n_intervals"),
    Input("run-btn", "n_clicks"),
    State("num-traders", "value"),
    State("volatility", "value"),
    State("lam", "value"),
    State("num-rounds", "value"),
    State("info-noise", "value"),
    State("correlation", "value"),
    prevent_initial_call=True
)
def initialize_simulation(n_clicks, num_traders, volatility, lam, num_rounds, info_noise, correlation):
    traders_data = []
    wealth = {}
    for i in range(num_traders):
        if i % 4 == 0:
            perceived_value = np.random.normal(100, info_noise)
            personality = "fundamentalist"
            true_value = perceived_value
        elif i % 4 == 1:
            personality = "momentum"
            true_value = 100
        elif i % 4 == 2:
            personality = "contrarian"
            true_value = 100
        else:
            personality = "noise"
            true_value = 100

        name = f"{personality}_{i}"
        traders_data.append({"name": name, "personality": personality, "true_value": true_value})
        wealth[name] = {"cash": 1000, "shares_a": 0, "shares_b": 0}

    state = {
        "traders": traders_data,
        "wealth": wealth,
        "prices_a": [100.0],
        "prices_b": [100.0],
        "price_a": 100.0,
        "price_b": 100.0,
        "last_price_a": 100.0,
        "last_price_b": 100.0,
        "round": 0,
        "num_rounds": num_rounds,
        "volatility": volatility,
        "lam": lam,
        "correlation": correlation,
        "done": False
    }

    return state, False, 0


# callback 2 — interval advances simulation one round at a time
@app.callback(
    Output("price-chart", "figure"),
    Output("wealth-display", "children"),
    Output("sim-state", "data", allow_duplicate=True),
    Output("interval", "disabled", allow_duplicate=True),
    Input("interval", "n_intervals"),
    State("sim-state", "data"),
    prevent_initial_call=True
)
def advance_simulation(n_intervals, state):
    if state is None or state["done"]:
        return dash.no_update, dash.no_update, dash.no_update, True

    # run one round
    price_a = state["price_a"]
    price_b = state["price_b"]
    last_price_a = state["last_price_a"]
    last_price_b = state["last_price_b"]
    wealth = state["wealth"]
    volatility = state["volatility"]
    lam = state["lam"]
    correlation = state["correlation"]

    net_order_a = 0
    net_order_b = 0

    for td in state["traders"]:
        t = Trader(td["personality"], td["true_value"])
        order_a = t.get_order(price_a, last_price_a)
        order_b = t.get_order(price_b, last_price_b)

        if order_a > 0:
            order_a = min(order_a, wealth[td["name"]]["cash"] / 2 / price_a)
        elif order_a < 0:
            order_a = max(order_a, -10)

        if order_b > 0:
            order_b = min(order_b, wealth[td["name"]]["cash"] / 2 / price_b)
        elif order_b < 0:
            order_b = max(order_b, -10)

        net_order_a += order_a
        net_order_b += order_b
        wealth[td["name"]]["cash"] -= order_a * price_a + order_b * price_b
        wealth[td["name"]]["shares_a"] += order_a
        wealth[td["name"]]["shares_b"] += order_b

    z1 = np.random.normal(0, 1)
    z2 = np.random.normal(0, 1)
    shock_a = volatility * z1
    shock_b = volatility * (correlation * z1 + np.sqrt(1 - correlation**2) * z2)

    old_price_a = price_a
    old_price_b = price_b

    price_a = float(np.clip(price_a + lam * net_order_a + shock_a, 1, 500))
    price_b = float(np.clip(price_b + lam * net_order_b + shock_b, 1, 500))

    prices_a = state["prices_a"] + [price_a]
    prices_b = state["prices_b"] + [price_b]

    current_round = state["round"] + 1
    done = current_round >= state["num_rounds"]

    # update state
    new_state = {**state, "price_a": price_a, "price_b": price_b,
                 "last_price_a": old_price_a, "last_price_b": old_price_b,
                 "prices_a": prices_a, "prices_b": prices_b,
                 "wealth": wealth, "round": current_round, "done": done}

    # build chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=prices_a, name="Stock A", line=dict(color="#00ff88")))
    fig.add_trace(go.Scatter(y=prices_b, name="Stock B", line=dict(color="#ff9900")))
    fig.add_hline(y=100, line_dash="dash", line_color="#00ff88", opacity=0.3)
    fig.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        font=dict(color="white", family="monospace"),
        xaxis=dict(title="Round", gridcolor="#222"),
        yaxis=dict(title="Price", gridcolor="#222"),
        legend=dict(bgcolor="#0a0a0a"),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    # build wealth cards
    final_wealth = {}
    for td in new_state["traders"]:
        total = wealth[td["name"]]["cash"] + wealth[td["name"]]["shares_a"] * price_a + wealth[td["name"]]["shares_b"] * price_b
        p = td["personality"]
        if p not in final_wealth:
            final_wealth[p] = []
        final_wealth[p].append(total)

    colors = {"fundamentalist": "#00ff88", "momentum": "#ff4444", "contrarian": "#ff9900", "noise": "#4488ff"}
    wealth_cards = []
    for personality, totals in final_wealth.items():
        avg = sum(totals) / len(totals)
        card = html.Div([
            html.Div(personality.upper(), style={"fontSize": "11px", "color": "#aaa", "marginBottom": "4px"}),
            html.Div(f"${avg:.0f}", style={"fontSize": "24px", "fontWeight": "bold", "color": colors.get(personality, "white")})
        ], style={"backgroundColor": "#111", "padding": "20px", "borderRadius": "8px",
                  "border": f"1px solid {colors.get(personality, '#333')}",
                  "minWidth": "150px", "textAlign": "center"})
        wealth_cards.append(card)

    return fig, wealth_cards, new_state, done

if __name__ == "__main__":
    app.run(debug=True)