"""Smoke tests for market simulator core logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from app import (
    TRUE_VALUE,
    build_highlights,
    build_price_figure,
    clamp_order,
    get_trader_order,
)


def test_clamp_order_respects_shares():
    assert clamp_order(-50, 100, 1000, 3) == -3


def test_clamp_order_respects_cash():
    assert clamp_order(100, 100, 200, 0) == 1.0


def test_build_price_figure_placeholder():
    fig = build_price_figure([100.0], [100.0], placeholder=True)
    assert fig.layout.paper_bgcolor == "#0a0a0a"


def test_build_highlights_empty():
    assert build_highlights([], [100]) == []


def test_build_highlights_with_history():
    history = [{
        "round": 1,
        "price_a_before": 100,
        "price_a_after": 105,
        "price_b_before": 100,
        "price_b_after": 98,
        "orders": {p: {"a": 1.0, "b": 0.5} for p in [
            "fundamentalist", "momentum", "contrarian", "noise"
        ]},
    }]
    result = build_highlights(history, [100, 105])
    assert len(result) == 2


def test_simulation_never_negative_shares():
    def run_round(state):
        price_a, price_b = state["price_a"], state["price_b"]
        last_a, last_b = state["last_price_a"], state["last_price_b"]
        wealth = state["wealth"]
        lam, vol, corr = state["lam"], state["volatility"], state["correlation"]
        net_a = net_b = 0
        for td in state["traders"]:
            w = wealth[td["name"]]
            oa = clamp_order(
                get_trader_order(td["personality"], td["true_value"], price_a, last_a),
                price_a, w["cash"], w["shares_a"],
            )
            ob = clamp_order(
                get_trader_order(td["personality"], td["true_value"], price_b, last_b),
                price_b, w["cash"], w["shares_b"],
            )
            w["cash"] -= oa * price_a + ob * price_b
            w["shares_a"] += oa
            w["shares_b"] += ob
            assert w["shares_a"] >= -1e-9
            assert w["shares_b"] >= -1e-9
            assert w["cash"] >= -1e-6
            net_a += oa
            net_b += ob
        z1, z2 = np.random.normal(0, 1), np.random.normal(0, 1)
        shock_a = vol * z1
        shock_b = vol * (corr * z1 + np.sqrt(1 - corr**2) * z2)
        state["last_price_a"], state["last_price_b"] = price_a, price_b
        state["price_a"] = float(np.clip(price_a + lam * net_a + shock_a, 1, 500))
        state["price_b"] = float(np.clip(price_b + lam * net_b + shock_b, 1, 500))
        return state

    np.random.seed(0)
    personalities = ["fundamentalist", "momentum", "contrarian", "noise"]
    traders = [
        {"name": f"t{i}", "personality": personalities[i % 4], "true_value": 100.0}
        for i in range(20)
    ]
    wealth = {t["name"]: {"cash": 1000, "shares_a": 0, "shares_b": 0} for t in traders}
    state = {
        "traders": traders,
        "wealth": wealth,
        "price_a": 100.0,
        "price_b": 100.0,
        "last_price_a": 100.0,
        "last_price_b": 100.0,
        "lam": 0.1,
        "volatility": 1.0,
        "correlation": 0.5,
    }
    for _ in range(500):
        state = run_round(state)


if __name__ == "__main__":
    test_clamp_order_respects_shares()
    test_clamp_order_respects_cash()
    test_build_price_figure_placeholder()
    test_build_highlights_empty()
    test_build_highlights_with_history()
    test_simulation_never_negative_shares()
    print("All tests passed.")
