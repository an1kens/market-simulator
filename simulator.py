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
        
def run_simulation(num_rounds = 200, num_traders = 20, volatility = 1.0, lam = 0.1, info_noise=5):

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
        wealth[t.name] = {"cash": 1000, "shares": 0}

    #starting price
    price = 100.0
    last_price = 100.0
    prices = [price]

    #main loop
    for t in range(num_rounds):
        net_order = 0
        for trader in traders:
            order = trader.get_order(price,last_price )

            #position limits
            if order > 0: # buying
                max_affordable = wealth[trader.name]["cash"] / price
                order = min(order, max_affordable)
            elif order < 0: #selling
                max_sellable = wealth[trader.name]["shares"]
                order = max(order, -max_sellable)

            net_order += order

            #update wealth
            cost = order * price
            wealth[trader.name]["cash"] -= cost
            wealth[trader.name]["shares"] += order

        shock = np.random.normal(0, volatility)
        new_price = price + lam * net_order + shock
        new_price = np.clip(new_price, 1, 500)

        last_price = price
        price = new_price
        prices.append(price)

    return prices, traders, wealth
    
st.title("Market Simulator")

num_traders = st.slider("Number of Traders", 4, 100, 20)
volatility = st.slider("Volatility", 0.1, 10.0, 1.0)
lam = st.slider("Lambda (Market Impact)", 0.01, 0.5, 0.1)
num_rounds = st.slider("Number of Rounds", 50, 500, 200)
info_noise = st.slider("Information Asymmetry", 0.0, 20.0, 5.0)

prices, traders, wealth = run_simulation(num_rounds, num_traders, volatility, lam, info_noise)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(prices)
ax.axhline(y=100, color = 'r', linestyle='--', label = "True Value")
ax.set_title("Price Over Time")
ax.set_xlabel("Round")
ax.set_ylabel("Price")
ax.set_ylim(max(1, min(prices) * 0.9, max(prices) * 1.1))
ax.legend()

st.pyplot(fig)

st.subheader("Final Wealth by Trader Type")

final_wealth = {}
for trader in traders:
    total = wealth[trader.name]["cash"] + wealth[trader.name]["shares"] * prices[-1]
    personality = trader.personality
    if personality not in final_wealth:
        final_wealth[personality] = []
    final_wealth[personality].append(total)

for personality, totals in final_wealth.items():
    avg = sum(totals)/ len(totals)
    st.metric(personality, f"${avg: .2f}")