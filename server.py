from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf
import os
import json
import threading
import time
import requests
app = Flask(__name__, static_folder="public")
CORS(app)

PORT = int(os.environ.get("PORT", 3000))

print("CURRENT WORKING DIR:", os.getcwd())

# -----------------------------
# JSON Helpers
# -----------------------------
def load_json(file, default):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return default

# def save_json(file, data):
    
#     print("\n===== SAVE_JSON CALLED =====")
#     print("File:", file)

#     print("Data going to be saved:")
#     for item in data:
#         print(item)

#     with open(file, "w") as f:
#         json.dump(data, f, indent=2)

#     print("File write completed")

#     # Verify file content immediately
#     try:
#         with open(file, "r") as f:
#             verify = json.load(f)

#         print("Data read back from file:")
#         for item in verify:
#             print(item)

#     except Exception as e:
#         print("Verification read failed:", e)

#     print("===== SAVE_JSON END =====\n")



def save_json(file, data):
    # print(file)
    # print(data)
    with open(file, "w") as f:
        # print("check")
        # print(file)
        json.dump(data, f, indent=2)
    # print("Full file path:", os.path.abspath(file))
    # with open(file, "r") as f:
    #     content = json.load(f)   # load json data
    #     print("JSON file content:")
    #     print(content)
# -----------------------------
# Load Files
# -----------------------------
stocks = load_json("stocks.json", [])
portfolio = load_json("portfolio.json", [])
prices_cache = load_json("prices.json", {})
# -----------------------------
# Load CSV Momentum Stocks
# -----------------------------
import pandas as pd
import logging

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

df = pd.read_csv("ind.csv")

if "Symbol" not in df.columns:
    raise Exception("CSV must contain 'Symbol' column")

def clean_symbol(symbol):
    symbol = str(symbol).strip()
    symbol = symbol.replace("$", "")
    symbol = symbol.replace("-", "")
    return symbol + ".NS"

stocks1 = [clean_symbol(s) for s in df["Symbol"].tolist()]

print("Momentum stock list loaded:", len(stocks1))


# -----------------------------
# ⭐ BEST PRICE FETCH FUNCTION
# -----------------------------
def fetch_price(symbol):

    try:
        ticker = yf.Ticker(symbol)

        # 1️⃣ Primary
        price = ticker.info.get("currentPrice")

        # 2️⃣ Fallback
        if price is None:
            price = ticker.fast_info.get("last_price")

        # 3️⃣ Last fallback
        if price is None:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]

        return price

    except Exception as e:
        print("Fetch error:", symbol, e)
        return None


# -----------------------------
# Update Prices From Yahoo
# -----------------------------
def update_prices():
    global prices_cache

    print("Updating prices...")

    for symbol in stocks:

        price = fetch_price(symbol)

        if price:
            prices_cache[symbol] = float(price)

    save_json("prices.json", prices_cache)


# -----------------------------
# Background Scheduler
# -----------------------------
def scheduler():
    while True:
        update_prices()
        time.sleep(5)

momentum_30_cache = []
momentum_3min_cache = []
last_10_cycles = load_json("last_10_cycles.json", [])

def fetch_all_prices():
    
    try:
        data = yf.download(
            stocks1,
            period="1d",
            interval="1m",
            group_by="ticker",
            threads=False,
            progress=False
        )

        prices = {}

        for symbol in stocks1:
            try:
                price = data[symbol]["Close"].iloc[-1]

                if price is not None and not pd.isna(price):
                    prices[symbol] = float(price)
                else:
                    prices[symbol] = 0

            except:
                pass

        return prices

    except:
        return {}


def calculate_momentum(start, end):

    results = []

    for stock in start:
        if stock in end and start[stock] != 0:
            change = ((end[stock] - start[stock]) / start[stock]) * 100
            results.append({
                "name": stock,
                "price": end[stock],
                "change": round(change,3)
            })

    results.sort(key=lambda x: x["change"], reverse=True)
    return results
# def calculate_static_momentum(cycles):
    
#     results = {}

#     # Compare each consecutive cycle
#     for i in range(len(cycles) - 1):

#         start = cycles[i]
#         end = cycles[i + 1]

#         for stock in start:

#             if stock in end and start[stock] != 0:

#                 change = ((end[stock] - start[stock]) / start[stock]) * 100

#                 if stock not in results:
#                     results[stock] = {
#                         "name": stock,
#                         "price": end[stock],
#                         "change": change
#                     }
#                 else:
#                     # Keep maximum gain found
#                     if change > results[stock]["change"]:
#                         results[stock]["change"] = change
#                         results[stock]["price"] = end[stock]

#     # Convert dict → list
#     final = list(results.values())

#     final.sort(key=lambda x: x["change"], reverse=True)

#     return final[:5]

def calculate_static_momentum(cycles):
    
    results = []

    if len(cycles) < 2:
        return []

    start_cycle = cycles[0]
    end_cycle = cycles[-1]

    for stock in start_cycle:

        if stock in end_cycle and start_cycle[stock] != 0:

            start_price = start_cycle[stock]
            end_price = end_cycle[stock]

            change = ((end_price - start_price) / start_price) * 100

            results.append({
                "name": stock,
                "price": end_price,
                "change": round(change, 3)
            })

    results.sort(key=lambda x: x["change"], reverse=True)

    return results[:5]

