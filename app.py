import os

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np

COLORS = {"fundamentalist": "#00ff88", "momentum": "#ff4444", "contrarian": "#ff9900", "noise": "#4488ff"}
TRUE_VALUE = 100

RUN_BTN_STYLE = {
    "backgroundColor": "#00ff88",
    "color": "#0a0a0a",
    "border": "none",
    "padding": "12px 40px",
    "fontSize": "16px",
    "fontFamily": "monospace",
    "fontWeight": "bold",
    "cursor": "pointer",
    "borderRadius": "4px",
}
RUN_BTN_DISABLED_STYLE = {**RUN_BTN_STYLE, "backgroundColor": "#333", "color": "#666", "cursor": "not-allowed"}


def get_trader_order(personality, true_value, current_price, last_price):
    if personality == "fundamentalist":
        return 0.5 * (true_value - current_price)
    if personality == "momentum":
        return 0.8 * (current_price - last_price)
    if personality == "contrarian":
        return -0.8 * (current_price - last_price)
    if personality == "noise":
        return np.random.normal(0, 2)
    return 0.0


def clamp_order(order, price, cash, shares):
    if order > 0:
        max_affordable = cash / 2 / price if price > 0 else 0
        return min(order, max_affordable)
    if order < 0:
        return max(order, -shares)
    return order


def personality_order_magnitude(orders_entry):
    return abs(orders_entry["a"]) + abs(orders_entry["b"])


def dominant_personality(orders):
    return max(orders.items(), key=lambda item: personality_order_magnitude(item[1]))


def build_price_figure(prices_a, prices_b, x_max=200, placeholder=False):
    x = list(range(len(prices_a)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=prices_a, name="Stock A",
        line=dict(color="#00ff88", width=2),
        mode="lines+markers" if len(x) == 1 else "lines",
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=x, y=prices_b, name="Stock B",
        line=dict(color="#ff9900", width=2),
        mode="lines+markers" if len(x) == 1 else "lines",
        marker=dict(size=6),
    ))
    fig.add_hline(y=TRUE_VALUE, line_dash="dash", line_color="#888888", line_width=1, opacity=0.5)

    yaxis = dict(title="Price", gridcolor="#222", zerolinecolor="#222")
    if placeholder or len(prices_a) <= 1:
        yaxis["range"] = [70, 130]
    else:
        yaxis["autorange"] = True

    fig.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
        font=dict(color="white", family="monospace"),
        xaxis=dict(title="Round", gridcolor="#222", range=[0, x_max]),
        yaxis=yaxis,
        legend=dict(bgcolor="#0a0a0a", orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=50, r=30, t=50, b=40),
        annotations=[
            dict(
                x=1,
                xref="paper",
                y=TRUE_VALUE,
                yref="y",
                text=f"${TRUE_VALUE} true value",
                showarrow=False,
                xanchor="right",
                yanchor="bottom",
                font=dict(size=11, color="#888888", family="monospace"),
            )
        ],
    )

    if placeholder:
        fig.add_annotation(
            text="Click RUN SIMULATION to start",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#555555", family="monospace"),
        )

    return fig


CLOSE_BTN_STYLE = {
    "backgroundColor": "transparent",
    "color": "#888",
    "border": "1px solid #444",
    "padding": "4px 12px",
    "fontSize": "12px",
    "fontFamily": "monospace",
    "cursor": "pointer",
    "borderRadius": "4px",
}


def click_panel_header(title):
    return html.Div([
        html.Div(title, style={"color": "#00ff88", "fontSize": "14px", "fontWeight": "bold"}),
        html.Button("✕ Close", id="close-panel-btn", n_clicks=0, style=CLOSE_BTN_STYLE),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "marginBottom": "16px",
    })


