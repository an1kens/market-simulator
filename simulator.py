import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
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
            return np.random.normal(0,2)
        
def run_simulation(num_rounds=200, num_traders=20, volatility=1.0, lam=0.1, info_noise=5, true_value_b=150, correlation=0.5):

    #create a mix of trader personalities
    traders = []
    wealth = {}

    for i in range(num_traders):
        if i % 4 == 0:
            percieved_value = np.random.normal(100, info_noise)
            t = Trader("fundamentalist", true_value=percieved_value)
        elif i % 4 == 1:
            t = Trader("momentum")
        elif i % 4 == 2:
            t = Trader("contrarian")
        else:
            t = Trader("noise")

        t.name = f"{t.personality}_{i}"
        traders.append(t)
        wealth[t.name] = {"cash": 1000, "shares_a": 0, "shares_b": 0}

    #starting price
    price = 100.0
    last_price = 100.0
    prices = [price]

    price_b = true_value_b
    last_price_b = true_value_b
    prices_b = [price_b]

    #main loop
    for t in range(num_rounds):
        net_order_a = 0
        net_order_b = 0

    for trader in traders:
        order_a = trader.get_order(price, last_price)
        order_b = trader.get_order(price_b, last_price_b)

        # position limits for stock a
        if order_a > 0:
            max_affordable = wealth[trader.name]["cash"] / 2 / price
            order_a = min(order_a, max_affordable)
        elif order_a < 0:
            max_sellable = wealth[trader.name]["shares_a"]
            order_a = max(order_a, -max_sellable)

        # position limits for stock b
        if order_b > 0:
            max_affordable = wealth[trader.name]["cash"] / 2 / price_b
            order_b = min(order_b, max_affordable)
        elif order_b < 0:
            max_sellable = wealth[trader.name]["shares_b"]
            order_b = max(order_b, -max_sellable)

        net_order_a += order_a
        net_order_b += order_b

        wealth[trader.name]["cash"] -= order_a * price
        wealth[trader.name]["cash"] -= order_b * price_b
        wealth[trader.name]["shares_a"] += order_a
        wealth[trader.name]["shares_b"] += order_b

    # correlated shocks
    z1 = np.random.normal(0, 1)
    z2 = np.random.normal(0, 1)
    shock_a = volatility * z1
    shock_b = volatility * (correlation * z1 + np.sqrt(1 - correlation**2) * z2)

    new_price = np.clip(price + lam * net_order_a + shock_a, 1, 500)
    new_price_b = np.clip(price_b + lam * net_order_b + shock_b, 1, 500)

    last_price = price
    last_price_b = price_b
    price = new_price
    price_b = new_price_b

    prices.append(price)
    prices_b.append(price_b)

    return prices, prices_b, traders, wealth
    
st.title("Market Simulator")

num_traders = st.slider("Number of Traders", 4, 100, 20)
volatility = st.slider("Volatility", 0.1, 10.0, 1.0)
lam = st.slider("Lambda (Market Impact)", 0.01, 0.5, 0.1)
num_rounds = st.slider("Number of Rounds", 50, 500, 200)
info_noise = st.slider("Information Asymmetry", 0.0, 20.0, 5.0)
true_value_b = st.slider("Stock B True Value", 50, 300, 100)
correlation = st.slider("Correlation", -1.0, 1.0, 0.5)

prices, prices_b, traders, wealth = run_simulation(num_rounds, num_traders, volatility, lam, info_noise, true_value_b, correlation)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(prices, label="Stock A", color='blue')
ax.plot(prices_b, label="Stock B", color='orange')
ax.axhline(y=100, color='blue', linestyle='--', alpha=0.3, label="True Value A")
ax.axhline(y=true_value_b, color='orange', linestyle='--', alpha=0.3, label="True Value B")
ax.set_title("Stock A vs Stock B Price Over Time")
ax.set_xlabel("Round")
ax.set_ylabel("Price")
ax.legend()
ax.set_ylim(min(min(prices), min(prices_b)) * 0.9, max(max(prices), max(prices_b)) * 1.1)
st.pyplot(fig)

st.subheader("Final Wealth by Trader Type")

final_wealth = {}
for trader in traders:
    total = wealth[trader.name]["cash"] + wealth[trader.name]["shares_a"] * prices[-1] + wealth[trader.name]["shares_b"]
    personality = trader.personality
    if personality not in final_wealth:
        final_wealth[personality] = []
    final_wealth[personality].append(total)

for personality, totals in final_wealth.items():
    avg = sum(totals)/ len(totals)
    st.metric(personality, f"${avg: .2f}")