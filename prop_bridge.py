from flask import Flask, jsonify
import requests

app = Flask(__name__)

# --- Fungsi ambil data real-time dari API Forex gratis ---
def get_forex_data():
    url = "https://api.exchangerate.host/latest?base=USD"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        rates = data.get("rates", {})

        # Pilih pair FX utama
        fx_data = {
            "EURUSD": round(1 / rates.get("EUR", 1), 5),
            "GBPUSD": round(1 / rates.get("GBP", 1), 5),
            "USDJPY": round(rates.get("JPY", 0), 3),
            "AUDUSD": round(1 / rates.get("AUD", 1), 5),
            "NZDUSD": round(1 / rates.get("NZD", 1), 5),
            "USDCHF": round(rates.get("CHF", 0), 5),
            "USDCAD": round(rates.get("CAD", 0), 5)
        }
        return fx_data

    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return "✅ Prop Firm AI Bridge is running!"

@app.route('/chart')
def chart():
    data = get_forex_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)