# ── Highlights engine ─────────────────────────────────────────
def build_highlights(history, prices_a):
    if not history:
        return []

    biggest_crash = max(history, key=lambda h: h["price_a_before"] - h["price_a_after"])
    biggest_spike = max(history, key=lambda h: h["price_a_after"] - h["price_a_before"])

    divergences = [(h["round"], abs(h["price_a_after"] - h["price_b_after"])) for h in history]
    max_div = max(divergences, key=lambda x: x[1])
    min_div = min(divergences, key=lambda x: x[1])

    n = len(prices_a)
    chunk = max(1, n // 10)
    early_avg = sum(prices_a[:chunk]) / chunk
    late_avg = sum(prices_a[-chunk:]) / chunk
    change_pct = ((late_avg - early_avg) / early_avg) * 100
    if change_pct > 10:
        trend = f"Strong upward trend (+{change_pct:.1f}%)"
        trend_color = "#00ff88"
    elif change_pct < -10:
        trend = f"Strong downward trend ({change_pct:.1f}%)"
        trend_color = "#ff4444"
    else:
        trend = f"Choppy — no clear direction ({change_pct:+.1f}%)"
        trend_color = "#ff9900"

    avg_deviation_a = sum(abs(h["price_a_after"] - TRUE_VALUE) for h in history) / len(history)
    avg_deviation_b = sum(abs(h["price_b_after"] - TRUE_VALUE) for h in history) / len(history)

    force_totals = {"fundamentalist": 0, "momentum": 0, "contrarian": 0, "noise": 0}
    for h in history:
        for p in force_totals:
            force_totals[p] += personality_order_magnitude(h["orders"][p])
    dominant = max(force_totals, key=force_totals.get)

    def card(title, value, detail, color="#00ff88"):
        return html.Div([
            html.Div(title, style={"color": "#aaa", "fontSize": "11px", "marginBottom": "4px"}),
            html.Div(value, style={"color": color, "fontSize": "18px", "fontWeight": "bold", "marginBottom": "4px"}),
            html.Div(detail, style={"color": "#888", "fontSize": "12px"})
        ], style={"backgroundColor": "#111", "padding": "16px", "borderRadius": "8px",
                  "border": "1px solid #333", "minWidth": "200px", "flex": "1"})

    cards = [
        card("BIGGEST CRASH",
             f"−${biggest_crash['price_a_before'] - biggest_crash['price_a_after']:.2f}",
             f"Round {biggest_crash['round']} — ${biggest_crash['price_a_before']:.2f} → ${biggest_crash['price_a_after']:.2f}",
             "#ff4444"),
        card("BIGGEST SPIKE",
             f"+${biggest_spike['price_a_after'] - biggest_spike['price_a_before']:.2f}",
             f"Round {biggest_spike['round']} — ${biggest_spike['price_a_before']:.2f} → ${biggest_spike['price_a_after']:.2f}",
             "#00ff88"),
        card("MAX DIVERGENCE",
             f"${max_div[1]:.2f} apart",
             f"Round {max_div[0]} — stocks furthest from each other",
             "#ff9900"),
        card("MAX CONVERGENCE",
             f"${min_div[1]:.2f} apart",
             f"Round {min_div[0]} — stocks closest to each other",
             "#4488ff"),
        card("OVERALL TREND (STOCK A)",
             trend,
             f"Early avg ${early_avg:.2f} → Late avg ${late_avg:.2f}",
             trend_color),
        card("AVG DEVIATION FROM TRUE VALUE",
             f"A: ${avg_deviation_a:.2f} · B: ${avg_deviation_b:.2f}",
             f"Average distance from ${TRUE_VALUE} true value per stock across all rounds",
             "#ff9900"),
        card("DOMINANT MARKET FORCE",
             dominant.upper(),
             f"Highest combined order volume (A + B): {force_totals[dominant]:.1f}",
             COLORS[dominant]),
    ]

    return [
        html.Div("SIMULATION HIGHLIGHTS", style={"color": "#00ff88", "fontSize": "14px", "fontWeight": "bold", "marginBottom": "16px", "marginTop": "30px"}),
        html.Div(cards, style={"display": "flex", "gap": "16px", "flexWrap": "wrap"})
    ]


# ── App layout ────────────────────────────────────────────────
app = dash.Dash(__name__)

app.layout = html.Div(style={"backgroundColor": "#0a0a0a", "minHeight": "100vh", "padding": "20px", "fontFamily": "monospace"}, children=[

    html.H1("Market Simulator", style={"textAlign": "center", "color": "#00ff88"}),

    html.Div(style={"display": "flex", "gap": "40px", "justifyContent": "center", "flexWrap": "wrap", "marginBottom": "20px"}, children=[
        html.Div([html.Label(id="num-traders-label", children="Traders: 20", style={"color": "#aaa"}), dcc.Slider(id="num-traders", min=4, max=100, step=4, value=20, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label(id="volatility-label", children="Volatility: 1.0", style={"color": "#aaa"}), dcc.Slider(id="volatility", min=0.1, max=10.0, step=0.1, value=1.0, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label(id="lam-label", children="Lambda: 0.10", style={"color": "#aaa"}), dcc.Slider(id="lam", min=0.01, max=0.5, step=0.01, value=0.1, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label(id="num-rounds-label", children="Rounds: 200", style={"color": "#aaa"}), dcc.Slider(id="num-rounds", min=50, max=500, step=50, value=200, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label(id="info-noise-label", children="Info Noise: 5.0", style={"color": "#aaa"}), dcc.Slider(id="info-noise", min=0.0, max=20.0, step=0.5, value=5.0, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
        html.Div([html.Label(id="correlation-label", children="Correlation: 0.5", style={"color": "#aaa"}), dcc.Slider(id="correlation", min=-1.0, max=1.0, step=0.1, value=0.5, marks=None, tooltip={"placement": "bottom"})], style={"width": "200px"}),
    ]),

    html.Div(
        html.Button("RUN SIMULATION", id="run-btn", n_clicks=0, style=RUN_BTN_STYLE),
        style={"textAlign": "center", "marginBottom": "30px"}
    ),

    dcc.Store(id="sim-state"),
    dcc.Interval(id="interval", interval=50, n_intervals=0, disabled=True),

    dcc.Graph(
        id="price-chart",
        figure=build_price_figure([TRUE_VALUE], [TRUE_VALUE], placeholder=True),
        config={"displayModeBar": False},
    ),

    html.Div(id="click-panel", style={"margin": "20px auto", "maxWidth": "900px", "backgroundColor": "#111", "borderRadius": "8px", "padding": "20px", "display": "none"}),

    html.Div(id="wealth-display", style={"display": "flex", "justifyContent": "center", "gap": "20px", "marginTop": "20px", "flexWrap": "wrap"}),

    html.Div(id="highlights-display", style={"margin": "20px auto", "maxWidth": "1200px"}),
])

CLICK_PANEL_HIDDEN = {"margin": "20px auto", "maxWidth": "900px", "backgroundColor": "#111", "borderRadius": "8px", "padding": "20px", "display": "none"}


@app.callback(
    Output("num-traders-label", "children"),
    Output("volatility-label", "children"),
    Output("lam-label", "children"),
    Output("num-rounds-label", "children"),
    Output("info-noise-label", "children"),
    Output("correlation-label", "children"),
    Input("num-traders", "value"),
    Input("volatility", "value"),
    Input("lam", "value"),
    Input("num-rounds", "value"),
    Input("info-noise", "value"),
    Input("correlation", "value"),
)
def update_slider_labels(num_traders, volatility, lam, num_rounds, info_noise, correlation):
    return (
        f"Traders: {num_traders}",
        f"Volatility: {volatility:.1f}",
        f"Lambda: {lam:.2f}",
        f"Rounds: {num_rounds}",
        f"Info Noise: {info_noise:.1f}",
        f"Correlation: {correlation:.1f}",
    )


# ── Callback 1: initialize ────────────────────────────────────
@app.callback(
    Output("sim-state", "data"),
    Output("interval", "disabled"),
    Output("interval", "n_intervals"),
    Output("run-btn", "disabled"),
    Output("run-btn", "style"),
    Output("click-panel", "children"),
    Output("click-panel", "style"),
    Output("highlights-display", "children"),
    Output("price-chart", "figure"),
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
            personality = "fundamentalist"
            true_value = float(np.random.normal(TRUE_VALUE, info_noise))
        elif i % 4 == 1:
            personality = "momentum"
            true_value = TRUE_VALUE
        elif i % 4 == 2:
            personality = "contrarian"
            true_value = TRUE_VALUE
        else:
            personality = "noise"
            true_value = TRUE_VALUE

        name = f"{personality}_{i}"
        traders_data.append({"name": name, "personality": personality, "true_value": true_value})
        wealth[name] = {"cash": 1000, "shares_a": 0, "shares_b": 0}

    state = {
        "traders": traders_data,
        "wealth": wealth,
        "prices_a": [float(TRUE_VALUE)],
        "prices_b": [float(TRUE_VALUE)],
        "price_a": float(TRUE_VALUE),
        "price_b": float(TRUE_VALUE),
        "last_price_a": float(TRUE_VALUE),
        "last_price_b": float(TRUE_VALUE),
        "round": 0,
        "num_rounds": num_rounds,
        "volatility": volatility,
        "lam": lam,
        "correlation": correlation,
        "done": False,
        "history": []
    }

    initial_fig = build_price_figure([float(TRUE_VALUE)], [float(TRUE_VALUE)], x_max=num_rounds)
    return state, False, 0, True, RUN_BTN_DISABLED_STYLE, [], CLICK_PANEL_HIDDEN, [], initial_fig


# ── Callback 2: advance one round ─────────────────────────────
@app.callback(
    Output("price-chart", "figure"),
    Output("wealth-display", "children"),
    Output("sim-state", "data", allow_duplicate=True),
    Output("interval", "disabled", allow_duplicate=True),
    Output("highlights-display", "children", allow_duplicate=True),
    Output("run-btn", "disabled", allow_duplicate=True),
    Output("run-btn", "style", allow_duplicate=True),
    Input("interval", "n_intervals"),
    State("sim-state", "data"),
    prevent_initial_call=True
)
def advance_simulation(n_intervals, state):
    if state is None or state["done"]:
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, False, RUN_BTN_STYLE

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
    round_orders = {
        "fundamentalist": {"a": 0, "b": 0},
        "momentum": {"a": 0, "b": 0},
        "contrarian": {"a": 0, "b": 0},
        "noise": {"a": 0, "b": 0}
    }

    for td in state["traders"]:
        w = wealth[td["name"]]
        order_a = get_trader_order(td["personality"], td["true_value"], price_a, last_price_a)
        order_b = get_trader_order(td["personality"], td["true_value"], price_b, last_price_b)

        order_a = clamp_order(order_a, price_a, w["cash"], w["shares_a"])
        order_b = clamp_order(order_b, price_b, w["cash"], w["shares_b"])

        round_orders[td["personality"]]["a"] += order_a
        round_orders[td["personality"]]["b"] += order_b
        net_order_a += order_a
        net_order_b += order_b
        w["cash"] -= order_a * price_a + order_b * price_b
        w["shares_a"] += order_a
        w["shares_b"] += order_b

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

    history_entry = {
        "round": current_round,
        "price_a_before": round(old_price_a, 2),
        "price_a_after": round(price_a, 2),
        "price_b_before": round(old_price_b, 2),
        "price_b_after": round(price_b, 2),
        "shock_a": round(shock_a, 3),
        "shock_b": round(shock_b, 3),
        "orders": round_orders
    }
    history = state.get("history", []) + [history_entry]

    new_state = {**state,
                 "price_a": price_a, "price_b": price_b,
                 "last_price_a": old_price_a, "last_price_b": old_price_b,
                 "prices_a": prices_a, "prices_b": prices_b,
                 "wealth": wealth, "round": current_round,
                 "done": done, "history": history}

    fig = build_price_figure(prices_a, prices_b, x_max=state["num_rounds"])

    final_wealth = {}
    for td in new_state["traders"]:
        total = (wealth[td["name"]]["cash"]
                 + wealth[td["name"]]["shares_a"] * price_a
                 + wealth[td["name"]]["shares_b"] * price_b)
        p = td["personality"]
        final_wealth.setdefault(p, []).append(total)

    wealth_cards = []
    for personality, totals in final_wealth.items():
        avg = sum(totals) / len(totals)
        wealth_cards.append(html.Div([
            html.Div(personality.upper(), style={"fontSize": "11px", "color": "#aaa", "marginBottom": "4px"}),
            html.Div(f"${avg:.0f}", style={"fontSize": "24px", "fontWeight": "bold", "color": COLORS.get(personality, "white")})
        ], style={"backgroundColor": "#111", "padding": "20px", "borderRadius": "8px",
                  "border": f"1px solid {COLORS.get(personality, '#333')}",
                  "minWidth": "150px", "textAlign": "center"}))

    highlights = build_highlights(history, prices_a) if done else dash.no_update
    run_disabled = not done
    run_style = RUN_BTN_DISABLED_STYLE if run_disabled else RUN_BTN_STYLE

    return fig, wealth_cards, new_state, done, highlights, run_disabled, run_style


# ── Callback 3: click to explain round ───────────────────────
@app.callback(
    Output("click-panel", "children", allow_duplicate=True),
    Output("click-panel", "style", allow_duplicate=True),
    Input("price-chart", "clickData"),
    State("sim-state", "data"),
    prevent_initial_call=True
)
def explain_round(clickData, state):
    if clickData is None or state is None or not state.get("history"):
        return dash.no_update, CLICK_PANEL_HIDDEN

    clicked_round = clickData["points"][0]["x"]

    if clicked_round <= 0 or clicked_round > len(state["history"]):
        return dash.no_update, CLICK_PANEL_HIDDEN

    h = state["history"][clicked_round - 1]
    orders = h["orders"]

    price_change_a = h["price_a_after"] - h["price_a_before"]
    price_change_b = h["price_b_after"] - h["price_b_before"]

    def direction(val):
        if val > 0.5:
            return "▲ bought"
        if val < -0.5:
            return "▼ sold"
        return "→ neutral"

    def describe_shock(shock):
        if abs(shock) > 3:
            return f"extreme {'positive' if shock > 0 else 'negative'} shock ({shock:+.2f})"
        if abs(shock) > 1.5:
            return f"moderate {'positive' if shock > 0 else 'negative'} shock ({shock:+.2f})"
        return f"mild noise ({shock:+.2f})"

    dominant_name, dominant_orders = dominant_personality(orders)
    dominant_val_a = dominant_orders["a"]
    dominant_val_b = dominant_orders["b"]

    summary = (
        f"Stock A moved {'UP' if price_change_a > 0 else 'DOWN'} by ${abs(price_change_a):.2f}; "
        f"Stock B moved {'UP' if price_change_b > 0 else 'DOWN'} by ${abs(price_change_b):.2f}. "
        f"Dominant force: {dominant_name} "
        f"(A net {dominant_val_a:+.2f}, B net {dominant_val_b:+.2f}). "
        f"Random shocks: A {describe_shock(h['shock_a'])}, B {describe_shock(h['shock_b'])}."
    )

    panel_content = [
        click_panel_header(f"ROUND {clicked_round} ANALYSIS"),

        html.Div(style={"display": "flex", "gap": "30px", "marginBottom": "16px", "flexWrap": "wrap"}, children=[
            html.Div([
                html.Div("STOCK A", style={"color": "#aaa", "fontSize": "11px"}),
                html.Div(f"${h['price_a_before']:.2f} → ${h['price_a_after']:.2f}", style={"color": "#00ff88", "fontSize": "18px"}),
                html.Div(f"{price_change_a:+.2f}", style={"color": "#00ff88" if price_change_a > 0 else "#ff4444", "fontSize": "14px"})
            ]),
            html.Div([
                html.Div("STOCK B", style={"color": "#aaa", "fontSize": "11px"}),
                html.Div(f"${h['price_b_before']:.2f} → ${h['price_b_after']:.2f}", style={"color": "#ff9900", "fontSize": "18px"}),
                html.Div(f"{price_change_b:+.2f}", style={"color": "#00ff88" if price_change_b > 0 else "#ff4444", "fontSize": "14px"})
            ]),
            html.Div([
                html.Div("SHOCK A", style={"color": "#aaa", "fontSize": "11px"}),
                html.Div(f"{h['shock_a']:+.3f}", style={"color": "#4488ff", "fontSize": "18px"})
            ]),
            html.Div([
                html.Div("SHOCK B", style={"color": "#aaa", "fontSize": "11px"}),
                html.Div(f"{h['shock_b']:+.3f}", style={"color": "#4488ff", "fontSize": "18px"})
            ]),
        ]),

        html.Div("TRADER ACTIVITY", style={"color": "#aaa", "fontSize": "11px", "marginBottom": "8px"}),
        html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px", "flexWrap": "wrap"}, children=[
            html.Div([
                html.Div(p.upper(), style={"color": COLORS[p], "fontSize": "11px"}),
                html.Div(f"A: {direction(orders[p]['a'])} ({orders[p]['a']:+.2f})", style={"color": "white", "fontSize": "13px"}),
                html.Div(f"B: {direction(orders[p]['b'])} ({orders[p]['b']:+.2f})", style={"color": "white", "fontSize": "13px"}),
            ], style={"backgroundColor": "#1a1a1a", "padding": "12px", "borderRadius": "6px", "minWidth": "160px"})
            for p in ["fundamentalist", "momentum", "contrarian", "noise"]
        ]),

        html.Div("SUMMARY", style={"color": "#aaa", "fontSize": "11px", "marginBottom": "8px"}),
        html.Div(summary, style={"color": "white", "fontSize": "13px", "lineHeight": "1.6"})
    ]

    panel_style = {
        "margin": "20px auto",
        "maxWidth": "900px",
        "backgroundColor": "#111",
        "borderRadius": "8px",
        "padding": "20px",
        "display": "block",
        "border": "1px solid #333"
    }

    return panel_content, panel_style


@app.callback(
    Output("click-panel", "children", allow_duplicate=True),
    Output("click-panel", "style", allow_duplicate=True),
    Input("close-panel-btn", "n_clicks"),
    prevent_initial_call=True,
)
def close_click_panel(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update
    return [], CLICK_PANEL_HIDDEN


if __name__ == "__main__":
    debug = os.getenv("DASH_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=debug)
