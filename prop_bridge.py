from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Prop Firm AI Bridge Aktif (FX Pairs Only via FreeForexAPI)"

@app.route('/chart')
def chart():
    url = "https://www.freeforexapi.com/api/live?pairs=EURUSD,GBPUSD,USDJPY,AUDUSD,NZDUSD,USDCHF,USDCAD"
    data = requests.get(url).json()
    fx = {p: data["rates"][p]["rate"] for p in data["rates"]}
    return jsonify(fx)

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    eq = float(data.get("equity", 10000))
    bal = float(data.get("balance", 10000))
    step = int(data.get("step", 1))
    growth = ((eq - bal) / bal) * 100
    base = 0.10
    lot = round(base * (1 + (growth // 2) * 0.1), 2)
    target = bal * (0.10 if step == 1 else 0.05)
    return jsonify({
        "growth_percent": round(growth, 2),
        "next_lot": lot,
        "target_profit": round(target, 2)
    })