def momentum_scheduler():
    
    global momentum_30_cache, momentum_3min_cache, last_10_cycles

    # ⭐ Pre-load first cycle to avoid empty UI
    previous_prices = fetch_all_prices()
    # print(previous_prices)
    if not previous_prices:
        previous_prices = {}

    while True:

        current_prices = fetch_all_prices()

        # ⭐ If fetch failed, skip cycle
        if not current_prices:
            time.sleep(5)
            continue

        # -------------------------
        # ⭐ 5 SEC MOMENTUM
        # -------------------------
        if previous_prices:
            temp = calculate_momentum(previous_prices, current_prices)
            momentum_30_cache = temp[:5]

        previous_prices = current_prices

        # -------------------------
        # ⭐ STORE LAST 10 CYCLES
        # -------------------------
        if current_prices:

            last_10_cycles.append(current_prices)

            # Keep only last 10 cycles
            if len(last_10_cycles) > 5:
                last_10_cycles.pop(0)

            save_json("last_10_cycles.json", last_10_cycles)

        # -------------------------
        # ⭐ 3 MIN STATIC MOMENTUM
        # -------------------------
        if len(last_10_cycles) == 5:

            momentum_3min_cache = calculate_static_momentum(last_10_cycles)

        # ⭐ Wait 5 seconds
        time.sleep(5)


@app.route("/momentum30")
def momentum30():
    return jsonify(momentum_30_cache)

@app.route("/momentum3min")
def momentum3min():
    return jsonify(momentum_3min_cache)

# -----------------------------
# Serve Frontend
# -----------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# -----------------------------
# Get Stocks
# -----------------------------
@app.route("/stocks")
def get_stocks():

    result = []

    for symbol in stocks:
        result.append({
            "name": symbol,
            "price": prices_cache.get(symbol)
        })
        # print(result)
        # print(symbol)
    return jsonify(result)


# -----------------------------
# Add Stock
# -----------------------------
@app.route("/add-stock", methods=["POST"])
def add_stock():

    data = request.get_json()
    symbol = data["symbol"].upper()

    if not symbol.endswith(".NS"):
        symbol += ".NS"

    if symbol not in stocks:
        stocks.append(symbol)
        save_json("stocks.json", stocks)

    return jsonify(stocks)


@app.route("/removeStock/<name>", methods=["DELETE"])
def remove_stock(name):

    if name in stocks:
        stocks.remove(name)
        save_json("stocks.json", stocks)
        return jsonify({"status":"removed"})

    return jsonify({"status":"not found"})

# -----------------------------
# Portfolio
# -----------------------------
@app.route("/portfolio")
def get_portfolio():
    return jsonify(portfolio)


# -----------------------------
# Buy Stock
# -----------------------------
@app.route("/buy", methods=["POST"])
def buy_stock():

    data = request.get_json()
    buy_price = float(data["price"])

    stock = {
        "name": data["name"],
        "buy_price": buy_price,
        "target_price": buy_price * 1.50,
        "highest_price": buy_price,
        "alert_triggered": False
    }
    portfolio.append(stock)
    save_json("portfolio.json", portfolio)

    return jsonify(portfolio)


# -----------------------------
# Sell Stock
# -----------------------------
@app.route("/sell", methods=["POST"])
def sell_stock():

    name = request.get_json()["name"]

    global portfolio
    portfolio = [s for s in portfolio if s["name"] != name]

    save_json("portfolio.json", portfolio)

    return jsonify(portfolio)


# -----------------------------
# ALERT LOGIC
# -----------------------------
@app.route("/check-alerts")
def check_alerts():

    alerts = []

    for stock in portfolio:

        symbol = stock["name"]
        current_price = prices_cache.get(symbol)

        if current_price is None:
            continue

        buy_price = stock["buy_price"]
        target_price = stock["target_price"]

        # Initialize last price if not exists
        if "last_price" not in stock:
            stock["last_price"] = current_price

        # Ignore until +3% profit
        if current_price < target_price:
            stock["alert_triggered"] = False
            stock["last_price"] = current_price
            continue

        # Update highest price
        if current_price > stock["highest_price"]:
            stock["highest_price"] = current_price
            stock["alert_triggered"] = False

        highest_price = stock["highest_price"]
        last_price = stock["last_price"]

        # Calculate drop from highest
        drop_percent = (highest_price - current_price) / highest_price

        # 🟥 Alarm ON → falling direction + drop threshold
        # print(current_price)
        # print(last_price)
        if (current_price <= last_price):
            stock["alert_triggered"] = True
            alerts.append(symbol)

        # 🟩 Alarm OFF → price rising
        if current_price > last_price:
            stock["alert_triggered"] = False

        # Update last price
        stock["last_price"] = current_price

    save_json("portfolio.json", portfolio)
    return jsonify(alerts)


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":

    threading.Thread(target=scheduler, daemon=True).start()
    threading.Thread(target=momentum_scheduler, daemon=True).start()

    app.run(host="0.0.0.0", port=PORT)

